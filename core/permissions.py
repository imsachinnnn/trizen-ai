from functools import wraps
from django.core.exceptions import PermissionDenied
from .models import EventMember


def is_admin_user(user):
    return user.is_authenticated and (user.role == 'ADMIN' or user.is_superuser)


def is_assigned_to_event(user, event):
    if not user.is_authenticated:
        return False
    if is_admin_user(user):
        return True
    return EventMember.objects.filter(event=event, user=user).exists()


def admin_required(view_func):
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        if not is_admin_user(request.user):
            raise PermissionDenied("Only Admin leads can perform this action.")
        return view_func(request, *args, **kwargs)
    return _wrapped_view

