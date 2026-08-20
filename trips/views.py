from datetime import datetime, timedelta, timezone as dt_timezone
from zoneinfo import ZoneInfo

from django import forms
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.db import IntegrityError
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone

from common.ai.summaries import get_expected_score_summary, get_score_diff_explanation
from common.services.calendar import build_trip_calendar, calendar_response
from common.services.recovery import (
    CHECK_TYPE_INPUT_MODE,
    RECOVERY_ITEM_CATALOG,
    get_or_create_recovery_items,
)
from common.services.score import (
    calculate_actual_score,
    calculate_expected_score,
    calculate_target_score,
)
from common.services.timezone import timezone_diff_minutes, to_timezone, travel_direction
from recovery.models import InflightCheck, RecoveryItem
from trips.services import refresh_trip_status
from .models import Airport, Trip

KST = ZoneInfo("Asia/Seoul")

SCORE_COMPONENT_LABELS = {
    "sleep": "수면·리듬",
    "circulation": "순환",
    "hydration": "수분",
    "skin": "피부",
}

INFLIGHT_CHECK_LABELS = {
    "moisturize": "피부 보습하기",
    "sleep": "6시간 취침하기",
    "water": "물 100ml 마시기",
    "stretch": "팔·다리 스트레칭하기",
}

INFLIGHT_CHECK_ORDER = ["moisturize", "sleep", "water", "stretch"]
TRIP_DURATION_CHOICES = [(i, f"{i}일") for i in range(1, 15)]

