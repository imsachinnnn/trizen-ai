from functools import wraps
from django.core.exceptions import PermissionDenied
from django.shortcuts import get_object_or_404
from rest_framework.permissions import BasePermission
from .models import Event, EventMember


def is_admin_user(user):
    return user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser)


def is_assigned_to_event(user, event):
    if not user.is_authenticated:
        return False
    if is_admin_user(user):
        return True
    return EventMember.objects.filter(event=event, user=user).exists()


def is_gallery_unlocked(request, slug):
    return bool(request.session.get(f'gallery_unlocked_{slug}'))


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied("Only Admin leads can perform this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


def event_assignment_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        event_id = kwargs.get('event_id') or kwargs.get('pk') or kwargs.get('id')
        event = get_object_or_404(Event, id=event_id)
        if not is_assigned_to_event(request.user, event):
            raise PermissionDenied("You are not assigned to this event.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view


class DRFIsAdminUser(BasePermission):
    def has_permission(self, request, view):
        return is_admin_user(request.user)


class DRFIsAssignedMember(BasePermission):
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        if is_admin_user(request.user):
            return True
        event_id = view.kwargs.get('event_id') or view.kwargs.get('pk')
        if not event_id:
            return False
        return EventMember.objects.filter(event_id=event_id, user=request.user).exists()
