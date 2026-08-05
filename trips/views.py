from django.contrib.auth.decorators import login_required
from django.db.models import Count, Q
from django.shortcuts import get_object_or_404, render

from common.services.calendar import build_trip_calendar, calendar_response
from recovery.models import RecoveryItem

from .models import Trip


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

# Create your views here.
