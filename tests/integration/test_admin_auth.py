import os

from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import make_password
from django.test import TestCase
from django.urls import reverse


class RestrictedAdminLoginTests(TestCase):
    # Use environment variables for test credentials
    email = os.environ.get("TEST_ADMIN_EMAIL", "test@example.com")
    password = os.environ.get("TEST_ADMIN_PASSWORD", "test-password-change-me")

    def setUp(self):
        self._previous_email = os.environ.get("ALLOWED_ADMIN_EMAIL")
        self._previous_hash = os.environ.get("ALLOWED_ADMIN_PASSWORD_HASH")
        os.environ["ALLOWED_ADMIN_EMAIL"] = self.email
        os.environ["ALLOWED_ADMIN_PASSWORD_HASH"] = make_password(self.password)

    def tearDown(self):
        if self._previous_email is None:
            os.environ.pop("ALLOWED_ADMIN_EMAIL", None)
        else:
            os.environ["ALLOWED_ADMIN_EMAIL"] = self._previous_email

        if self._previous_hash is None:
            os.environ.pop("ALLOWED_ADMIN_PASSWORD_HASH", None)
        else:
            os.environ["ALLOWED_ADMIN_PASSWORD_HASH"] = self._previous_hash

    def test_admin_login_succeeds_for_allowed_account(self):
        response = self.client.post(
            reverse("admin:login"),
            {"username": self.email, "password": self.password},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertIn("_auth_user_id", self.client.session)

        user = get_user_model().objects.get(email__iexact=self.email)
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)
        self.assertFalse(user.has_usable_password())

    def test_admin_login_rejects_unknown_accounts(self):
        response = self.client.post(
            reverse("admin:login"),
            {"username": "bogus@example.com", "password": self.password},
            follow=True,
        )

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Yetkisiz giris")
        self.assertNotIn("_auth_user_id", self.client.session)
        self.assertFalse(get_user_model().objects.exists())
