from datetime import datetime, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django.utils import timezone


def to_timezone(value, timezone_name):
    if timezone.is_naive(value):
        value = timezone.make_aware(value, timezone=dt_timezone.utc)
    return value.astimezone(ZoneInfo(timezone_name))


def timezone_diff_minutes(origin_timezone, destination_timezone, at=None):
    at = at or timezone.now()
    if timezone.is_naive(at):
        at = timezone.make_aware(at, timezone=dt_timezone.utc)

    origin_offset = at.astimezone(ZoneInfo(origin_timezone)).utcoffset()
    destination_offset = at.astimezone(ZoneInfo(destination_timezone)).utcoffset()
    return int((destination_offset - origin_offset).total_seconds() // 60)


def travel_direction(origin_timezone, destination_timezone, at=None):
    diff = timezone_diff_minutes(origin_timezone, destination_timezone, at)
    if diff > 0:
        return "east"
    if diff < 0:
        return "west"
    return "none"


def local_datetime_to_utc(value, timezone_name):
    if not isinstance(value, datetime):
        raise TypeError("value must be a datetime")
    if timezone.is_naive(value):
        value = value.replace(tzinfo=ZoneInfo(timezone_name))
    return value.astimezone(dt_timezone.utc)
