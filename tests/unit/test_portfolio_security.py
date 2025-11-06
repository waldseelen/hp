"""
Unit tests for Portfolio Security & Auth Models.

Tests cover:
- Admin (2FA, backup codes, account locking)
- UserSession (device detection, session management)
- CookieConsent (GDPR consent tracking)
- DataExportRequest (GDPR export workflow)
- AccountDeletionRequest (30-day grace period)

Target: 25-30 tests for comprehensive security coverage.
"""

from datetime import timedelta

from django.utils import timezone

import pytest

from apps.portfolio.models import (
    AccountDeletionRequest,
    Admin,
    CookieConsent,
    DataExportRequest,
    UserSession,
)

# ============================================================================
# ADMIN MODEL TESTS (2FA, Backup Codes, Account Locking)
# ============================================================================


@pytest.mark.django_db
class TestAdminModel:
    """Test Admin model - 2FA, backup codes, and account locking."""

    def test_admin_creation(self):
        """Test basic admin creation."""
        admin = Admin.objects.create_user(
            username="admin1",
            email="admin@example.com",
            name="Test Admin",
            password="testpass123",
        )
        assert admin.email == "admin@example.com"
        assert admin.name == "Test Admin"
        assert not admin.is_2fa_enabled
        assert admin.failed_login_attempts == 0

    def test_generate_totp_secret(self):
        """Test TOTP secret generation."""
        admin = Admin.objects.create_user(
            username="admin2",
            email="admin2@example.com",
            name="Admin 2",
            password="pass",
        )
        secret = admin.generate_totp_secret()
        assert secret is not None
        assert len(secret) == 32  # pyotp default length
        assert admin.totp_secret == secret

        # Should return same secret if called again
        secret2 = admin.generate_totp_secret()
        assert secret == secret2

    def test_get_totp_uri(self):
        """Test TOTP URI generation for QR code."""
        admin = Admin.objects.create_user(
            username="admin3",
            email="admin3@example.com",
            name="Admin 3",
            password="pass",
        )
        uri = admin.get_totp_uri()
        assert "otpauth://totp/" in uri
        assert "admin3@example.com" in uri
        assert "Portfolio Site" in uri

    def test_get_qr_code(self):
        """Test QR code generation."""
        admin = Admin.objects.create_user(
            username="admin4",
            email="admin4@example.com",
            name="Admin 4",
            password="pass",
        )
        qr_code = admin.get_qr_code()
        assert qr_code is not None
        assert isinstance(qr_code, str)
        # Base64 encoded PNG should start with specific characters
        assert len(qr_code) > 100  # QR codes are typically large

    def test_verify_totp_without_2fa(self):
        """Test TOTP verification fails when 2FA not enabled."""
        admin = Admin.objects.create_user(
            username="admin5",
            email="admin5@example.com",
            name="Admin 5",
            password="pass",
        )
        admin.generate_totp_secret()
        assert not admin.verify_totp("123456")  # 2FA not enabled

    def test_verify_totp_with_2fa_enabled(self):
        """Test TOTP verification with 2FA enabled."""
        import pyotp

        admin = Admin.objects.create_user(
            username="admin6",
            email="admin6@example.com",
            name="Admin 6",
            password="pass",
        )
        admin.generate_totp_secret()
        admin.is_2fa_enabled = True
        admin.save()

        # Generate valid token
        totp = pyotp.TOTP(admin.totp_secret)
        valid_token = totp.now()

        assert admin.verify_totp(valid_token)
        assert not admin.verify_totp("000000")  # Invalid token

    def test_generate_backup_codes(self):
        """Test backup code generation."""
        admin = Admin.objects.create_user(
            username="admin7",
            email="admin7@example.com",
            name="Admin 7",
            password="pass",
        )
        codes = admin.generate_backup_codes(count=8)
        assert len(codes) == 8
        assert len(admin.backup_codes) == 8
        # Each code should be 8 characters
        for code in codes:
            assert len(code) == 8
            assert code.isalnum()

    def test_use_backup_code(self):
        """Test backup code usage (one-time use)."""
        admin = Admin.objects.create_user(
            username="admin8",
            email="admin8@example.com",
            name="Admin 8",
            password="pass",
        )
        codes = admin.generate_backup_codes(count=5)
        first_code = codes[0]

        # First use should succeed
        assert admin.use_backup_code(first_code)
        assert first_code not in admin.backup_codes
        assert len(admin.backup_codes) == 4

        # Second use should fail
        assert not admin.use_backup_code(first_code)

    def test_account_locking(self):
        """Test account locking functionality."""
        admin = Admin.objects.create_user(
            username="admin9",
            email="admin9@example.com",
            name="Admin 9",
            password="pass",
        )
        assert not admin.is_account_locked()

        admin.lock_account(duration_minutes=30)
        assert admin.is_account_locked()
        assert admin.account_locked_until is not None

    def test_account_unlock(self):
        """Test account unlocking."""
        admin = Admin.objects.create_user(
            username="admin10",
            email="admin10@example.com",
            name="Admin 10",
            password="pass",
        )
        admin.failed_login_attempts = 5
        admin.lock_account()

        admin.unlock_account()
        assert not admin.is_account_locked()
        assert admin.failed_login_attempts == 0
        assert admin.account_locked_until is None
        assert admin.last_failed_login is None

    def test_record_failed_login(self):
        """Test failed login attempt recording."""
        admin = Admin.objects.create_user(
            username="admin11",
            email="admin11@example.com",
            name="Admin 11",
            password="pass",
        )

        # Record 4 failed attempts
        for i in range(4):
            admin.record_failed_login()
            assert admin.failed_login_attempts == i + 1
            assert not admin.is_account_locked()

        # 5th attempt should lock account
        admin.record_failed_login()
        assert admin.failed_login_attempts == 5
        assert admin.is_account_locked()

    def test_record_successful_login(self):
        """Test successful login resets failed attempts."""
        admin = Admin.objects.create_user(
            username="admin12",
            email="admin12@example.com",
            name="Admin 12",
            password="pass",
        )
        admin.failed_login_attempts = 3
        admin.last_failed_login = timezone.now()
        admin.save()

        admin.record_successful_login()
        assert admin.failed_login_attempts == 0
        assert admin.last_failed_login is None


