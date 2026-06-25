from django import template

from accounts.date_labels import friendly_datetime

register = template.Library()


@register.filter
def friendly_date(value):
    return friendly_datetime(value)
