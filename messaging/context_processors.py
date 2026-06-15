from .notifications import notification_counts


def notifications(request):
    if not request.user.is_authenticated:
        return {
            'notification_counts': {'messages': 0, 'connections': 0, 'panel': 0},
        }
    return {
        'notification_counts': notification_counts(request.user),
    }