# ============================================================================
# USERSESSION MODEL TESTS (Device Detection, Session Management)
# ============================================================================


@pytest.mark.django_db
class TestUserSessionModel:
    """Test UserSession model - device detection and session management."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for session tests."""
        return Admin.objects.create_user(
            username="session_admin",
            email="session@example.com",
            name="Session Admin",
            password="pass",
        )

    def test_session_creation(self, admin_user):
        """Test basic session creation."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="test_session_key_123",
            ip_address="192.168.1.1",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0",
        )
        assert session.user == admin_user
        assert session.is_active
        assert session.session_key == "test_session_key_123"

    def test_device_detection_mobile(self, admin_user):
        """Test mobile device detection."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="mobile_session",
            ip_address="192.168.1.2",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X) Mobile Safari",
        )
        device_info = session.get_device_info()
        assert device_info["device_type"] == "Mobile"
        assert device_info["browser"] == "Safari"

    def test_device_detection_tablet(self, admin_user):
        """Test tablet device detection."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="tablet_session",
            ip_address="192.168.1.3",
            user_agent="Mozilla/5.0 (iPad; CPU OS 13_0 like Mac OS X) AppleWebKit",
        )
        device_info = session.get_device_info()
        assert device_info["device_type"] == "Tablet"

    def test_device_detection_desktop(self, admin_user):
        """Test desktop device detection."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="desktop_session",
            ip_address="192.168.1.4",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) Chrome/90.0",
        )
        device_info = session.get_device_info()
        assert device_info["device_type"] == "Desktop"
        assert device_info["browser"] == "Chrome"

    def test_browser_detection_firefox(self, admin_user):
        """Test Firefox browser detection."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="firefox_session",
            ip_address="192.168.1.5",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:88.0) Gecko/20100101 Firefox/88.0",
        )
        device_info = session.get_device_info()
        assert device_info["browser"] == "Firefox"

    def test_browser_detection_edge(self, admin_user):
        """Test Edge browser detection."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="edge_session",
            ip_address="192.168.1.6",
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 Edge/90.0",
        )
        device_info = session.get_device_info()
        assert device_info["browser"] == "Edge"

    def test_user_agent_truncation(self, admin_user):
        """Test user agent truncation in device info."""
        long_user_agent = "A" * 200
        session = UserSession.objects.create(
            user=admin_user,
            session_key="long_ua_session",
            ip_address="192.168.1.7",
            user_agent=long_user_agent,
        )
        device_info = session.get_device_info()
        assert len(device_info["user_agent"]) <= 103  # 100 + "..."

    def test_session_deactivation(self, admin_user):
        """Test session deactivation."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="deactivate_session",
            ip_address="192.168.1.8",
            user_agent="Test User Agent",
        )
        assert session.is_active

        session.deactivate()
        assert not session.is_active

    def test_session_string_representation(self, admin_user):
        """Test session __str__ method."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="str_session",
            ip_address="192.168.1.9",
            user_agent="Test",
        )
        str_repr = str(session)
        assert "session@example.com" in str_repr
        assert "192.168.1.9" in str_repr


