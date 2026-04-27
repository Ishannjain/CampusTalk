import json
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import timedelta
from django.db.models import Count
from django.shortcuts import get_object_or_404

from .models import Report, ModerationAction, SystemNotification, CommonPost, Comment, User
from .decorators import moderator_required

# Decorator to parse JSON body
def require_json(view_func):
    def wrapper(request, *args, **kwargs):
        if request.content_type == 'application/json':
            try:
                request.json = json.loads(request.body)
            except json.JSONDecodeError:
                return JsonResponse({'error': 'Invalid JSON data'}, status=400)
        else:
            request.json = {}
        return view_func(request, *args, **kwargs)
    return wrapper

@csrf_exempt
@login_required
@require_http_methods(["POST"])
@require_json
def create_report(request):
    """
    POST /api/reports/
    """
    data = request.json
    target_type = data.get('target_type')
    target_id = data.get('target_id')
    reason = data.get('reason')
    description = data.get('description', '')

    if not all([target_type, target_id, reason]):
        return JsonResponse({'error': 'Missing required fields (target_type, target_id, reason)'}, status=400)

    if target_type not in ['post', 'comment', 'user']:
        return JsonResponse({'error': 'Invalid target_type'}, status=400)

    # Prevent duplicate reports from same user
    existing = Report.objects.filter(
        reporter=request.user,
        target_type=target_type,
        target_id=target_id
    ).exists()

    if existing:
        return JsonResponse({'error': 'You have already reported this item'}, status=409)

    # Rate limiting: max 5 reports per hour
    one_hour_ago = timezone.now() - timedelta(hours=1)
    recent_reports_count = Report.objects.filter(
        reporter=request.user,
        created_at__gte=one_hour_ago
    ).count()

    if recent_reports_count >= 5:
        return JsonResponse({'error': 'Rate limit exceeded. Maximum 5 reports per hour.'}, status=429)

    # Validate target exists
    try:
        target_id = int(target_id)
        if target_type == 'post':
            target_exists = CommonPost.objects.filter(id=target_id).exists()
        elif target_type == 'comment':
            target_exists = Comment.objects.filter(id=target_id).exists()
        elif target_type == 'user':
            target_exists = User.objects.filter(id=target_id).exists()
            if target_id == request.user.id:
                return JsonResponse({'error': 'You cannot report yourself'}, status=400)
        if not target_exists:
            return JsonResponse({'error': 'Target item not found'}, status=404)
    except ValueError:
        return JsonResponse({'error': 'target_id must be an integer'}, status=400)

    report = Report.objects.create(
        reporter=request.user,
        target_type=target_type,
        target_id=target_id,
        reason=reason,
        description=description
    )

    # Notify moderators
    moderators = User.objects.filter(role__in=['admin', 'moderator'])
    for mod in moderators:
        SystemNotification.objects.create(
            recipient=mod,
            message=f"New report submitted by {request.user.username} on a {target_type}."
        )

    return JsonResponse({
        'message': 'Report submitted successfully',
        'report_id': report.id
    }, status=201)

@login_required
@moderator_required
@require_http_methods(["GET"])
def list_reports(request):
    """
    GET /api/reports/
    """
    status_filter = request.GET.get('status')
    type_filter = request.GET.get('type')

    reports = Report.objects.all().select_related('reporter')
    
    if status_filter:
        reports = reports.filter(status=status_filter)
    if type_filter:
        reports = reports.filter(target_type=type_filter)

    data = []
    for r in reports:
        data.append({
            'id': r.id,
            'reporter_username': r.reporter.username,
            'target_type': r.target_type,
            'target_id': r.target_id,
            'reason': r.get_reason_display(),
            'status': r.status,
            'status_display': r.get_status_display(),
            'created_at': r.created_at.isoformat()
        })

    return JsonResponse({'reports': data})

