"""
GDPR Compliance Tests
====================

Tests for GDPR compliance features:
- Cookie consent middleware
- Privacy preferences
- Data export
- Data deletion
"""

import json
from datetime import datetime, timedelta

from django.contrib.auth import get_user_model
from django.http import HttpResponse
from django.test import Client, RequestFactory, TestCase
from django.utils import timezone

import pytest

from apps.core.middleware.gdpr_compliance import (
    CookieConsentMiddleware,
    DataCollectionLoggingMiddleware,
    PrivacyPreferencesMiddleware,
    clear_consent_cookie,
    get_consent_categories,
    has_consent_for,
    set_consent_cookie,
)
from apps.core.models.gdpr import (
    ConsentRecord,
    DataDeletionRequest,
    DataExportRequest,
    PrivacyPreferences,
)

User = get_user_model()


@pytest.mark.django_db
class TestCookieConsentMiddleware(TestCase):
    """Test cookie consent middleware."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse()
        self.middleware = CookieConsentMiddleware(self.get_response)

    def test_no_consent_cookie(self):
        """Test request without consent cookie."""
        request = self.factory.get("/")
        self.middleware.process_request(request)

        assert request.gdpr_consent is None
        assert request.needs_consent_banner is True

    def test_valid_consent_cookie(self):
        """Test request with valid consent cookie."""
        # Create consent cookie data
        consent_data = {
            "version": "1.0",
            "timestamp": datetime.now().isoformat(),
            "categories": {
                "necessary": True,
                "functional": True,
                "analytics": False,
                "marketing": False,
            },
        }

        request = self.factory.get("/")
        request.COOKIES[CookieConsentMiddleware.CONSENT_COOKIE_NAME] = json.dumps(
            consent_data
        )

        self.middleware.process_request(request)

        assert request.gdpr_consent is not None
        assert request.needs_consent_banner is False
        assert request.gdpr_consent["categories"]["functional"] is True

    def test_expired_consent_cookie(self):
        """Test expired consent cookie."""
        # Create expired consent
        old_date = datetime.now() - timedelta(days=400)
        consent_data = {
            "version": "1.0",
            "timestamp": old_date.isoformat(),
            "categories": {"necessary": True},
        }

        request = self.factory.get("/")
        request.COOKIES[CookieConsentMiddleware.CONSENT_COOKIE_NAME] = json.dumps(
            consent_data
        )

        self.middleware.process_request(request)

        assert request.gdpr_consent is None
        assert request.needs_consent_banner is True

    def test_cookie_filtering_no_consent(self):
        """Test cookie filtering without consent."""
        request = self.factory.get("/")
        self.middleware.process_request(request)

        response = HttpResponse()
        response.set_cookie("sessionid", "test")
        response.set_cookie("_ga", "analytics")

        filtered_response = self.middleware.process_response(request, response)

        # Only necessary cookies allowed
        assert "sessionid" in filtered_response.cookies
        assert "_ga" not in filtered_response.cookies


@pytest.mark.django_db
class TestPrivacyPreferences(TestCase):
    """Test privacy preferences."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_privacy_preferences(self):
        """Test creating privacy preferences."""
        prefs = PrivacyPreferences.objects.create(
            user=self.user,
            data_retention_period=180,
            allow_profiling=False,
            allow_analytics=True,
        )

        assert prefs.user == self.user
        assert prefs.data_retention_period == 180
        assert prefs.allow_profiling is False
        assert prefs.allow_analytics is True

    def test_default_privacy_preferences(self):
        """Test default privacy preferences."""
        prefs = PrivacyPreferences.objects.create(user=self.user)

        assert prefs.data_retention_period == 365
        assert prefs.allow_profiling is False
        assert prefs.allow_third_party is False