# ============================================================================
# COOKIECONSENT MODEL TESTS (GDPR Consent Tracking)
# ============================================================================


@pytest.mark.django_db
class TestCookieConsentModel:
    """Test CookieConsent model - GDPR consent tracking."""

    def test_cookie_consent_creation(self):
        """Test basic cookie consent creation."""
        consent = CookieConsent.objects.create(
            session_key="consent_session_123",
            ip_address="192.168.1.10",
            user_agent="Mozilla/5.0",
        )
        assert consent.necessary  # Always true by default
        assert not consent.functional
        assert not consent.analytics
        assert not consent.marketing

    def test_consent_expiration_auto_set(self):
        """Test consent expiration is auto-set to 1 year."""
        consent = CookieConsent.objects.create(
            session_key="expiry_session",
            ip_address="192.168.1.11",
            user_agent="Test",
        )
        assert consent.expires_at is not None
        expected_expiry = timezone.now() + timedelta(days=365)
        # Allow 1 minute tolerance for test execution time
        assert abs((consent.expires_at - expected_expiry).total_seconds()) < 60

    def test_is_expired_false(self):
        """Test is_expired returns False for valid consent."""
        consent = CookieConsent.objects.create(
            session_key="valid_consent",
            ip_address="192.168.1.12",
            user_agent="Test",
        )
        assert not consent.is_expired()

    def test_is_expired_true(self):
        """Test is_expired returns True for expired consent."""
        consent = CookieConsent.objects.create(
            session_key="expired_consent",
            ip_address="192.168.1.13",
            user_agent="Test",
        )
        # Manually set expiration to past
        consent.expires_at = timezone.now() - timedelta(days=1)
        consent.save()
        assert consent.is_expired()

    def test_get_consent_summary(self):
        """Test consent summary generation."""
        consent = CookieConsent.objects.create(
            session_key="summary_session",
            ip_address="192.168.1.14",
            user_agent="Test",
            necessary=True,
            functional=True,
            analytics=False,
            marketing=False,
        )
        summary = consent.get_consent_summary()
        assert summary["necessary"] is True
        assert summary["functional"] is True
        assert summary["analytics"] is False
        assert summary["marketing"] is False

    def test_consent_string_representation(self):
        """Test consent __str__ method."""
        consent = CookieConsent.objects.create(
            session_key="str_consent",
            ip_address="192.168.1.15",
            user_agent="Test",
        )
        str_repr = str(consent)
        assert "str_consent" in str_repr
        assert "Cookie Consent" in str_repr


