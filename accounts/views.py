import datetime
import jwt
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db import models
from django.db.models import Q, Count
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse
from django.views.decorators.http import require_http_methods

from .forms import CustomUserCreationForm, LoginForm, PostForm, CommentForm, ChatMessageForm
from .models import User, CommonPost, Comment, ChatMessage, ContentReport, Report
from .decorators import admin_required, moderator_required, can_post, can_moderate


def make_jwt_token(user):
    now = datetime.datetime.utcnow()
    payload = {
        'user_id': user.id,
        'username': user.username,
        'iat': now,
        'exp': now + datetime.timedelta(minutes=30),
    }
    return jwt.encode(payload, settings.SECRET_KEY, algorithm='HS256')


def decode_jwt_token(token):
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=['HS256'])
        return payload
    except jwt.ExpiredSignatureError:
        return None
    except jwt.InvalidTokenError:
        return None


def index(request):
    if request.user.is_authenticated:
        posts = CommonPost.objects.select_related('author').prefetch_related('comments__author')
        common_chat_preview = ChatMessage.objects.filter(is_common=True).select_related('sender').order_by('-created_at')[:5]
        other_users = User.objects.exclude(id=request.user.id).order_by('username')
        post_form = PostForm()
        comment_form = CommentForm()
        
        # Get user's submitted reports
        user_reports = Report.objects.filter(
            reporter=request.user
        ).order_by('-created_at')

        # Separate posts by author role
        staff_posts = posts.filter(author__role__in=['admin', 'moderator'])
        student_posts = posts.filter(author__role='student')

        return render(request, 'accounts/index.html', {
            'posts': posts,
            'staff_posts': staff_posts,
            'student_posts': student_posts,
            'common_chat_preview': reversed(common_chat_preview),
            'other_users': other_users,
            'post_form': post_form,
            'comment_form': comment_form,
            'user_reports': user_reports,
        })

    return render(request, 'accounts/index.html')


def register(request):
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            user = form.save()
            login(request, user)
            token = make_jwt_token(user)
            response = redirect('index')
            response.set_cookie(
                'jwt_token',
                token,
                httponly=True,
                samesite='Lax',
                secure=False,
                max_age=30 * 60,
            )
            return response
    else:
        form = CustomUserCreationForm()

    return render(request, 'accounts/register.html', {'form': form})
def login_view(request):
    if request.method == 'POST':
        form = LoginForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password = form.cleaned_data['password']
            user = authenticate(request, username=username, password=password)

            if user is not None:
                login(request, user)
                token = make_jwt_token(user)
                response = redirect('index')
                response.set_cookie(
                    'jwt_token',
                    token,
                    httponly=True,
                    samesite='Lax',
                    secure=False,
                    max_age=30 * 60,
                )
                return response

            form.add_error(None, 'Invalid username or password')
    else:
        form = LoginForm()

    return render(request, 'accounts/login.html', {'form': form})


@login_required
def profile(request):
    token = request.COOKIES.get('jwt_token')
    decoded = decode_jwt_token(token) if token else None
    return render(request, 'accounts/profile.html', {'jwt_payload': decoded})


@login_required
def create_post(request):
    if request.method == 'POST':
        form = PostForm(request.POST)
        if form.is_valid():
            post = form.save(commit=False)
            post.author = request.user
            post.save()
            messages.success(request, 'Post created successfully!')
    return redirect('index')


@login_required
def add_comment(request, post_id):
    post = get_object_or_404(CommonPost, pk=post_id)
    if request.method == 'POST':
        form = CommentForm(request.POST)
        if form.is_valid():
            comment = form.save(commit=False)
            comment.post = post
            comment.author = request.user
            comment.save()
    return redirect('index')


@login_required
def common_chat(request):
    messages = ChatMessage.objects.filter(is_common=True).select_related('sender').order_by('created_at')
    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.sender = request.user
            chat.is_common = True
            chat.save()
            return redirect('common_chat')
    else:
        form = ChatMessageForm()

    return render(request, 'accounts/common_chat.html', {
        'messages': messages,
        'form': form,
    })


@login_required
def personal_chat(request, username):
    other_user = get_object_or_404(User, username=username)
    messages = ChatMessage.objects.filter(
        is_common=False,
    ).filter(
        Q(sender=request.user, recipient=other_user) | Q(sender=other_user, recipient=request.user)
    ).select_related('sender', 'recipient').order_by('created_at')

    if request.method == 'POST':
        form = ChatMessageForm(request.POST)
        if form.is_valid():
            chat = form.save(commit=False)
            chat.sender = request.user
            chat.recipient = other_user
            chat.is_common = False
            chat.save()
            return redirect('personal_chat', username=username)
    else:
        form = ChatMessageForm()

    return render(request, 'accounts/personal_chat.html', {
        'messages': messages,
        'form': form,
        'other_user': other_user,
    })


def logout_view(request):
    logout(request)
    response = HttpResponseRedirect(reverse('index'))
    response.delete_cookie('jwt_token')
    return response


# ============================================================================
# Content Reporting and Moderation Views
# ============================================================================

@login_required
@require_http_methods(['POST'])
def report_post(request, post_id):
    """Report inappropriate content"""
    post = get_object_or_404(CommonPost, pk=post_id)
    
    reason = request.POST.get('reason')
    description = request.POST.get('description', '')
    
    if not reason:
        messages.error(request, 'Please select a reason for reporting.')
        return redirect('index')
    
    # Check if user has already reported this post
    existing_report = ContentReport.objects.filter(
        post=post,
        reporter=request.user
    ).exists()
    
    if existing_report:
        messages.warning(request, 'You have already reported this post.')
        return redirect('index')
    
    # Create report
    report = ContentReport.objects.create(
        post=post,
        reporter=request.user,
        reason=reason,
        description=description
    )
    
    messages.success(request, 'Thank you for reporting. Our team will review this shortly.')
    return redirect('index')


