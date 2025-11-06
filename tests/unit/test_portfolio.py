"""
Unit tests for Portfolio app models.

Coverage targets:
- Security & Auth: Admin (2FA, account locking), UserSession (device detection)
- GDPR: CookieConsent, DataExportRequest, AccountDeletionRequest
- Content: PersonalInfo, SocialLink, AITool, CybersecurityResource
- Monitoring: PerformanceMetric, ErrorLog, AnalyticsEvent
- Utilities: ShortURL, NotificationLog, WebPushSubscription
"""

from datetime import timedelta

from django.contrib.auth import get_user_model
from django.core.exceptions import ValidationError
from django.utils import timezone

import pytest

from apps.portfolio.models import (
    AccountDeletionRequest,
    Admin,
    AITool,
    AnalyticsEvent,
    CookieConsent,
    CybersecurityResource,
    DataExportRequest,
    ErrorLog,
    NotificationLog,
    PerformanceMetric,
    PersonalInfo,
    ShortURL,
    SocialLink,
    UserSession,
    WebPushSubscription,
)

User = get_user_model()


# ============================================================================
# FIXTURES
# ============================================================================


@pytest.fixture
def admin_user(db):
    """Create a test admin user."""
    return Admin.objects.create_user(
        username="testadmin",
        email="admin@test.com",
        password="testpass123",
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture
def admin_with_2fa(admin_user):
    """Create admin with 2FA enabled."""
    admin_user.generate_totp_secret()
    admin_user.is_2fa_enabled = True
    admin_user.save()
    return admin_user


@pytest.fixture
def user_session(db, admin_user):
    """Create a test user session."""
    return UserSession.objects.create(
        user=admin_user,
        session_key="test_session_key_123",
        ip_address="192.168.1.1",
        user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
        location="Test Location",
        is_active=True,
    )


# ============================================================================
# PHASE 1: SECURITY & AUTH TESTS (Admin, UserSession)
# ============================================================================


class TestAdminModel:
    """Test Admin model with 2FA and account locking features."""

    def test_admin_creation(self, db):
        """Test basic admin user creation."""
        admin = Admin.objects.create_user(
            username="admin1",
            email="admin1@test.com",
            password="pass123",
        )
        assert admin.username == "admin1"
        assert admin.email == "admin1@test.com"
        assert admin.check_password("pass123")
        assert admin.failed_login_attempts == 0
        assert not admin.is_2fa_enabled

    def test_admin_string_representation(self, admin_user):
        """Test admin __str__ method."""
        assert str(admin_user) == "testadmin"

    def test_email_uniqueness(self, db):
        """Test email must be unique."""
        Admin.objects.create_user(username="user1", email="test@test.com")
        with pytest.raises(Exception):  # IntegrityError
            Admin.objects.create_user(username="user2", email="test@test.com")

    # 2FA Tests
    def test_generate_totp_secret(self, admin_user):
        """Test TOTP secret generation."""
        secret = admin_user.generate_totp_secret()
        assert secret is not None
        assert len(secret) == 32  # Base32 secret length
        assert admin_user.totp_secret == secret

    def test_get_totp_uri(self, admin_with_2fa):
        """Test TOTP URI generation for QR code."""
        uri = admin_with_2fa.get_totp_uri()
        assert uri.startswith("otpauth://totp/")
        assert "testadmin" in uri
        assert admin_with_2fa.totp_secret in uri

    def test_get_qr_code(self, admin_with_2fa):
        """Test QR code generation."""
        qr_code = admin_with_2fa.get_qr_code()
        assert qr_code.startswith("data:image/png;base64,")
        assert len(qr_code) > 100  # Base64 image should be substantial

    def test_verify_totp_valid(self, admin_with_2fa):
        """Test TOTP verification with valid token."""
        import pyotp

        totp = pyotp.TOTP(admin_with_2fa.totp_secret)
        valid_token = totp.now()
        assert admin_with_2fa.verify_totp(valid_token) is True

    def test_verify_totp_invalid(self, admin_with_2fa):
        """Test TOTP verification with invalid token."""
        assert admin_with_2fa.verify_totp("000000") is False

    def test_verify_totp_disabled(self, admin_user):
        """Test TOTP verification when 2FA is disabled."""
        admin_user.generate_totp_secret()
        admin_user.is_2fa_enabled = False
        admin_user.save()
        assert admin_user.verify_totp("123456") is False

    # Backup Codes Tests
    def test_generate_backup_codes(self, admin_user):
        """Test backup code generation."""
        codes = admin_user.generate_backup_codes(count=8)
        assert len(codes) == 8
        assert all(len(code) == 8 for code in codes)
        assert admin_user.backup_codes == codes

    def test_use_backup_code_success(self, admin_user):
        """Test using a valid backup code."""
        codes = admin_user.generate_backup_codes(count=3)
        test_code = codes[1]
        assert admin_user.use_backup_code(test_code) is True
        assert test_code not in admin_user.backup_codes

    def test_use_backup_code_already_used(self, admin_user):
        """Test using an already used backup code."""
        codes = admin_user.generate_backup_codes(count=3)
        test_code = codes[0]
        admin_user.use_backup_code(test_code)
        assert admin_user.use_backup_code(test_code) is False

    def test_use_backup_code_invalid(self, admin_user):
        """Test using an invalid backup code."""
        admin_user.generate_backup_codes(count=3)
        assert admin_user.use_backup_code("INVALID1") is False

    # Account Locking Tests
    def test_record_failed_login_increments(self, admin_user):
        """Test failed login attempt increments counter."""
        initial_count = admin_user.failed_login_attempts
        admin_user.record_failed_login()
        assert admin_user.failed_login_attempts == initial_count + 1
        assert admin_user.last_failed_login is not None

    def test_record_failed_login_locks_at_threshold(self, admin_user):
        """Test account locks after 5 failed attempts."""
        for _ in range(4):
            admin_user.record_failed_login()
        assert not admin_user.is_account_locked()

        admin_user.record_failed_login()  # 5th attempt
        assert admin_user.is_account_locked()
        assert admin_user.account_locked_until is not None

    def test_is_account_locked_expired(self, admin_user):
        """Test account lock expires after duration."""
        admin_user.lock_account(duration_minutes=30)
        assert admin_user.is_account_locked()

        # Simulate time passing (mock expired lock)
        admin_user.account_locked_until = timezone.now() - timedelta(minutes=1)
        admin_user.save()
        assert not admin_user.is_account_locked()

    def test_unlock_account(self, admin_user):
        """Test manual account unlock."""
        admin_user.failed_login_attempts = 5
        admin_user.lock_account()
        assert admin_user.is_account_locked()

        admin_user.unlock_account()
        assert admin_user.failed_login_attempts == 0
        assert admin_user.account_locked_until is None
        assert not admin_user.is_account_locked()

    def test_record_successful_login_resets_counter(self, admin_user):
        """Test successful login resets failed attempt counter."""
        admin_user.failed_login_attempts = 3
        admin_user.record_successful_login()
        assert admin_user.failed_login_attempts == 0
        assert admin_user.last_login is not None


class TestUserSession:
    """Test UserSession model for device tracking."""

    def test_session_creation(self, user_session):
        """Test basic session creation."""
        assert user_session.session_key == "test_session_key_123"
        assert user_session.ip_address == "192.168.1.1"
        assert user_session.is_active is True

    def test_get_device_info_mobile(self, db, admin_user):
        """Test device detection for mobile user agent."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="mobile_session",
            ip_address="10.0.0.1",
            user_agent="Mozilla/5.0 (iPhone; CPU iPhone OS 14_0 like Mac OS X)",
        )
        device_info = session.get_device_info()
        assert device_info["device_type"] == "Mobile"
        assert "Safari" in device_info["browser"] or "iPhone" in device_info["browser"]

    def test_get_device_info_tablet(self, db, admin_user):
        """Test device detection for tablet user agent."""
        session = UserSession.objects.create(
            user=admin_user,
            session_key="tablet_session",
            ip_address="10.0.0.2",
            user_agent="Mozilla/5.0 (iPad; CPU OS 13_0 like Mac OS X)",
        )
        device_info = session.get_device_info()
        assert device_info["device_type"] == "Tablet"

    def test_get_device_info_desktop(self, user_session):
        """Test device detection for desktop user agent."""
        device_info = user_session.get_device_info()
        assert device_info["device_type"] == "Desktop"
        assert "Chrome" in device_info["browser"]

    def test_deactivate_session(self, user_session):
        """Test session deactivation."""
        assert user_session.is_active is True
        user_session.deactivate()
        assert user_session.is_active is False

    def test_session_string_representation(self, user_session):
        """Test session __str__ method."""
        str_repr = str(user_session)
        assert "testadmin" in str_repr
        assert "192.168.1.1" in str_repr


# ============================================================================
# PHASE 2: GDPR COMPLIANCE TESTS
# ============================================================================


class TestCookieConsent:
    """Test CookieConsent model for GDPR compliance."""

    def test_cookie_consent_creation(self, db, admin_user):
        """Test cookie consent record creation."""
        consent = CookieConsent.objects.create(
            user=admin_user,
            necessary=True,
            functional=True,
            analytics=False,
            marketing=False,
        )
        assert consent.necessary is True  # Always true
        assert consent.functional is True
        assert consent.analytics is False
        assert consent.marketing is False

    def test_cookie_consent_auto_expiration(self, db, admin_user):
        """Test consent expires after 365 days."""
        consent = CookieConsent.objects.create(user=admin_user)
        expected_expiry = timezone.now() + timedelta(days=365)
        # Allow 1 minute tolerance for test execution time
        assert abs((consent.expires_at - expected_expiry).total_seconds()) < 60

    def test_is_expired_false(self, db, admin_user):
        """Test consent is not expired when valid."""
        consent = CookieConsent.objects.create(user=admin_user)
        assert consent.is_expired() is False

    def test_is_expired_true(self, db, admin_user):
        """Test consent is expired after expiry date."""
        consent = CookieConsent.objects.create(user=admin_user)
        consent.expires_at = timezone.now() - timedelta(days=1)
        consent.save()
        assert consent.is_expired() is True

    def test_get_consent_summary(self, db, admin_user):
        """Test consent summary dictionary."""
        consent = CookieConsent.objects.create(
            user=admin_user,
            functional=True,
            analytics=True,
            marketing=False,
        )
        summary = consent.get_consent_summary()
        assert summary["necessary"] is True
        assert summary["functional"] is True
        assert summary["analytics"] is True
        assert summary["marketing"] is False


class TestDataExportRequest:
    """Test DataExportRequest model for GDPR data export."""

    def test_export_request_creation(self, db, admin_user):
        """Test data export request creation."""
        request = DataExportRequest.objects.create(
            user=admin_user,
            status="pending",
        )
        assert request.status == "pending"
        assert request.file_path is None
        assert request.completed_at is None

    def test_export_request_workflow_complete(self, db, admin_user):
        """Test export request workflow to completion."""
        request = DataExportRequest.objects.create(user=admin_user, status="pending")

        request.status = "processing"
        request.save()
        assert request.status == "processing"

        request.status = "completed"
        request.file_path = "/exports/user_123.zip"
        request.completed_at = timezone.now()
        request.save()
        assert request.status == "completed"
        assert request.file_path is not None

    def test_export_request_workflow_failed(self, db, admin_user):
        """Test export request failure handling."""
        request = DataExportRequest.objects.create(user=admin_user, status="processing")
        request.status = "failed"
        request.error_message = "Database connection error"
        request.save()

        assert request.status == "failed"
        assert "error" in request.error_message.lower()

    def test_export_request_string_representation(self, db, admin_user):
        """Test export request __str__ method."""
        request = DataExportRequest.objects.create(user=admin_user)
        str_repr = str(request)
        assert "testadmin" in str_repr
        assert "pending" in str_repr.lower()


class TestAccountDeletionRequest:
    """Test AccountDeletionRequest model for GDPR account deletion."""

    def test_deletion_request_creation(self, db, admin_user):
        """Test account deletion request creation."""
        request = AccountDeletionRequest.objects.create(
            user=admin_user,
            reason="No longer needed",
        )
        assert request.status == "pending"
        assert request.reason == "No longer needed"
        assert request.scheduled_deletion is not None

    def test_scheduled_deletion_30_days(self, db, admin_user):
        """Test deletion is scheduled 30 days from request."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        expected_deletion = timezone.now() + timedelta(days=30)
        # Allow 1 minute tolerance
        assert (
            abs((request.scheduled_deletion - expected_deletion).total_seconds()) < 60
        )

    def test_generate_confirmation_token(self, db, admin_user):
        """Test confirmation token generation."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        token = request.generate_confirmation_token()
        assert len(token) > 20  # URL-safe token
        assert request.confirmation_token == token

    def test_is_expired_within_window(self, db, admin_user):
        """Test confirmation not expired within 72-hour window."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        request.generate_confirmation_token()
        assert request.is_expired() is False

    def test_is_expired_after_window(self, db, admin_user):
        """Test confirmation expired after 72 hours."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        request.generate_confirmation_token()
        request.requested_at = timezone.now() - timedelta(hours=73)
        request.save()
        assert request.is_expired() is True

    def test_confirm_deletion(self, db, admin_user):
        """Test deletion confirmation."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        request.generate_confirmation_token()
        request.confirm_deletion()

        assert request.status == "confirmed"
        assert request.confirmed_at is not None

    def test_cancel_deletion(self, db, admin_user):
        """Test deletion cancellation."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        request.cancel_deletion()

        assert request.status == "cancelled"

    def test_deletion_request_string_representation(self, db, admin_user):
        """Test deletion request __str__ method."""
        request = AccountDeletionRequest.objects.create(user=admin_user)
        str_repr = str(request)
        assert "testadmin" in str_repr


# ============================================================================
# PHASE 3: CONTENT MANAGEMENT TESTS
# ============================================================================


class TestPersonalInfo:
    """Test PersonalInfo model for key-value content storage."""

    def test_personal_info_creation_text(self, db):
        """Test creating text-type personal info."""
        info = PersonalInfo.objects.create(
            key="bio",
            type="text",
            value="Software developer with 10 years experience",
            order=1,
        )
        assert info.key == "bio"
        assert info.type == "text"
        assert info.is_visible is True

    def test_personal_info_json_valid(self, db):
        """Test creating JSON-type personal info with valid JSON."""
        import json

        json_data = json.dumps({"skills": ["Python", "Django", "React"]})
        info = PersonalInfo.objects.create(
            key="skills",
            type="json",
            value=json_data,
        )
        parsed = json.loads(info.value)
        assert "Python" in parsed["skills"]

    def test_personal_info_json_validation(self, db):
        """Test JSON validation in clean() method."""
        info = PersonalInfo(
            key="invalid_json",
            type="json",
            value="{invalid json}",
        )
        with pytest.raises(ValidationError):
            info.clean()

    def test_personal_info_ordering(self, db):
        """Test ordering by order field."""
        PersonalInfo.objects.create(key="second", value="B", order=2)
        PersonalInfo.objects.create(key="first", value="A", order=1)
        PersonalInfo.objects.create(key="third", value="C", order=3)

        ordered = list(PersonalInfo.objects.order_by("order"))
        assert ordered[0].key == "first"
        assert ordered[1].key == "second"
        assert ordered[2].key == "third"

    def test_personal_info_visibility_filter(self, db):
        """Test filtering by is_visible flag."""
        PersonalInfo.objects.create(key="visible", value="A", is_visible=True)
        PersonalInfo.objects.create(key="hidden", value="B", is_visible=False)

        visible = PersonalInfo.objects.filter(is_visible=True)
        assert visible.count() == 1
        assert visible.first().key == "visible"


class TestSocialLink:
    """Test SocialLink model with platform-specific validation."""

    def test_social_link_creation(self, db, admin_user):
        """Test basic social link creation."""
        link = SocialLink.objects.create(
            user=admin_user,
            platform="github",
            url="https://github.com/testuser",
            order=1,
        )
        assert link.platform == "github"
        assert link.is_visible is True

    def test_email_platform_validation(self, db, admin_user):
        """Test email platform adds mailto: prefix."""
        link = SocialLink(
            user=admin_user,
            platform="email",
            url="test@example.com",
        )
        link.clean()
        assert link.url.startswith("mailto:")
        assert "test@example.com" in link.url

    def test_email_already_has_mailto(self, db, admin_user):
        """Test email with existing mailto: prefix."""
        link = SocialLink(
            user=admin_user,
            platform="email",
            url="mailto:test@example.com",
        )
        link.clean()
        # Should not add another mailto:
        assert link.url.count("mailto:") == 1

    def test_github_url_validation_valid(self, db, admin_user):
        """Test GitHub URL validation passes for valid URL."""
        link = SocialLink(
            user=admin_user,
            platform="github",
            url="https://github.com/testuser",
        )
        link.clean()  # Should not raise

    def test_github_url_validation_invalid(self, db, admin_user):
        """Test GitHub URL validation fails for non-GitHub URL."""
        link = SocialLink(
            user=admin_user,
            platform="github",
            url="https://gitlab.com/testuser",
        )
        with pytest.raises(ValidationError) as exc_info:
            link.clean()
        assert "github.com" in str(exc_info.value).lower()

    def test_linkedin_url_validation_valid(self, db, admin_user):
        """Test LinkedIn URL validation passes."""
        link = SocialLink(
            user=admin_user,
            platform="linkedin",
            url="https://linkedin.com/in/testuser",
        )
        link.clean()  # Should not raise

    def test_linkedin_url_validation_invalid(self, db, admin_user):
        """Test LinkedIn URL validation fails."""
        link = SocialLink(
            user=admin_user,
            platform="linkedin",
            url="https://facebook.com/testuser",
        )
        with pytest.raises(ValidationError) as exc_info:
            link.clean()
        assert "linkedin.com" in str(exc_info.value).lower()

    def test_twitter_url_validation_twitter_com(self, db, admin_user):
        """Test Twitter URL validation with twitter.com."""
        link = SocialLink(
            user=admin_user,
            platform="twitter",
            url="https://twitter.com/testuser",
        )
        link.clean()  # Should not raise

    def test_twitter_url_validation_x_com(self, db, admin_user):
        """Test Twitter URL validation with x.com."""
        link = SocialLink(
            user=admin_user,
            platform="twitter",
            url="https://x.com/testuser",
        )
        link.clean()  # Should not raise

    def test_twitter_url_validation_invalid(self, db, admin_user):
        """Test Twitter URL validation fails for other domains."""
        link = SocialLink(
            user=admin_user,
            platform="twitter",
            url="https://instagram.com/testuser",
        )
        with pytest.raises(ValidationError) as exc_info:
            link.clean()
        assert (
            "twitter.com" in str(exc_info.value).lower()
            or "x.com" in str(exc_info.value).lower()
        )

    def test_primary_link_enforcement(self, db, admin_user):
        """Test only one link can be primary."""
        link1 = SocialLink.objects.create(
            user=admin_user,
            platform="github",
            url="https://github.com/user1",
            is_primary=True,
        )
        link2 = SocialLink.objects.create(
            user=admin_user,
            platform="linkedin",
            url="https://linkedin.com/in/user1",
            is_primary=True,
        )

        # Re-fetch link1 to check if it was updated
        link1.refresh_from_db()
        # Only one should remain primary (the latest one)
        primary_count = SocialLink.objects.filter(
            user=admin_user, is_primary=True
        ).count()
        assert primary_count == 1


class TestAITool:
    """Test AITool model for AI tool directory."""

    def test_ai_tool_creation(self, db):
        """Test basic AI tool creation."""
        tool = AITool.objects.create(
            name="GPT-4",
            description="Advanced language model",
            url="https://openai.com/gpt-4",
            category="general",
            rating=5,
            is_free=False,
        )
        assert tool.name == "GPT-4"
        assert tool.category == "general"
        assert tool.rating == 5

    def test_ai_tool_categories(self, db):
        """Test different AI tool categories."""
        categories = ["general", "visual", "video", "audio", "text", "code"]
        for cat in categories:
            tool = AITool.objects.create(
                name=f"Tool {cat}",
                category=cat,
                url="https://example.com",
            )
            assert tool.category == cat

    def test_ai_tool_featured_flag(self, db):
        """Test featured AI tool filtering."""
        AITool.objects.create(name="Featured", url="https://ex.com", is_featured=True)
        AITool.objects.create(name="Normal", url="https://ex2.com", is_featured=False)

        featured = AITool.objects.filter(is_featured=True)
        assert featured.count() == 1
        assert featured.first().name == "Featured"


class TestCybersecurityResource:
    """Test CybersecurityResource model."""

    def test_cybersecurity_resource_creation(self, db):
        """Test basic cybersecurity resource creation."""
        resource = CybersecurityResource.objects.create(
            title="OWASP Top 10",
            description="Top 10 web application security risks",
            url="https://owasp.org/top10",
            type="standard",
            difficulty="intermediate",
            severity_level=3,  # High
        )
        assert resource.title == "OWASP Top 10"
        assert resource.type == "standard"
        assert resource.severity_level == 3

    def test_resource_types(self, db):
        """Test different resource types."""
        types = ["tool", "threat", "standard", "practice", "tutorial"]
        for res_type in types:
            resource = CybersecurityResource.objects.create(
                title=f"Resource {res_type}",
                url="https://example.com",
                type=res_type,
            )
            assert resource.type == res_type

    def test_difficulty_levels(self, db):
        """Test difficulty level choices."""
        levels = ["beginner", "intermediate", "advanced", "expert"]
        for level in levels:
            resource = CybersecurityResource.objects.create(
                title=f"Tutorial {level}",
                url="https://example.com",
                difficulty=level,
            )
            assert resource.difficulty == level

    def test_urgent_flag_filtering(self, db):
        """Test filtering urgent security resources."""
        CybersecurityResource.objects.create(
            title="Critical CVE",
            url="https://ex.com",
            is_urgent=True,
            severity_level=4,
        )
        CybersecurityResource.objects.create(
            title="General Info",
            url="https://ex2.com",
            is_urgent=False,
        )

        urgent = CybersecurityResource.objects.filter(is_urgent=True)
        assert urgent.count() == 1
        assert urgent.first().title == "Critical CVE"


# ============================================================================
# PHASE 4: MONITORING & ANALYTICS TESTS
# ============================================================================


class TestPerformanceMetric:
    """Test PerformanceMetric model for Core Web Vitals tracking."""

    def test_performance_metric_creation(self, db):
        """Test basic performance metric creation."""
        metric = PerformanceMetric.objects.create(
            url="/",
            metric_type="lcp",
            value=1800.0,  # 1.8 seconds
            device_type="mobile",
        )
        assert metric.metric_type == "lcp"
        assert metric.value == 1800.0

    def test_lcp_good_score(self, db):
        """Test LCP good score (≤2.5s)."""
        metric = PerformanceMetric.objects.create(
            url="/",
            metric_type="lcp",
            value=2000.0,  # 2.0 seconds
        )
        assert metric.is_good_score is True

    def test_lcp_poor_score(self, db):
        """Test LCP poor score (>2.5s)."""
        metric = PerformanceMetric.objects.create(
            url="/",
            metric_type="lcp",
            value=3000.0,  # 3.0 seconds
        )
        assert metric.is_good_score is False

    def test_fid_good_score(self, db):
        """Test FID good score (≤100ms)."""
        metric = PerformanceMetric.objects.create(
            url="/",
            metric_type="fid",
            value=80.0,  # 80ms
        )
        assert metric.is_good_score is True

    def test_cls_good_score(self, db):
        """Test CLS good score (≤0.1)."""
        metric = PerformanceMetric.objects.create(
            url="/",
            metric_type="cls",
            value=0.05,
        )
        assert metric.is_good_score is True

    def test_device_context(self, db):
        """Test different device types."""
        devices = ["mobile", "desktop", "tablet"]
        for device in devices:
            metric = PerformanceMetric.objects.create(
                url="/",
                metric_type="lcp",
                value=2000.0,
                device_type=device,
            )
            assert metric.device_type == device


class TestErrorLog:
    """Test ErrorLog model for error tracking."""

    def test_error_log_creation(self, db):
        """Test basic error log creation."""
        error = ErrorLog.objects.create(
            level="error",
            error_type="javascript",
            message="Uncaught TypeError: Cannot read property 'x'",
            url="/dashboard",
            user_agent="Mozilla/5.0...",
        )
        assert error.level == "error"
        assert error.occurrence_count == 1
        assert error.is_resolved is False

    def test_mark_resolved(self, db):
        """Test marking error as resolved."""
        error = ErrorLog.objects.create(
            level="error",
            error_type="python",
            message="Division by zero",
        )
        error.mark_resolved(notes="Fixed in commit abc123")

        assert error.is_resolved is True
        assert error.resolved_at is not None
        assert "abc123" in error.resolution_notes

    def test_increment_occurrence(self, db):
        """Test incrementing error occurrence count."""
        error = ErrorLog.objects.create(
            level="warning",
            error_type="validation",
            message="Invalid input",
        )
        initial_count = error.occurrence_count
        initial_time = error.last_occurred

        error.increment_occurrence()

        assert error.occurrence_count == initial_count + 1
        assert error.last_occurred > initial_time

    def test_error_levels(self, db):
        """Test different error levels."""
        levels = ["debug", "info", "warning", "error", "critical"]
        for level in levels:
            error = ErrorLog.objects.create(
                level=level,
                error_type="system",
                message=f"Test {level} message",
            )
            assert error.level == level


class TestAnalyticsEvent:
    """Test AnalyticsEvent model for privacy-compliant tracking."""

    def test_analytics_event_creation(self, db):
        """Test basic analytics event creation."""
        event = AnalyticsEvent.objects.create(
            event_type="page_view",
            page_path="/about",
            anonymous_id="anon_123",
            gdpr_consent=True,
        )
        assert event.event_type == "page_view"
        assert event.gdpr_consent is True

    def test_event_auto_expiration(self, db):
        """Test event expires after 90 days (GDPR)."""
        event = AnalyticsEvent.objects.create(
            event_type="page_view",
            page_path="/",
            gdpr_consent=True,
        )
        expected_expiry = timezone.now() + timedelta(days=90)
        # Allow 1 minute tolerance
        assert abs((event.expires_at - expected_expiry).total_seconds()) < 60

    def test_cleanup_expired_events(self, db):
        """Test cleanup_expired() class method."""
        # Create expired event
        expired = AnalyticsEvent.objects.create(
            event_type="page_view",
            page_path="/",
            gdpr_consent=True,
        )
        expired.expires_at = timezone.now() - timedelta(days=1)
        expired.save()

        # Create valid event
        AnalyticsEvent.objects.create(
            event_type="page_view",
            page_path="/",
            gdpr_consent=True,
        )

        deleted_count = AnalyticsEvent.cleanup_expired()
        assert deleted_count == 1
        assert AnalyticsEvent.objects.count() == 1


# ============================================================================
# PHASE 5: NOTIFICATION & UTILITY TESTS
# ============================================================================


class TestWebPushSubscription:
    """Test WebPushSubscription model for push notifications."""

    def test_subscription_creation(self, db, admin_user):
        """Test basic subscription creation."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://fcm.googleapis.com/fcm/send/abc123",
            p256dh="public_key_base64",
            auth="auth_secret_base64",
        )
        assert sub.endpoint.startswith("https://")
        assert sub.is_active is True

    def test_record_delivery_success(self, db, admin_user):
        """Test recording successful delivery."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        initial_delivered = sub.total_delivered

        sub.record_delivery_success()

        assert sub.total_delivered == initial_delivered + 1
        assert sub.last_success_at is not None

    def test_record_delivery_failure(self, db, admin_user):
        """Test recording failed delivery."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        initial_failed = sub.total_failed

        sub.record_delivery_failure(reason="Endpoint expired")

        assert sub.total_failed == initial_failed + 1
        assert sub.last_failure_at is not None
        assert "expired" in sub.last_failure_reason.lower()

    def test_is_active_property(self, db, admin_user):
        """Test is_active property checks recent success."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
            enabled=True,
        )
        sub.record_delivery_success()
        # Should be active with recent success
        assert sub.is_active is True


class TestNotificationLog:
    """Test NotificationLog model."""

    def test_notification_log_creation(self, db, admin_user):
        """Test basic notification log creation."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        log = NotificationLog.objects.create(
            subscription=sub,
            notification_type="blog_post",
            title="New Post Published",
            body="Check out our latest article!",
            status="pending",
        )
        assert log.notification_type == "blog_post"
        assert log.status == "pending"

    def test_notification_status_workflow(self, db, admin_user):
        """Test notification status transitions."""
        sub = WebPushSubscription.objects.create(
            user=admin_user,
            endpoint="https://example.com/push",
            p256dh="key",
            auth="auth",
        )
        log = NotificationLog.objects.create(
            subscription=sub,
            notification_type="alert",
            title="Test",
            body="Test body",
            status="pending",
        )

        log.status = "sent"
        log.save()
        assert log.status == "sent"

        log.status = "delivered"
        log.save()
        assert log.status == "delivered"


