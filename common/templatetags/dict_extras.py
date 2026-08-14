from django import template

register = template.Library()


@register.filter
def dict_get(d, key):
    return d.get(key)

@register.filter
def div_minutes_to_days(minutes):
    return round(minutes / (60 * 24))

@register.filter
def div_minutes_to_hours(minutes):
    return round(minutes / 60) if minutes else 0