@login_required
@moderator_required
def moderator_dashboard(request):
    """Dashboard for moderators and admins to review reports"""
    pending_reports = ContentReport.objects.filter(
        status='pending'
    ).select_related('post__author', 'reporter').order_by('-created_at')
    
    report_stats = {
        'pending': ContentReport.objects.filter(status='pending').count(),
        'approved': ContentReport.objects.filter(status='approved').count(),
        'rejected': ContentReport.objects.filter(status='rejected').count(),
        'resolved': ContentReport.objects.filter(status='resolved').count(),
    }
    
    # Get students list with post count for promotion (only admins can promote to admin)
    students_list = User.objects.filter(role='student').annotate(
        posts_count=Count('posts')
    ).order_by('-date_joined')
    
    return render(request, 'accounts/moderator_dashboard.html', {
        'pending_reports': pending_reports,
        'report_stats': report_stats,
        'students_list': students_list,
    })

@login_required
@moderator_required
def advanced_moderation(request):
    """New REST-powered dashboard for advanced moderation"""
    return render(request, 'accounts/advanced_moderation.html')


@login_required
@moderator_required
@require_http_methods(['POST'])
def review_report(request, report_id):
    """Review a content report and take action"""
    report = get_object_or_404(ContentReport, pk=report_id)
    
    action = request.POST.get('action')
    review_notes = request.POST.get('review_notes', '')
    
    if action not in ['approve', 'reject', 'resolve']:
        return JsonResponse({'error': 'Invalid action'}, status=400)
    
    # Map action to status
    status_map = {
        'approve': 'approved',
        'reject': 'rejected',
        'resolve': 'resolved',
    }
    
    report.status = status_map[action]
    report.reviewed_by = request.user
    report.review_notes = review_notes
    report.save()
    messages.success(request, 'Report status updated.')
    return redirect('moderator_dashboard')


@login_required
def user_profile(request, username=None):
    """Display user profile"""
    if username:
        user = get_object_or_404(User, username=username)
    else:
        user = request.user
    
    posts = CommonPost.objects.filter(author=user).count()
    comments = Comment.objects.filter(author=user).count()
    
    user_posts = CommonPost.objects.filter(author=user).order_by('-created_at')[:5]
    
    context = {
        'profile_user': user,
        'posts_count': posts,
        'comments_count': comments,
        'user_posts': user_posts,
        'is_own_profile': (user == request.user),
    }
    
    return render(request, 'accounts/user_profile.html', context)


@login_required
@admin_required
def admin_panel(request):
    """Admin panel for system management"""
    user_stats = {
        'total_users': User.objects.count(),
        'students': User.objects.filter(role='student').count(),
        'moderators': User.objects.filter(role='moderator').count(),
        'admins': User.objects.filter(role='admin').count(),
        'verified_users': User.objects.filter(is_verified=True).count(),
    }
    
    report_stats = {
        'pending': Report.objects.filter(status='pending').count(),
        'under_review': Report.objects.filter(status='under_review').count(),
        'rejected': Report.objects.filter(status='rejected').count(),
        'resolved': Report.objects.filter(status='resolved').count(),
    }
    
    recent_reports = Report.objects.all().order_by('-created_at')[:10]
    staff_list = User.objects.filter(role__in=['moderator', 'admin']).order_by('role', 'username')
    
    # Get students list with post count for promotion
    students_list = User.objects.filter(role='student').annotate(
        posts_count=Count('posts')
    ).order_by('-date_joined')
    
    return render(request, 'accounts/admin_panel.html', {
        'user_stats': user_stats,
        'report_stats': report_stats,
        'recent_reports': recent_reports,
        'staff_list': staff_list,
        'students_list': students_list,
    })


@login_required
@admin_required
@require_http_methods(['POST'])
def promote_user(request, user_id):
    """Promote user to moderator or admin"""
    user = get_object_or_404(User, pk=user_id)
    new_role = request.POST.get('role')
    
    if new_role not in ['student', 'moderator', 'admin']:
        messages.error(request, 'Invalid role.')
        return redirect('admin_panel')
    
    old_role = user.get_role_display()
    user.role = new_role
    user.save()
    
    messages.success(request, f'{user.username} role changed from {old_role} to {user.get_role_display()}.')
    return redirect('admin_panel')


@login_required
@admin_required
@require_http_methods(['POST'])
def manage_user(request, user_id):
    """Manage user account (verify, unverify, warn, suspend)"""
    user = get_object_or_404(User, pk=user_id)
    action = request.POST.get('action')
    
    if action == 'verify':
        user.is_verified = True
        user.save()
        messages.success(request, f'{user.username} verified.')
    elif action == 'unverify':
        user.is_verified = False
        user.save()
        messages.success(request, f'{user.username} verification revoked.')
    elif action == 'suspend':
        user.is_active = False
        user.save()
        messages.success(request, f'{user.username} suspended.')
    elif action == 'unsuspend':
        user.is_active = True
        user.save()
        messages.success(request, f'{user.username} unsuspended.')
    elif action == 'warn':
        messages.success(request, f'{user.username} has been warned.')
    
    return redirect('admin_panel')