# ============================================================================
# DATAEXPORTREQUEST MODEL TESTS (GDPR Export Workflow)
# ============================================================================


@pytest.mark.django_db
class TestDataExportRequestModel:
    """Test DataExportRequest model - GDPR export workflow."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for export tests."""
        return Admin.objects.create_user(
            username="export_admin",
            email="export@example.com",
            name="Export Admin",
            password="pass",
        )

    def test_export_request_creation(self, admin_user):
        """Test basic export request creation."""
        export_req = DataExportRequest.objects.create(
            user=admin_user,
            email="export@example.com",
        )
        assert export_req.status == "pending"
        assert export_req.completed_at is None
        assert export_req.file_path == ""

    def test_export_status_choices(self, admin_user):
        """Test all export status choices."""
        for status, _ in DataExportRequest.STATUS_CHOICES:
            export_req = DataExportRequest.objects.create(
                user=admin_user,
                email="export@example.com",
                status=status,
            )
            assert export_req.status == status

    def test_export_string_representation(self, admin_user):
        """Test export request __str__ method."""
        export_req = DataExportRequest.objects.create(
            user=admin_user,
            email="export@example.com",
        )
        str_repr = str(export_req)
        assert "export@example.com" in str_repr
        assert "pending" in str_repr


# ============================================================================
# ACCOUNTDELETIONREQUEST MODEL TESTS (30-Day Grace Period)
# ============================================================================


@pytest.mark.django_db
class TestAccountDeletionRequestModel:
    """Test AccountDeletionRequest model - 30-day grace period."""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for deletion tests."""
        return Admin.objects.create_user(
            username="delete_admin",
            email="delete@example.com",
            name="Delete Admin",
            password="pass",
        )

    def test_deletion_request_creation(self, admin_user):
        """Test basic deletion request creation."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
            reason="Test reason",
        )
        assert deletion_req.status == "pending"
        assert deletion_req.confirmed_at is None

    def test_scheduled_deletion_auto_set(self, admin_user):
        """Test scheduled deletion is auto-set to 30 days."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        assert deletion_req.scheduled_deletion is not None
        expected_deletion = timezone.now() + timedelta(days=30)
        # Allow 1 minute tolerance
        assert (
            abs((deletion_req.scheduled_deletion - expected_deletion).total_seconds())
            < 60
        )

    def test_generate_confirmation_token(self, admin_user):
        """Test confirmation token generation."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        token = deletion_req.generate_confirmation_token()
        assert token is not None
        assert len(token) > 20  # URL-safe tokens are long
        assert deletion_req.confirmation_token == token

    def test_is_expired_false(self, admin_user):
        """Test is_expired returns False for valid request."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        assert not deletion_req.is_expired()

    def test_is_expired_true(self, admin_user):
        """Test is_expired returns True after 72 hours (pending only)."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        # Set request date to 73 hours ago
        deletion_req.request_date = timezone.now() - timedelta(hours=73)
        deletion_req.save()
        assert deletion_req.is_expired()

    def test_is_expired_confirmed_not_expired(self, admin_user):
        """Test is_expired returns False for confirmed requests."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
            status="confirmed",
        )
        deletion_req.request_date = timezone.now() - timedelta(hours=73)
        deletion_req.save()
        assert not deletion_req.is_expired()  # Confirmed requests don't expire

    def test_confirm_deletion(self, admin_user):
        """Test deletion confirmation."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        deletion_req.confirm_deletion()
        assert deletion_req.status == "confirmed"
        assert deletion_req.confirmed_at is not None

    def test_cancel_deletion(self, admin_user):
        """Test deletion cancellation."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        deletion_req.cancel_deletion()
        assert deletion_req.status == "cancelled"

    def test_deletion_string_representation(self, admin_user):
        """Test deletion request __str__ method."""
        deletion_req = AccountDeletionRequest.objects.create(
            user=admin_user,
            email="delete@example.com",
        )
        str_repr = str(deletion_req)
        assert "delete@example.com" in str_repr
        assert "pending" in str_repr
