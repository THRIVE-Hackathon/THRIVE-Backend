from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render, redirect
from common.services.calendar import build_trip_calendar, calendar_response
from recovery.models import RecoveryItem
from .models import Trip, City
from django import forms
from django.contrib import messages
from django.db import IntegrityError
from common.services.score import calculate_expected_score, calculate_actual_score, calculate_target_score
from common.services.timezone import timezone_diff_minutes, travel_direction
from django.utils import timezone

@login_required
def trip_list_view(request):
    active_trip = (
        Trip.objects.select_related("origin_city", "destination_city")
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
        "origin_city",
        "destination_city",
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
        past_trips = past_trips.exclude(pk=active_trip.pk)

    context = {
        "active_trip": active_trip,
        "past_trips": past_trips[:20],
    }
    return render(request, "trips/list.html", context)


@login_required
def trip_calendar_view(request, trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related("origin_city", "destination_city"),
        pk=trip_id,
        user=request.user,
    )
    recovery_items = RecoveryItem.objects.filter(trip=trip)
    content = build_trip_calendar(trip, recovery_items)
    return calendar_response(f"thrive-trip-{trip.pk}.ics", content)

class TripCreateForm(forms.Form):
    origin_city = forms.ModelChoiceField(queryset=City.objects.filter(active=True))
    destination_city = forms.ModelChoiceField(queryset=City.objects.filter(active=True))
    layover_count = forms.ChoiceField(choices=Trip.LayoverCount.choices)
    total_flight_minutes = forms.IntegerField(min_value=360)  # 6시간 미만 차단 (F-S1-09)
    max_layover_minutes = forms.IntegerField(required=False)
    next_schedule_after_minutes = forms.IntegerField(min_value=0)

    def clean(self):
        cleaned = super().clean()
        origin = cleaned.get("origin_city")
        destination = cleaned.get("destination_city")
        if origin and destination and origin == destination:
            raise forms.ValidationError("출발지와 도착지가 같습니다")
        return cleaned


@login_required
def trip_create_view(request):
    if request.method == "POST":
        form = TripCreateForm(request.POST)
        if form.is_valid():
            data = form.cleaned_data
            diff = timezone_diff_minutes(
                data["origin_city"].timezone, data["destination_city"].timezone
            )
            direction = travel_direction(
                data["origin_city"].timezone, data["destination_city"].timezone
            )
            expected_score, breakdown = calculate_expected_score(
                data["total_flight_minutes"], diff, data["layover_count"]
            )
            try:
                trip = Trip.objects.create(
                    user=request.user,
                    origin_city=data["origin_city"],
                    destination_city=data["destination_city"],
                    layover_count=data["layover_count"],
                    total_flight_minutes=data["total_flight_minutes"],
                    max_layover_minutes=data.get("max_layover_minutes"),
                    next_schedule_after_minutes=data["next_schedule_after_minutes"],
                    timezone_diff_minutes=diff,
                    travel_direction=direction,
                    expected_score=expected_score,
                    score_breakdown=breakdown,
                )
            except IntegrityError:
                # uniq_active_trip_per_user 제약 위반 (F-S1-10)
                messages.error(request, "진행 중인 여정이 있습니다. 새로 등록하면 이전 여정이 종료됩니다")
                return redirect("trips:list")
            return redirect("trips:expected_score", trip_id=trip.pk)
    else:
        form = TripCreateForm()
    return render(request, "trips/create.html", {"form": form})

@login_required
def trip_expected_score_view(request, trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related("origin_city", "destination_city"),
        pk=trip_id,
        user=request.user,
    )
    context = {
        "trip": trip,
        "flight_hours": round(trip.total_flight_minutes / 60),
        "timezone_diff_hours": round(abs(trip.timezone_diff_minutes or 0) / 60),
    }
    return render(request, "trips/expected_score.html", context)

@login_required
def trip_actual_score_view(request, trip_id):
    trip = get_object_or_404(
        Trip.objects.select_related("origin_city", "destination_city"),
        pk=trip_id,
        user=request.user,
    )

    if trip.status == Trip.Status.CREATED:
        # 착륙 확인 처리 (F-S4-01)
        checks = trip.inflight_checks.all()
        actual_score, breakdown = calculate_actual_score(
            trip.expected_score, trip.score_breakdown, checks
        )
        trip.actual_score = actual_score
        trip.current_score = actual_score
        trip.score_breakdown = breakdown
        trip.landing_at = timezone.now()
        trip.target_score = calculate_target_score(
            actual_score, trip.next_schedule_after_minutes
        )
        trip.status = Trip.Status.LANDED
        trip.save()

    return render(request, "trips/actual_score.html", {"trip": trip})