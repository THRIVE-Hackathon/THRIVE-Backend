from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse
from django.utils import timezone

from recovery.models import RecoveryItem

from trips.models import Trip, Airport


class TripListAndCalendarTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        self.origin = Airport.objects.create(
            iata_code="ICN",
            name_ko="인천국제공항",
            city_name="인천",
            country_code="KR",
            timezone="Asia/Seoul",
        )
        self.destination = Airport.objects.create(
            iata_code="CDG",
            name_ko="샤를 드골 공항",
            city_name="파리",
            country_code="FR",
            timezone="Europe/Paris",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            origin_airport=self.origin,
            destination_airport=self.destination,
            total_flight_minutes=780,
            next_schedule_after_minutes=1440,
            landing_at=timezone.now(),
            status=Trip.Status.RECOVERING,
            expected_score=44,
            actual_score=61,
            current_score=61,
            target_score=75,
        )

    def test_trip_list_shows_active_trip(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("trips:list"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "ICN → CDG")
        self.assertContains(response, "회복 중")
        self.assertContains(response, "예상 44")
        self.assertContains(response, "목표 75")

    def test_trip_calendar_exports_ics(self):
        RecoveryItem.objects.create(
            trip=self.trip,
            title="물 500ml",
            component=RecoveryItem.Component.HYDRATION,
            scheduled_at=timezone.now(),
            local_date=timezone.localdate(),
            score_delta=3,
        )
        self.client.force_login(self.user)

        response = self.client.get(reverse("trips:calendar", kwargs={"trip_id": self.trip.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "text/calendar; charset=utf-8")
        self.assertContains(response, "BEGIN:VCALENDAR")
        self.assertContains(response, "물 500ml")

# Create your tests here.
