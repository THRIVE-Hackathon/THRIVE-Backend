from django.contrib.auth import get_user_model
from django.test import TestCase
from django.urls import reverse

from accounts.models import Profile


class AccountFlowTests(TestCase):
    def test_signup_creates_user_and_redirects_to_profile_setup(self):
        response = self.client.post(
            reverse("accounts:signup"),
            {
                "email": "user@example.com",
                "password1": "StrongPass123!",
                "password2": "StrongPass123!",
                "terms_agreed": "on",
            },
        )

        self.assertRedirects(response, reverse("accounts:profile_setup"))
        self.assertTrue(get_user_model().objects.filter(email="user@example.com").exists())

    def test_profile_setup_creates_profile(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile_setup"),
            {
                "nickname": "지유",
                "gender": Profile.Gender.FEMALE,
                "age_group": Profile.AgeGroup.TWENTIES_LATE,
            },
        )

        self.assertRedirects(response, reverse("trips:list"))
        self.assertEqual(user.profile.nickname, "지유")

    def test_profile_edit_updates_profile(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        Profile.objects.create(
            user=user,
            nickname="지유",
            gender=Profile.Gender.FEMALE,
            age_group=Profile.AgeGroup.TWENTIES_LATE,
        )
        self.client.force_login(user)

        response = self.client.post(
            reverse("accounts:profile_edit"),
            {
                "nickname": "유정",
                "gender": Profile.Gender.UNDISCLOSED,
                "age_group": Profile.AgeGroup.THIRTIES,
            },
        )

        self.assertRedirects(response, reverse("accounts:profile"))
        user.profile.refresh_from_db()
        self.assertEqual(user.profile.nickname, "유정")
        self.assertEqual(user.profile.gender, Profile.Gender.UNDISCLOSED)

    def test_settings_page_shows_policy_summary(self):
        user = get_user_model().objects.create_user(
            email="user@example.com",
            password="StrongPass123!",
        )
        Profile.objects.create(
            user=user,
            nickname="지유",
            gender=Profile.Gender.FEMALE,
            age_group=Profile.AgeGroup.TWENTIES_LATE,
        )
        self.client.force_login(user)

        response = self.client.get(reverse("accounts:settings"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "수집하지 않는 정보")
        self.assertContains(response, "의학적 진단이나 처방이 아닌 참고 지표")

# Create your tests here.
