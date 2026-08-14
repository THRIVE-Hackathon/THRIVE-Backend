from django.utils import timezone
from .models import Trip


def refresh_trip_status(trip):
    now = timezone.now()

    if trip.status == Trip.Status.CREATED:
        if trip.arrival_at and now >= trip.arrival_at:
            trip.landing_at = trip.landing_at or trip.arrival_at
            trip.status = Trip.Status.LANDED
            trip.save(update_fields=["landing_at", "status"])

    elif trip.status == Trip.Status.RECOVERING:
        if trip.next_schedule_at and now >= trip.next_schedule_at:
            trip.status = Trip.Status.DONE
            trip.save(update_fields=["status"])

    return trip