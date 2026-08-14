from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from common.services.calendar import build_trip_calendar, calendar_response
from recovery.models import RecoveryItem,InflightCheck
from .models import Trip, Airport
from django import forms
from django.contrib import messages
from django.db import IntegrityError
from common.services.score import calculate_expected_score, calculate_actual_score, calculate_target_score
from common.services.timezone import timezone_diff_minutes, travel_direction, to_timezone
from django.utils import timezone
from common.ai.summaries import get_expected_score_summary, get_score_diff_explanation
from datetime import timedelta
from trips.services import refresh_trip_status
from common.services.recovery import CHECK_TYPE_INPUT_MODE, get_or_create_recovery_items, RECOVERY_ITEM_CATALOG
from zoneinfo import ZoneInfo
from datetime import timezone as dt_timezone

KST = ZoneInfo("Asia/Seoul")

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
    draft = request.session.get("trip_draft")

    if request.method == "POST":
        form = TripStep1Form(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            if data["origin_airport"] == data["destination_airport"]:
                form.add_error(None, "출발지와 도착지가 같습니다")
            else:
                new_draft = {
                    "origin_airport_id": data["origin_airport"].id,
                    "destination_airport_id": data["destination_airport"].id,
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
                "destination_airport": draft.get("destination_airport_id"),
                "layover_count": draft.get("layover_count"),
                "max_layover_minutes": draft.get("max_layover_minutes"),
            }
        form = TripStep1Form(initial=initial)
    return render(request, "trips/create_step1.html", {"form": form})

class TripStep1Form(forms.Form):
    origin_airport = forms.ModelChoiceField(queryset=Airport.objects.filter(active=True), label="출발 공항")
    destination_airport = forms.ModelChoiceField(queryset=Airport.objects.filter(active=True), label="도착 공항")
    layover_count = forms.ChoiceField(
        choices=Trip.LayoverCount.choices, widget=forms.RadioSelect, initial="none"
    )
    max_layover_minutes = forms.IntegerField(required=False, min_value=0, label="대기 시간")

@login_required
def trip_create_step2_view(request):
    draft = request.session.get("trip_draft")
    if not draft:
        messages.error(request, "여정 정보를 먼저 입력해주세요")
        return redirect("trips:create_step1")

    editing_trip_id = draft.get("editing_trip_id")

    if request.method == "POST":
        form = TripStep2Form(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            departure_at = data["departure_at"]
            arrival_at = data["arrival_at"]
            total_minutes = int((arrival_at - departure_at).total_seconds() // 60)

            if total_minutes < 360:
                form.add_error(None, "총 비행시간이 6시간 미만인 여정은 등록 불가")
            else:
                origin_airport = Airport.objects.get(pk=draft["origin_airport_id"])
                destination_airport = Airport.objects.get(pk=draft["destination_airport_id"])
                diff = timezone_diff_minutes(origin_airport.timezone, destination_airport.timezone)
                direction = travel_direction(origin_airport.timezone, destination_airport.timezone)
                expected_score, breakdown = calculate_expected_score(
                    total_minutes, diff, draft["layover_count"]
                )
                trip_duration_minutes = int(data["trip_duration_days"] * 24 * 60)

                if editing_trip_id:
                    # 수정 모드 — 기존 Trip 업데이트, 점수 재계산
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
                        messages.error(request, "진행 중인 여정이 있습니다. 새로 등록하면 이전 여정이 종료됩니다")
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
                "departure_at": timezone.localtime(trip.departure_at, KST).strftime("%Y-%m-%dT%H:%M"),
                "arrival_at": timezone.localtime(trip.arrival_at, KST).strftime("%Y-%m-%dT%H:%M"),
                "trip_duration_days": trip.next_schedule_after_minutes // (24 * 60),
            }
        form = TripStep2Form(initial=initial)
    return render(request, "trips/create_step2.html", {"form": form})

TRIP_DURATION_CHOICES = [(i, f"{i}일") for i in range(1, 15)]


class TripStep2Form(forms.Form):
    departure_at = forms.DateTimeField(
        label="출발 시간",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    arrival_at = forms.DateTimeField(
        label="도착 시간",
        widget=forms.DateTimeInput(attrs={"type": "datetime-local"}, format="%Y-%m-%dT%H:%M"),
        input_formats=["%Y-%m-%dT%H:%M"],
    )
    trip_duration_days = forms.TypedChoiceField(
        choices=TRIP_DURATION_CHOICES, coerce=int, label="여행 기간"
    )

    def _to_utc_from_kst(self, value):
        if timezone.is_aware(value):
            value = timezone.make_naive(value, timezone=dt_timezone.utc)
        value = value.replace(tzinfo=KST)
        return value.astimezone(dt_timezone.utc)

    def clean_departure_at(self):
        return self._to_utc_from_kst(self.cleaned_data["departure_at"])

    def clean_arrival_at(self):
        return self._to_utc_from_kst(self.cleaned_data["arrival_at"])

@login_required
def trip_registration_cancel_view(request):
    request.session.pop("trip_draft", None)
    return redirect("trips:home")

DISRUPTION_CHOICES = [
    (0, "0점 — 평소처럼 다 했어요"),
    (1, "1점 — 거의 다 했지만 조금 피로했어요"),
    (2, "2점 — 절반 정도만 했어요"),
    (3, "3점 — 중요한 일만 겨우 했어요"),
    (4, "4점 — 거의 아무것도 못 했어요"),
    (5, "5점 — 이틀 이상 영향을 받았어요"),
]

@login_required
def trip_survey_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)

    if request.method == "POST":
        has_experience = request.POST.get("has_recent_flight_experience")
        trip.has_recent_flight_experience = has_experience == "true"

        if trip.has_recent_flight_experience:
            trip.last_flight_date = request.POST.get("last_flight_date") or None
            last_flight_hours = request.POST.get("last_flight_hours")
            trip.last_flight_minutes = int(last_flight_hours) * 60 if last_flight_hours else None
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
            return render(request, "recovery/ing_score.html", {"trip": active_trip})

        return render(request, "recovery/inflight_check.html", _build_inflight_context(active_trip))

    items = get_or_create_recovery_items(active_trip)
    for item in items:
        item.mode = RECOVERY_ITEM_CATALOG.get(item.key, {}).get("mode", "toggle")

    remaining = active_trip.next_schedule_at - timezone.now() if active_trip.next_schedule_at else timedelta(0)
    remaining_hours = max(0, int(remaining.total_seconds() // 3600))

    context = {"trip": active_trip, "items": items, "remaining_hours": remaining_hours}
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

    return {
        "trip": trip,
        "checks": checks_map,
        "input_modes": CHECK_TYPE_INPUT_MODE,
        "remaining_hours": int(remaining_seconds // 3600),
        "remaining_minutes": int((remaining_seconds % 3600) // 60),
        "flight_hours": round(trip.total_flight_minutes / 60),
        "departure_local": to_timezone(trip.departure_at, trip.origin_airport.timezone),
        "arrival_local": to_timezone(trip.arrival_at, trip.destination_airport.timezone),
    }

def _build_before_context(trip):
    return {
        "trip": trip,
        "flight_hours": round(trip.total_flight_minutes / 60),
        "timezone_diff_hours": round(abs(trip.timezone_diff_minutes or 0) / 60),
        "departure_local": to_timezone(trip.departure_at, trip.origin_airport.timezone),
        "arrival_local": to_timezone(trip.arrival_at, trip.destination_airport.timezone),
    }

@login_required
def trip_edit_start_view(request, trip_id):
    trip = get_object_or_404(Trip, pk=trip_id, user=request.user)
    request.session["trip_draft"] = {
        "origin_airport_id": trip.origin_airport_id,
        "destination_airport_id": trip.destination_airport_id,
        "layover_count": trip.layover_count,
        "max_layover_minutes": trip.max_layover_minutes,
        "editing_trip_id": trip.id,
    }
    return redirect("trips:create_step1")