@pytest.mark.django_db
class TestConsentRecord(TestCase):
    """Test consent record."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_consent_record(self):
        """Test creating consent record."""
        record = ConsentRecord.objects.create(
            user=self.user,
            consent_type="cookie_consent",
            consented=True,
            consent_text="User accepted all cookies",
            consent_version="1.0",
        )

        assert record.user == self.user
        assert record.consent_type == "cookie_consent"
        assert record.consented is True

    def test_consent_withdrawal(self):
        """Test consent withdrawal."""
        # Grant consent
        ConsentRecord.objects.create(
            user=self.user,
            consent_type="marketing",
            consented=True,
            consent_text="User accepted marketing",
            consent_version="1.0",
        )

        # Withdraw consent
        ConsentRecord.objects.create(
            user=self.user,
            consent_type="marketing",
            consented=False,
            consent_text="User withdrew marketing consent",
            consent_version="1.0",
        )

        # Get latest record
        latest = ConsentRecord.objects.filter(
            user=self.user, consent_type="marketing"
        ).first()

        assert latest.consented is False


@pytest.mark.django_db
class TestDataExportRequest(TestCase):
    """Test data export request."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )
        self.client = Client()

    def test_create_export_request(self):
        """Test creating data export request."""
        request = DataExportRequest.objects.create(
            user=self.user,
            export_format="json",
            include_categories=["profile", "content"],
        )

        assert request.user == self.user
        assert request.status == "pending"
        assert request.export_format == "json"

    def test_export_request_status_progression(self):
        """Test export request status changes."""
        request = DataExportRequest.objects.create(user=self.user)

        assert request.status == "pending"

        request.status = "processing"
        request.save()
        assert request.status == "processing"

        request.status = "completed"
        request.processed_at = timezone.now()
        request.save()
        assert request.status == "completed"


@pytest.mark.django_db
class TestDataDeletionRequest(TestCase):
    """Test data deletion request."""

    def setUp(self):
        """Set up test fixtures."""
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_create_deletion_request(self):
        """Test creating data deletion request."""
        request = DataDeletionRequest.objects.create(
            user=self.user,
            delete_account=True,
            verification_code="ABC123",
            verification_expires_at=timezone.now() + timedelta(hours=24),
        )

        assert request.user == self.user
        assert request.status == "pending"
        assert request.delete_account is True
        assert request.verification_code == "ABC123"

    def test_deletion_grace_period(self):
        """Test 30-day grace period for deletion."""
        request = DataDeletionRequest.objects.create(
            user=self.user,
            scheduled_deletion_at=timezone.now() + timedelta(days=30),
        )

        # Should be scheduled for 30 days from now
        delta = request.scheduled_deletion_at - timezone.now()
        assert 29 <= delta.days <= 31  # Allow some margin


@pytest.mark.django_db
class TestGDPRViews(TestCase):
    """Test GDPR views."""

    def setUp(self):
        """Set up test fixtures."""
        self.client = Client()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_cookie_consent_save(self):
        """Test saving cookie consent."""
        response = self.client.post(
            "/gdpr/cookie-consent/",
            data=json.dumps(
                {
                    "categories": {
                        "necessary": True,
                        "functional": True,
                        "analytics": False,
                        "marketing": False,
                    }
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True

    def test_privacy_preferences_update(self):
        """Test updating privacy preferences."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            "/gdpr/privacy-preferences/",
            data=json.dumps(
                {
                    "data_retention_period": 180,
                    "allow_analytics": True,
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200

        # Verify preferences saved
        prefs = PrivacyPreferences.objects.get(user=self.user)
        assert prefs.data_retention_period == 180
        assert prefs.allow_analytics is True

    def test_request_data_export(self):
        """Test requesting data export."""
        self.client.login(username="testuser", password="testpass123")

        response = self.client.post(
            "/gdpr/data-export/",
            data=json.dumps(
                {
                    "format": "json",
                    "categories": ["profile", "content"],
                }
            ),
            content_type="application/json",
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "request_id" in data


class TestHelperFunctions(TestCase):
    """Test helper functions."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()

    def test_set_consent_cookie(self):
        """Test setting consent cookie."""
        response = HttpResponse()
        categories = {
            "necessary": True,
            "functional": True,
            "analytics": False,
            "marketing": False,
        }

        set_consent_cookie(response, categories)

        assert CookieConsentMiddleware.CONSENT_COOKIE_NAME in response.cookies

    def test_clear_consent_cookie(self):
        """Test clearing consent cookie."""
        response = HttpResponse()
        response.set_cookie(CookieConsentMiddleware.CONSENT_COOKIE_NAME, "test")

        clear_consent_cookie(response)

        # Cookie should be marked for deletion
        cookie = response.cookies[CookieConsentMiddleware.CONSENT_COOKIE_NAME]
        assert cookie["max-age"] == 0

    def test_has_consent_for(self):
        """Test checking consent for category."""
        request = self.factory.get("/")
        request.gdpr_consent = {
            "categories": {
                "necessary": True,
                "analytics": True,
                "marketing": False,
            }
        }

        assert has_consent_for(request, "analytics") is True
        assert has_consent_for(request, "marketing") is False
