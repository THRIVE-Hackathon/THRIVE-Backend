from django.utils import timezone

from .models import Trip


def refresh_trip_status(trip):
    now = timezone.now()

    if trip.status == Trip.Status.CREATED and trip.arrival_at and now >= trip.arrival_at:
        trip.landing_at = trip.arrival_at
        trip.status = Trip.Status.LANDED
        trip.save(update_fields=["landing_at", "status"])

    if trip.status == Trip.Status.RECOVERING and trip.next_schedule_at and now >= trip.next_schedule_at:
        trip.status = Trip.Status.DONE
        trip.save(update_fields=["status"])

    return trip