class TripStep1Form(forms.Form):
    """Step 1: 출발 정보 (출발 공항 + 출발 시간 + 경유 정보)"""
    origin_airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(active=True),
        label="출발 공항",
        widget=forms.Select(attrs={"class": "field__select"}),
    )
    departure_at = forms.DateTimeField(
        label="출발 시간",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "field__input"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    layover_count = forms.ChoiceField(
        choices=Trip.LayoverCount.choices,
        widget=forms.RadioSelect(attrs={"class": "survey-option__input"}),
        initial="none",
        label="경유 여부",
    )
    max_layover_minutes = forms.IntegerField(
        required=False,
        min_value=0,
        label="대기 시간 입력",
        widget=forms.NumberInput(
            attrs={
                "class": "field__input",
                "placeholder": "대기 시간(분)",
                "inputmode": "numeric",
            }
        ),
    )

    def _to_utc_from_kst(self, value):
        if timezone.is_aware(value):
            value = timezone.make_naive(value, dt_timezone.utc)
        value = value.replace(tzinfo=KST)
        return value.astimezone(dt_timezone.utc)

    def clean_departure_at(self):
        return self._to_utc_from_kst(self.cleaned_data["departure_at"])


class TripStep2Form(forms.Form):
    destination_airport = forms.ModelChoiceField(
        queryset=Airport.objects.filter(active=True),
        label="도착 공항",
        widget=forms.Select(attrs={"class": "field__select"}),
    )
    arrival_at = forms.DateTimeField(
        label="도착 시간",
        widget=forms.DateTimeInput(
            attrs={"type": "datetime-local", "class": "field__input"},
            format="%Y-%m-%dT%H:%M",
        ),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    trip_duration_days = forms.TypedChoiceField(
        choices=TRIP_DURATION_CHOICES,
        coerce=int,
        label="여행 기간",
        widget=forms.Select(attrs={"class": "field__select"}),
    )

    def _to_utc_from_kst(self, value):
        if timezone.is_aware(value):
            value = timezone.make_naive(value, dt_timezone.utc)
        value = value.replace(tzinfo=KST)
        return value.astimezone(dt_timezone.utc)

    def clean_arrival_at(self):
        return self._to_utc_from_kst(self.cleaned_data["arrival_at"])

@login_required
def trip_list_view(request):
    active_trip = (
        Trip.objects.select_related("origin_airport", "destination_airport")
        .annotate(
            recovery_count=Count("recovery_items", distinct=True),
            completed_recovery_count=Count(
                "recovery_items",
                filter=Q(recovery_items__status=RecoveryItem.Status.COMPLETED),
                distinct=True,
            ),
        )
        .filter(user=request.user, status__in=Trip.ACTIVE_STATUSES)
        .first()
    )

    past_trips = Trip.objects.select_related(
        "origin_airport",
        "destination_airport",
        "result",
    ).annotate(
        recovery_count=Count("recovery_items", distinct=True),
        completed_recovery_count=Count(
            "recovery_items",
            filter=Q(recovery_items__status=RecoveryItem.Status.COMPLETED),
            distinct=True,
        ),
    ).filter(user=request.user)

    if active_trip:
        refresh_trip_status(active_trip)
        past_trips = past_trips.exclude(pk=active_trip.pk)

    context = {
        "active_trip": active_trip,
        "past_trips": past_trips[:20],
    }
    return render(request, "trips/list.html", context)


@login_required
def trip_calendar_view(request, trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related("origin_airport", "destination_airport"),
        pk=trip_id,
        user=request.user,
    )
    recovery_items = RecoveryItem.objects.filter(trip=trip)
    content = build_trip_calendar(trip, recovery_items)
    return calendar_response(f"thrive-trip-{trip.pk}.ics", content)


@login_required
def trip_create_step1_view(request):
    draft = request.session.get("trip_draft", {})

    if request.method == "POST":
        form = TripStep1Form(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            new_draft = {
                "origin_airport_id": data["origin_airport"].id,
                "departure_at": data["departure_at"].isoformat(),
                "layover_count": data["layover_count"],
                "max_layover_minutes": data.get("max_layover_minutes"),
            }

            if draft and draft.get("editing_trip_id"):
                new_draft["editing_trip_id"] = draft["editing_trip_id"]

            request.session["trip_draft"] = new_draft
            return redirect("trips:create_step2")
    else:
        initial = {}
        if draft:
            initial = {
                "origin_airport": draft.get("origin_airport_id"),
                "layover_count": draft.get("layover_count"),
                "max_layover_minutes": draft.get("max_layover_minutes"),
            }

            if draft.get("departure_at"):
                dep_utc = datetime.fromisoformat(draft["departure_at"])
                initial["departure_at"] = timezone.localtime(dep_utc, KST).strftime("%Y-%m-%dT%H:%M")

        form = TripStep1Form(initial=initial)

    return render(request, "trips/create_step1.html", {"form": form})


@login_required
def trip_create_step2_view(request):
    draft = request.session.get("trip_draft")

    if not draft or "departure_at" not in draft or "origin_airport_id" not in draft:
        messages.error(request, "출발 정보를 먼저 입력해주세요.")
        return redirect("trips:create_step1")

    editing_trip_id = draft.get("editing_trip_id")

    if request.method == "POST":
        form = TripStep2Form(request.POST)
        if form.is_valid():
            data = form.cleaned_data

            departure_at = datetime.fromisoformat(draft["departure_at"])
            arrival_at = data["arrival_at"]  # cleaned_data에서 이미 UTC로 변환됨

            if draft["origin_airport_id"] == data["destination_airport"].id:
                form.add_error("destination_airport", "출발지와 도착지가 같습니다.")
                return render(request, "trips/create_step2.html", {"form": form})

            total_minutes = int((arrival_at - departure_at).total_seconds() // 60)
            if total_minutes < 360:
                form.add_error(None, "총 비행시간이 6시간 미만인 여정은 등록할 수 없습니다.")
                return render(request, "trips/create_step2.html", {"form": form})

            origin_airport = Airport.objects.get(pk=draft["origin_airport_id"])
            destination_airport = data["destination_airport"]
            diff = timezone_diff_minutes(origin_airport.timezone, destination_airport.timezone)
            direction = travel_direction(origin_airport.timezone, destination_airport.timezone)

            expected_score, breakdown = calculate_expected_score(
                total_minutes, diff, draft["layover_count"]
            )
            trip_duration_minutes = int(data["trip_duration_days"] * 24 * 60)

            if editing_trip_id:
                trip = get_object_or_404(Trip, pk=editing_trip_id, user=request.user)
                trip.origin_airport = origin_airport
                trip.destination_airport = destination_airport
                trip.layover_count = draft["layover_count"]
                trip.max_layover_minutes = draft.get("max_layover_minutes")
                trip.total_flight_minutes = total_minutes
                trip.departure_at = departure_at
                trip.arrival_at = arrival_at
                trip.next_schedule_after_minutes = trip_duration_minutes
                trip.timezone_diff_minutes = diff
                trip.travel_direction = direction
                trip.expected_score = expected_score
                trip.score_breakdown = breakdown
                trip.summary_text = get_expected_score_summary(trip)
                trip.save()
            else:
                try:
                    trip = Trip.objects.create(
                        user=request.user,
                        origin_airport=origin_airport,
                        destination_airport=destination_airport,
                        layover_count=draft["layover_count"],
                        max_layover_minutes=draft.get("max_layover_minutes"),
                        total_flight_minutes=total_minutes,
                        departure_at=departure_at,
                        arrival_at=arrival_at,
                        next_schedule_after_minutes=trip_duration_minutes,
                        timezone_diff_minutes=diff,
                        travel_direction=direction,
                        expected_score=expected_score,
                        score_breakdown=breakdown,
                    )
                    trip.summary_text = get_expected_score_summary(trip)
                    trip.save(update_fields=["summary_text"])
                except IntegrityError:
                    messages.error(request, "진행 중인 여정이 있습니다. 새로 등록하면 이전 여정이 종료됩니다.")
                    del request.session["trip_draft"]
                    return redirect("trips:list")

            del request.session["trip_draft"]
            if editing_trip_id:
                return redirect("trips:home")
            return redirect("trips:survey", trip_id=trip.pk)
    else:
        initial = {}
        if editing_trip_id:
            trip = get_object_or_404(Trip, pk=editing_trip_id, user=request.user)
            initial = {
                "destination_airport": trip.destination_airport_id,
                "arrival_at": timezone.localtime(trip.arrival_at, KST).strftime("%Y-%m-%dT%H:%M"),
                "trip_duration_days": trip.next_schedule_after_minutes // (24 * 60),
            }
        form = TripStep2Form(initial=initial)

    return render(request, "trips/create_step2.html", {"form": form})


@login_required
def trip_registration_cancel_view(request):
    request.session.pop("trip_draft", None)
    return redirect("trips:home")


@login_required
def trip_survey_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

    if request.method == "POST":
        has_experience = request.POST.get("has_recent_flight_experience")
        trip.has_recent_flight_experience = has_experience == "true"

        if trip.has_recent_flight_experience:
            trip.last_flight_date = request.POST.get("last_flight_date") or None
            last_flight_hours = request.POST.get("last_flight_hours")
            last_flight_minutes = request.POST.get("last_flight_minutes")
            total_minutes = (int(last_flight_hours) if last_flight_hours else 0) * 60 \
                + (int(last_flight_minutes) if last_flight_minutes else 0)
            trip.last_flight_minutes = total_minutes or None
            trip.typical_impact = request.POST.get("typical_impact", "")
        else:
            trip.last_flight_date = None
            trip.last_flight_minutes = None
            trip.typical_impact = ""

        trip.save(
            update_fields=[
                "has_recent_flight_experience",
                "last_flight_date",
                "last_flight_minutes",
                "typical_impact",
            ]
        )
        return redirect("trips:home")

    context = {"trip": trip, "impact_choices": Trip.TypicalImpact.choices}
    return render(request, "trips/survey.html", context)


@login_required
def trip_survey_skip_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    trip.survey_skipped = True
    trip.save(update_fields=["survey_skipped"])
    return redirect("trips:home")


@login_required
def trip_home_view(request):
    active_trip = (
        Trip.objects.select_related("origin_airport", "destination_airport")
        .filter(user=request.user, status__in=Trip.ACTIVE_STATUSES)
        .first()
    )

    if not active_trip:
        pending_report_trip = (
            Trip.objects.filter(user=request.user, status=Trip.Status.DONE)
            .exclude(result__isnull=False)
            .order_by("-updated_at")
            .first()
        )
        if pending_report_trip:
            return redirect("reports:detail", trip_id=pending_report_trip.pk)
        return render(request, "trips/home_none.html")

    refresh_trip_status(active_trip)
    active_trip.refresh_from_db()

    if active_trip.status == Trip.Status.DONE:
        return redirect("reports:detail", trip_id=active_trip.pk)

    if active_trip.status == Trip.Status.CREATED:
        now = timezone.now()
        if active_trip.departure_at and now >= active_trip.departure_at:
            return render(request, "recovery/inflight_check.html", _build_inflight_context(active_trip))
        return render(request, "trips/home_before.html", _build_before_context(active_trip))

    if active_trip.status == Trip.Status.LANDED:
        if active_trip.actual_score is None:
            checks = active_trip.inflight_checks.all()
            actual_score, breakdown = calculate_actual_score(
                active_trip.expected_score, active_trip.score_breakdown, checks
            )
            active_trip.actual_score = actual_score
            active_trip.current_score = actual_score
            active_trip.score_breakdown = breakdown
            active_trip.landing_at = active_trip.landing_at or timezone.now()
            active_trip.next_schedule_at = active_trip.landing_at + timedelta(
                minutes=active_trip.next_schedule_after_minutes
            )
            active_trip.target_score = calculate_target_score(
                actual_score, active_trip.next_schedule_after_minutes
            )
            active_trip.summary_text = get_score_diff_explanation(active_trip)
            active_trip.save()
            return render(request, "recovery/ing_score.html", _build_landing_context(active_trip))

        return render(request, "recovery/ing_score.html", _build_landing_context(active_trip))

    items = get_or_create_recovery_items(active_trip)
    for item in items:
        item.mode = RECOVERY_ITEM_CATALOG.get(item.key, {}).get("mode", "toggle")

    remaining = active_trip.next_schedule_at - timezone.now() if active_trip.next_schedule_at else timedelta(0)
    remaining_hours = max(0, int(remaining.total_seconds() // 3600))

    context = {
        "trip": active_trip,
        "items": items,
        "remaining_hours": remaining_hours,
        "score_breakdown_items": _score_breakdown_items(active_trip),
    }
    return render(request, "recovery/plan.html", context)


@login_required
def trip_start_recovery_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    if trip.status == Trip.Status.LANDED:
        trip.status = Trip.Status.RECOVERING
        trip.save(update_fields=["status"])
    return redirect("trips:home")


def _build_inflight_context(trip):
    now = timezone.now()
    remaining = trip.arrival_at - now if trip.arrival_at else timedelta(0)
    remaining_seconds = max(0, remaining.total_seconds())

    checks_map = {}
    for check_type, label in InflightCheck.CheckType.choices:
        obj, _ = InflightCheck.objects.get_or_create(
            trip=trip, check_type=check_type, defaults={"count": 0}
        )
        checks_map[check_type] = obj

    inflight_items = [
        {
            "check_type": check_type,
            "label": INFLIGHT_CHECK_LABELS.get(check_type, checks_map[check_type].get_check_type_display()),
            "check": checks_map[check_type],
            "mode": CHECK_TYPE_INPUT_MODE.get(check_type, "counter"),
        }
        for check_type in INFLIGHT_CHECK_ORDER
        if check_type in checks_map
    ]

    return {
        "trip": trip,
        "checks": checks_map,
        "inflight_items": inflight_items,
        "input_modes": CHECK_TYPE_INPUT_MODE,
        "remaining_hours": int(remaining_seconds // 3600),
        "remaining_minutes": int((remaining_seconds % 3600) // 60),
        "flight_hours": round(trip.total_flight_minutes / 60),
        "flight_duration_label": _format_duration(trip.total_flight_minutes),
        "layover_summary": _layover_summary(trip),
        "departure_local": to_timezone(trip.departure_at, trip.origin_airport.timezone),
        "arrival_local": to_timezone(trip.arrival_at, trip.destination_airport.timezone),
        "score_breakdown_items": _score_breakdown_items(trip),
    }


def _build_before_context(trip):
    departure_local = to_timezone(trip.departure_at, trip.origin_airport.timezone)
    arrival_local = to_timezone(trip.arrival_at, trip.destination_airport.timezone)
    recovery_minutes = min(trip.next_schedule_after_minutes, 3 * 24 * 60)
    return {
        "trip": trip,
        "flight_hours": round(trip.total_flight_minutes / 60),
        "flight_duration_label": _format_duration(trip.total_flight_minutes),
        "layover_summary": _layover_summary(trip),
        "timezone_diff_hours": round(abs(trip.timezone_diff_minutes or 0) / 60),
        "departure_local": departure_local,
        "arrival_local": arrival_local,
        "recovery_end_local": arrival_local + timedelta(minutes=recovery_minutes),
        "score_breakdown_items": _score_breakdown_items(trip),
    }


def _build_landing_context(trip):
    expected_score = trip.expected_score or 0
    current_score = trip.current_score if trip.current_score is not None else expected_score
    score_diff = current_score - expected_score
    recovery_window_minutes = min(trip.next_schedule_after_minutes, 3 * 24 * 60)
    recovery_window_hours = max(0, recovery_window_minutes // 60)

    return {
        "trip": trip,
        "score_diff": score_diff,
        "score_diff_abs": abs(score_diff),
        "score_breakdown_items": _score_breakdown_items(trip),
        "trip_duration_days": max(1, round(trip.next_schedule_after_minutes / (60 * 24))),
        "recovery_window_hours": recovery_window_hours,
        "recovery_window_days": max(1, round(recovery_window_hours / 24)),
    }


def _format_duration(total_minutes):
    hours = total_minutes // 60
    minutes = total_minutes % 60
    return f"{hours}시간 {minutes:02d}분"


def _layover_summary(trip):
    if trip.layover_count == Trip.LayoverCount.NONE:
        return "경유 없음"

    summary = f"경유 {trip.get_layover_count_display()}"
    if trip.max_layover_minutes:
        summary += f"({_format_duration(trip.max_layover_minutes)} 대기)"
    return summary


def _score_breakdown_items(trip):
    breakdown = trip.score_breakdown or {}
    items = []
    for key, label in SCORE_COMPONENT_LABELS.items():
        try:
            value = round(float(breakdown.get(key, 0)))
        except (TypeError, ValueError):
            value = 0
        items.append(
            {
                "key": key,
                "label": label,
                "value": value,
                "display": f"{value:+d}점" if value > 0 else f"{value}점",
                "width": min(100, max(8, abs(value) * 4)),
            }
        )
    return items


@login_required
def trip_edit_start_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    request.session["trip_draft"] = {
        "origin_airport_id": trip.origin_airport_id,
        "departure_at": trip.departure_at.isoformat(),
        "layover_count": trip.layover_count,
        "max_layover_minutes": trip.max_layover_minutes,
        "editing_trip_id": trip.id,
    }
    return redirect("trips:create_step1")