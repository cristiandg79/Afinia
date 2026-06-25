from datetime import timedelta

from django.utils import timezone


def friendly_datetime(value):
    if not value:
        return ''
    local_value = timezone.localtime(value)
    value_date = local_value.date()
    today = timezone.localdate()
    time_label = local_value.strftime('%H:%M')
    if value_date == today:
        return f'Hoy, {time_label}'
    if value_date == today - timedelta(days=1):
        return f'Ayer, {time_label}'
    return local_value.strftime('%d/%m/%Y %H:%M')