class TestShortURL:
    """Test ShortURL model for URL shortening."""

    def test_short_url_auto_code_generation(self, db):
        """Test auto-generated 6-char short code."""
        short = ShortURL.objects.create(
            original_url="https://example.com/very/long/url/path",
        )
        assert len(short.short_code) == 6
        assert short.short_code.isalnum()

    def test_short_url_custom_code(self, db):
        """Test custom short code."""
        short = ShortURL.objects.create(
            original_url="https://example.com",
            short_code="custom",
        )
        assert short.short_code == "custom"

    def test_increment_click(self, db):
        """Test click tracking."""
        short = ShortURL.objects.create(
            original_url="https://example.com",
        )
        initial_clicks = short.click_count

        short.increment_click()

        assert short.click_count == initial_clicks + 1
        assert short.last_clicked_at is not None

    def test_is_expired_false(self, db):
        """Test URL is not expired when no expiration set."""
        short = ShortURL.objects.create(
            original_url="https://example.com",
        )
        assert short.is_expired is False

    def test_is_expired_true(self, db):
        """Test URL is expired after expiration date."""
        short = ShortURL.objects.create(
            original_url="https://example.com",
            expires_at=timezone.now() - timedelta(days=1),
        )
        assert short.is_expired is True

    def test_get_short_url(self, db):
        """Test building full short URL."""
        short = ShortURL.objects.create(
            original_url="https://example.com/long/path",
        )
        full_url = short.get_short_url()
        assert "/s/" in full_url
        assert short.short_code in full_url
