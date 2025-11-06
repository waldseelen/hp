"""
Unit tests for Portfolio GDPR Compliance Models.

Advanced GDPR scenarios including:
- Cookie consent lifecycle and expiration
- Data export request workflows
- Account deletion grace periods and confirmations
- GDPR data retention policies

Target: 18-20 comprehensive GDPR compliance tests.
"""

from datetime import timedelta
from unittest.mock import MagicMock, patch

from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from apps.portfolio.models import (
    AccountDeletionRequest,
    Admin,
    CookieConsent,
    DataExportRequest,
)


@pytest.mark.django_db
class TestGDPRCookieConsentWorkflow:
    """Test GDPR cookie consent workflows and lifecycle."""

    def test_consent_update_workflow(self):
        """Test updating existing consent preferences."""
        # Initial consent with minimal permissions
        consent = CookieConsent.objects.create(
            session_key="update_test",
            ip_address="192.168.1.100",
            user_agent="Test Browser",
            functional=False,
            analytics=False,
            marketing=False,
        )
        initial_consent_date = consent.consent_given_at

        # Update consent preferences
        consent.functional = True
        consent.analytics = True
        consent.save()

        consent.refresh_from_db()
        assert consent.functional
        assert consent.analytics
        assert not consent.marketing
        assert consent.updated_at > initial_consent_date

    def test_consent_renewal_after_expiration(self):
        """Test consent renewal workflow after expiration."""
        # Create expired consent
        consent = CookieConsent.objects.create(
            session_key="renewal_test",
            ip_address="192.168.1.101",
            user_agent="Test",
        )
        consent.expires_at = timezone.now() - timedelta(days=10)
        consent.save()

        assert consent.is_expired()

        # Renew consent
        new_consent = CookieConsent.objects.create(
            session_key="renewal_test",
            ip_address="192.168.1.101",
            user_agent="Test",
            functional=True,
            analytics=True,
        )
        assert not new_consent.is_expired()
        assert new_consent.functional

    def test_consent_summary_all_enabled(self):
        """Test consent summary with all permissions enabled."""
        consent = CookieConsent.objects.create(
            session_key="all_enabled",
            ip_address="192.168.1.102",
            user_agent="Test",
            necessary=True,
            functional=True,
            analytics=True,
            marketing=True,
        )
        summary = consent.get_consent_summary()
        assert all(summary.values())

    def test_consent_summary_minimal(self):
        """Test consent summary with only necessary cookies."""
        consent = CookieConsent.objects.create(
            session_key="minimal",
            ip_address="192.168.1.103",
            user_agent="Test",
        )
        summary = consent.get_consent_summary()
        assert summary["necessary"]
        assert not summary["functional"]
        assert not summary["analytics"]
        assert not summary["marketing"]

    def test_consent_tracking_by_ip(self):
        """Test multiple consents from same IP address."""
        ip = "192.168.1.104"

        # Create 3 consents from same IP
        for i in range(3):
            CookieConsent.objects.create(
                session_key=f"session_{i}",
                ip_address=ip,
                user_agent="Test",
            )

        consents = CookieConsent.objects.filter(ip_address=ip)
        assert consents.count() == 3


@pytest.mark.django_db
class TestGDPRDataExportWorkflow:
    """Test GDPR data export request workflows."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for export tests."""
        return Admin.objects.create_user(
            username="export_user",
            email="export_user@example.com",
            name="Export User",
            password="pass",
        )

    def test_export_workflow_pending_to_processing(self, admin_user):
        """Test export status transition: pending → processing."""
        export_req = DataExportRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        assert export_req.status == "pending"

        # Start processing
        export_req.status = "processing"
        export_req.save()

        export_req.refresh_from_db()
        assert export_req.status == "processing"

    def test_export_workflow_processing_to_completed(self, admin_user):
        """Test export status transition: processing → completed."""
        export_req = DataExportRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
            status="processing",
        )

        # Complete export
        export_req.status = "completed"
        export_req.file_path = "/exports/user_123_data.zip"
        export_req.completed_at = timezone.now()
        export_req.save()

        export_req.refresh_from_db()
        assert export_req.status == "completed"
        assert export_req.file_path
        assert export_req.completed_at is not None

    def test_export_workflow_failure_handling(self, admin_user):
        """Test export failure scenario."""
        export_req = DataExportRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
            status="processing",
        )

        # Simulate failure
        export_req.status = "failed"
        export_req.error_message = "Database connection timeout"
        export_req.save()

        export_req.refresh_from_db()
        assert export_req.status == "failed"
        assert "timeout" in export_req.error_message.lower()

    def test_multiple_export_requests_per_user(self, admin_user):
        """Test user can have multiple export requests."""
        # Create 3 export requests
        for i in range(3):
            DataExportRequest.objects.create(
                user=admin_user,
                email=admin_user.email,
            )

        requests = DataExportRequest.objects.filter(user=admin_user)
        assert requests.count() == 3

    def test_export_request_ordering(self, admin_user):
        """Test export requests are ordered by date descending."""
        # Create requests with different dates
        old_req = DataExportRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        old_req.request_date = timezone.now() - timedelta(days=5)
        old_req.save()

        new_req = DataExportRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )

        requests = list(DataExportRequest.objects.filter(user=admin_user))
        assert requests[0] == new_req  # Most recent first
        assert requests[1] == old_req


