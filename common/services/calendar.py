from datetime import timedelta, timezone as dt_timezone

from django.http import HttpResponse
from django.utils import timezone


def _escape_ics_text(value):
    return (
        str(value)
        .replace("\\", "\\\\")
        .replace("\n", "\\n")
        .replace(",", "\\,")
        .replace(";", "\\;")
    )


def _format_utc(dt):
    if timezone.is_naive(dt):
        dt = timezone.make_aware(dt, timezone=dt_timezone.utc)
    return dt.astimezone(dt_timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _event(uid, title, starts_at, description="", duration_minutes=30):
    ends_at = starts_at + timedelta(minutes=duration_minutes)
    return [
        "BEGIN:VEVENT",
        f"UID:{_escape_ics_text(uid)}",
        f"DTSTAMP:{_format_utc(timezone.now())}",
        f"DTSTART:{_format_utc(starts_at)}",
        f"DTEND:{_format_utc(ends_at)}",
        f"SUMMARY:{_escape_ics_text(title)}",
        f"DESCRIPTION:{_escape_ics_text(description)}",
        "END:VEVENT",
    ]


def build_trip_calendar(trip, recovery_items):
    lines = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        "PRODID:-//THRIVE//Recovery Calendar//KO",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
    ]

    if trip.landing_at:
        lines.extend(
            _event(
                uid=f"trip-{trip.pk}-landing@thrive",
                title=f"{trip.route_name} 착륙 후 회복 시작",
                starts_at=trip.landing_at,
                description="의학적 진단이 아닌 참고 지표입니다.",
                duration_minutes=30,
            )
        )

    for item in recovery_items:
        lines.extend(
            _event(
                uid=f"recovery-{item.pk}@thrive",
                title=f"{item.title} ({item.get_component_display()} +{item.score_delta})",
                starts_at=item.scheduled_at,
                description=item.reason_text or "회복 점수를 올리기 위한 추천 항목입니다.",
                duration_minutes=20,
            )
        )

    lines.append("END:VCALENDAR")
    return "\r\n".join(lines) + "\r\n"


def calendar_response(filename, content):
    response = HttpResponse(content, content_type="text/calendar; charset=utf-8")
    response["Content-Disposition"] = f'attachment; filename="{filename}"'
    return response
