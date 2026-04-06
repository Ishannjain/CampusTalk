import datetime
import jwt
from django.conf import settings
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.http import HttpResponseRedirect
from django.shortcuts import get_object_or_404, redirect, render
from django.urls import reverse

from .forms import CustomUserCreationForm, LoginForm, PostForm, CommentForm, ChatMessageForm
from .models import User, CommonPost, Comment, ChatMessage


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

        return render(request, 'accounts/index.html', {
            'posts': posts,
            'common_chat_preview': reversed(common_chat_preview),
            'other_users': other_users,
            'post_form': post_form,
            'comment_form': comment_form,
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