"""
Decorators for role-based access control and permission checking
"""
from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.http import HttpResponseForbidden
from django.contrib.auth.decorators import login_required


def admin_required(view_func):
    """Decorator to restrict view to administrators only"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_admin():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def moderator_required(view_func):
    """Decorator to restrict view to moderators and administrators"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_moderator():
            messages.error(request, 'You do not have permission to access this page.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def student_required(view_func):
    """Decorator to ensure user is authenticated and verified"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            messages.warning(request, 'Please verify your college email to access this feature.')
            return redirect('index')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_post(view_func):
    """Decorator to check if user can create posts"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_verified:
            messages.error(request, 'You must verify your email before posting.')
            return redirect('profile')
        return view_func(request, *args, **kwargs)
    return wrapper


def can_moderate(view_func):
    """Decorator to check if user can perform moderation actions"""
    @wraps(view_func)
    @login_required
    def wrapper(request, *args, **kwargs):
        if not request.user.is_moderator():
            messages.error(request, 'You do not have moderation permissions.')
            return HttpResponseForbidden('Forbidden')
        return view_func(request, *args, **kwargs)
    return wrapper
