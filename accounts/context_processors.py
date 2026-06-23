from .permissions import is_site_admin


def moderation(request):
    return {
        'is_site_admin': is_site_admin(getattr(request, 'user', None)),
    }