@pytest.mark.django_db
class TestGDPRAccountDeletionWorkflow:
    """Test GDPR account deletion with 30-day grace period."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for deletion tests."""
        return Admin.objects.create_user(
            username="delete_user",
            email="delete_user@example.com",
            name="Delete User",
            password="pass",
        )

    def test_deletion_grace_period_calculation(self, admin_user):
        """Test 30-day grace period is correctly calculated."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )

        expected_deletion = timezone.now() + timedelta(days=30)
        actual_deletion = deletion_req.scheduled_deletion

        # Allow 1 minute tolerance
        time_diff = abs((actual_deletion - expected_deletion).total_seconds())
        assert time_diff < 60

    def test_deletion_workflow_pending_to_confirmed(self, admin_user):
        """Test deletion workflow: pending → confirmed."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        token = deletion_req.generate_confirmation_token()

        # Confirm deletion
        deletion_req.confirm_deletion()

        assert deletion_req.status == "confirmed"
        assert deletion_req.confirmed_at is not None
        assert deletion_req.confirmation_token == token

    def test_deletion_workflow_cancellation(self, admin_user):
        """Test deletion cancellation before grace period expires."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )

        # Cancel before confirmation
        deletion_req.cancel_deletion()

        assert deletion_req.status == "cancelled"

    def test_deletion_confirmation_expiry(self, admin_user):
        """Test deletion confirmation expires after 72 hours."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )

        # Set request date to 73 hours ago
        deletion_req.request_date = timezone.now() - timedelta(hours=73)
        deletion_req.save()

        assert deletion_req.is_expired()

    def test_deletion_no_expiry_after_confirmation(self, admin_user):
        """Test confirmed deletion requests don't expire."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        deletion_req.confirm_deletion()

        # Set old request date
        deletion_req.request_date = timezone.now() - timedelta(days=10)
        deletion_req.save()

        assert not deletion_req.is_expired()  # Confirmed = no expiry

    def test_deletion_user_data_backup(self, admin_user):
        """Test user data is backed up before deletion."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )

        # Simulate data backup
        deletion_req.user_data_backup = {
            "email": admin_user.email,
            "name": admin_user.name,
            "created_at": str(admin_user.created_at),
            "posts_count": 5,
        }
        deletion_req.save()

        assert deletion_req.user_data_backup["email"] == admin_user.email
        assert "posts_count" in deletion_req.user_data_backup

    def test_deletion_with_reason(self, admin_user):
        """Test deletion request with optional reason."""
        reason = "No longer need the account"
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
            reason=reason,
        )

        assert deletion_req.reason == reason

    def test_deletion_token_uniqueness(self, admin_user):
        """Test confirmation tokens are unique."""
        deletion_req1 = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        token1 = deletion_req1.generate_confirmation_token()

        # Create second user
        admin_user2 = Admin.objects.create_user(
            username="delete_user2",
            email="delete_user2@example.com",
            name="Delete User 2",
            password="pass",
        )
        deletion_req2 = AccountDeletionRequest.objects.create(
            user=admin_user2,
            email=admin_user2.email,
        )
        token2 = deletion_req2.generate_confirmation_token()

        assert token1 != token2


@pytest.mark.django_db
class TestGDPRDataRetentionPolicies:
    """Test GDPR data retention and cleanup policies."""

    def test_expired_consents_identification(self):
        """Test identification of expired cookie consents."""
        # Create mix of valid and expired consents
        valid_consent = CookieConsent.objects.create(
            session_key="valid",
            ip_address="192.168.1.200",
            user_agent="Test",
        )

        expired_consent = CookieConsent.objects.create(
            session_key="expired",
            ip_address="192.168.1.201",
            user_agent="Test",
        )
        expired_consent.expires_at = timezone.now() - timedelta(days=1)
        expired_consent.save()

        # Query expired consents
        expired = CookieConsent.objects.filter(expires_at__lt=timezone.now())
        assert expired.count() == 1
        assert expired.first() == expired_consent

    def test_pending_deletion_requests_cleanup(self):
        """Test cleanup of expired pending deletion requests."""
        admin_user = Admin.objects.create_user(
            username="cleanup_user",
            email="cleanup@example.com",
            name="Cleanup User",
            password="pass",
        )

        # Create expired pending request
        expired_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email=admin_user.email,
        )
        expired_req.request_date = timezone.now() - timedelta(hours=80)
        expired_req.save()

        # Query expired pending requests
        expired_pending = AccountDeletionRequest.objects.filter(
            status="pending", request_date__lt=timezone.now() - timedelta(hours=72)
        )
        assert expired_pending.count() == 1
