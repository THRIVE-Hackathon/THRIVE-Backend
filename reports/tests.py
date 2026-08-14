from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from trips.models import Airport, Trip

from .models import TripResult


class ReportTests(TestCase):
    def setUp(self):
        self.user = get_user_model().objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        origin = Airport.objects.create(
            iata_code="ICN",
            name_ko="인천국제공항",
            city_name="인천",
            country_code="KR",
            timezone="Asia/Seoul",
        )
        destination = Airport.objects.create(
            iata_code="CDG",
            name_ko="샤를 드골 공항",
            city_name="파리",
            country_code="FR",
            timezone="Europe/Paris",
        )
        self.trip = Trip.objects.create(
            user=self.user,
            origin_airport=origin,
            destination_airport=destination,
            total_flight_minutes=780,
            next_schedule_after_minutes=1440,
            status=Trip.Status.RECOVERING,
            expected_score=44,
            actual_score=61,
            current_score=73,
            target_score=75,
            score_breakdown={
                "수면": {"penalty": -18, "reason": "시차 8시간"},
                "수분": {"penalty": -13, "reason": "저습도 노출"},
            },
        )

    def test_report_detail_creates_trip_result(self):
        self.client.force_login(self.user)

        response = self.client.post(
            reverse("reports:detail", kwargs={"trip_id": self.trip.pk}),
            {"disruption_score": TripResult.DisruptionScore.DELAYED},
        )

        self.assertRedirects(response, reverse("reports:detail", kwargs={"trip_id": self.trip.pk}))
        self.trip.refresh_from_db()
        self.assertEqual(self.trip.status, Trip.Status.DONE)
        self.assertEqual(self.trip.result.disruption_score, TripResult.DisruptionScore.DELAYED)

    def test_report_detail_shows_score_breakdown(self):
        self.client.force_login(self.user)

        response = self.client.get(reverse("reports:detail", kwargs={"trip_id": self.trip.pk}))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "목표 달성률")
        self.assertContains(response, "시차 8시간")
        self.assertContains(response, "저습도 노출")

# Create your tests here.