@login_required
@moderator_required
@require_http_methods(["GET", "PATCH"])
@require_json
def report_detail(request, report_id):
    """
    GET, PATCH /api/reports/<id>/
    """
    report = get_object_or_404(Report, id=report_id)

    if request.method == "GET":
        actions = ModerationAction.objects.filter(report=report).select_related('moderator').order_by('-created_at')
        actions_data = [{
            'action_taken': a.get_action_taken_display(),
            'moderator': a.moderator.username if a.moderator else 'Unknown',
            'notes': a.notes,
            'created_at': a.created_at.isoformat()
        } for a in actions]

        # Get preview of target
        target_preview = "Unknown Target"
        if report.target_type == 'post':
            target = CommonPost.objects.filter(id=report.target_id).first()
            if target: target_preview = f"Title: {target.title} | Body: {target.body[:100]}"
        elif report.target_type == 'comment':
            target = Comment.objects.filter(id=report.target_id).first()
            if target: target_preview = f"Text: {target.text[:100]}"
        elif report.target_type == 'user':
            target = User.objects.filter(id=report.target_id).first()
            if target: target_preview = f"Username: {target.username} | Role: {target.role}"

        data = {
            'id': report.id,
            'reporter': report.reporter.username,
            'target_type': report.target_type,
            'target_id': report.target_id,
            'target_preview': target_preview,
            'reason': report.get_reason_display(),
            'description': report.description,
            'status': report.status,
            'status_display': report.get_status_display(),
            'created_at': report.created_at.isoformat(),
            'actions': actions_data
        }
        return JsonResponse(data)

    elif request.method == "PATCH":
        data = request.json
        new_status = data.get('status')
        if new_status in ['pending', 'under_review', 'resolved', 'rejected']:
            report.status = new_status
            report.save()
            return JsonResponse({'message': 'Status updated'})
        return JsonResponse({'error': 'Invalid status'}, status=400)

@csrf_exempt
@login_required
@moderator_required
@require_http_methods(["POST"])
@require_json
def take_moderation_action(request, report_id):
    """
    POST /api/reports/<id>/action/
    """
    report = get_object_or_404(Report, id=report_id)
    data = request.json
    action_taken = data.get('action_taken')
    notes = data.get('notes', '')

    if action_taken not in ['warn', 'delete_content', 'ban_user', 'ignore']:
        return JsonResponse({'error': 'Invalid action_taken'}, status=400)

    # Actually execute the action based on rules
    if action_taken == 'delete_content':
        if report.target_type == 'post':
            CommonPost.objects.filter(id=report.target_id).delete()
        elif report.target_type == 'comment':
            Comment.objects.filter(id=report.target_id).delete()
        # if user, we don't delete user on 'delete_content', maybe ban instead
    
    elif action_taken == 'ban_user':
        target_user = None
        if report.target_type == 'user':
            target_user = User.objects.filter(id=report.target_id).first()
        elif report.target_type == 'post':
            post = CommonPost.objects.filter(id=report.target_id).select_related('author').first()
            if post: target_user = post.author
        elif report.target_type == 'comment':
            comment = Comment.objects.filter(id=report.target_id).select_related('author').first()
            if comment: target_user = comment.author
        
        if target_user and not target_user.is_superuser:
            target_user.is_active = False
            target_user.save()

    # Create the ModerationAction
    ModerationAction.objects.create(
        report=report,
        moderator=request.user,
        action_taken=action_taken,
        notes=notes
    )

    # Update report status
    report.status = 'resolved' if action_taken != 'ignore' else 'rejected'
    report.save()

    # Notify the reporter
    SystemNotification.objects.create(
        recipient=report.reporter,
        message=f"Your report regarding a {report.target_type} has been reviewed and action has been taken."
    )

    return JsonResponse({'message': 'Action recorded successfully'})

@login_required
@require_http_methods(["GET", "POST"])
def get_unread_notifications(request):
    """
    GET /api/notifications/
    POST /api/notifications/mark_read/
    """
    if request.method == "POST":
        SystemNotification.objects.filter(recipient=request.user, is_read=False).update(is_read=True)
        return JsonResponse({'message': 'Notifications marked as read'})
        
    notifications = SystemNotification.objects.filter(recipient=request.user, is_read=False).order_by('-created_at')
    data = [{'id': n.id, 'message': n.message, 'created_at': n.created_at.isoformat()} for n in notifications]
    return JsonResponse({'notifications': data})
