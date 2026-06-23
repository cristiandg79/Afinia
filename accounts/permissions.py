from functools import wraps

from django.conf import settings
from django.contrib import messages
from django.shortcuts import redirect


def site_admin_usernames():
    configured = getattr(settings, 'AFINIA_ADMIN_USERNAMES', ['cristiandg79', 'elme79'])
    return {username.strip().lower() for username in configured if username.strip()}


def is_site_admin(user):
    if not user or not user.is_authenticated:
        return False
    return user.is_active and (
        user.is_superuser
        or user.is_staff
        or user.username.lower() in site_admin_usernames()
    )


def site_admin_required(view_func):
    @wraps(view_func)
    def wrapper(request, *args, **kwargs):
        if is_site_admin(request.user):
            return view_func(request, *args, **kwargs)
        messages.error(request, 'No tienes permisos para acceder a moderacion.')
        return redirect('dashboard')

    return wrapper
