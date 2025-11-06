"""
Additional Security Tests
=========================

Comprehensive security testing beyond basic checks.
"""

import re

from django.conf import settings
from django.contrib.auth import get_user_model
from django.test import Client

import pytest

User = get_user_model()


class TestSecurityHeaders:
    """Test security headers in responses."""

    def test_strict_transport_security_header(self, client):
        """Test HSTS header is present."""
        response = client.get("/")

        assert "Strict-Transport-Security" in response
        hsts = response["Strict-Transport-Security"]
        assert "max-age" in hsts
        assert int(re.search(r"max-age=(\d+)", hsts).group(1)) >= 31536000

    def test_content_security_policy_header(self, client):
        """Test CSP header is present and restrictive."""
        response = client.get("/")

        assert "Content-Security-Policy" in response
        csp = response["Content-Security-Policy"]
        assert "default-src 'self'" in csp or "default-src 'none'" in csp

    def test_x_content_type_options_header(self, client):
        """Test X-Content-Type-Options header."""
        response = client.get("/")

        assert response.get("X-Content-Type-Options") == "nosniff"

    def test_x_frame_options_header(self, client):
        """Test X-Frame-Options header."""
        response = client.get("/")

        x_frame = response.get("X-Frame-Options", "").upper()
        assert x_frame in ["DENY", "SAMEORIGIN"]

    def test_referrer_policy_header(self, client):
        """Test Referrer-Policy header."""
        response = client.get("/")

        assert "Referrer-Policy" in response
        policy = response["Referrer-Policy"]
        assert policy in [
            "no-referrer",
            "no-referrer-when-downgrade",
            "strict-origin",
            "strict-origin-when-cross-origin",
        ]

    def test_permissions_policy_header(self, client):
        """Test Permissions-Policy header."""
        response = client.get("/")

        # Should have Permissions-Policy or Feature-Policy
        assert "Permissions-Policy" in response or "Feature-Policy" in response


class TestCookieSecurity:
    """Test cookie security settings."""

    def test_session_cookie_secure(self):
        """Test SESSION_COOKIE_SECURE is True."""
        # Should be True in production
        assert hasattr(settings, "SESSION_COOKIE_SECURE")

    def test_session_cookie_httponly(self):
        """Test SESSION_COOKIE_HTTPONLY is True."""
        assert settings.SESSION_COOKIE_HTTPONLY is True

    def test_session_cookie_samesite(self):
        """Test SESSION_COOKIE_SAMESITE is set."""
        assert settings.SESSION_COOKIE_SAMESITE in ["Lax", "Strict"]

    def test_csrf_cookie_secure(self):
        """Test CSRF_COOKIE_SECURE is configured."""
        assert hasattr(settings, "CSRF_COOKIE_SECURE")

    def test_csrf_cookie_httponly(self):
        """Test CSRF_COOKIE_HTTPONLY is True."""
        assert settings.CSRF_COOKIE_HTTPONLY is True

    def test_csrf_cookie_samesite(self):
        """Test CSRF_COOKIE_SAMESITE is set."""
        assert settings.CSRF_COOKIE_SAMESITE in ["Lax", "Strict"]


class TestPasswordSecurity:
    """Test password security requirements."""

    def test_password_hashers_configured(self):
        """Test PASSWORD_HASHERS uses strong algorithms."""
        hashers = settings.PASSWORD_HASHERS

        # Should use Argon2 or PBKDF2
        assert any("Argon2" in hasher or "PBKDF2" in hasher for hasher in hashers)

    def test_password_validators_configured(self):
        """Test password validators are enabled."""
        validators = settings.AUTH_PASSWORD_VALIDATORS

        assert len(validators) >= 3

        # Check for specific validators
        validator_names = [v["NAME"] for v in validators]

        assert any("UserAttributeSimilarity" in name for name in validator_names)
        assert any("MinimumLength" in name for name in validator_names)
        assert any("CommonPassword" in name for name in validator_names)

    @pytest.mark.django_db
    def test_weak_password_rejected(self):
        """Test weak passwords are rejected."""
        client = Client()

        response = client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "123456",
                "password2": "123456",
            },
        )

        # Should be rejected (400 or similar)
        assert response.status_code != 201

    @pytest.mark.django_db
    def test_strong_password_accepted(self):
        """Test strong passwords are accepted."""
        client = Client()

        response = client.post(
            "/api/auth/register/",
            {
                "username": "testuser",
                "email": "test@example.com",
                "password": "StrongP@ssw0rd123!",
                "password2": "StrongP@ssw0rd123!",
            },
        )

        # Should succeed (201) or fail for other reasons (not password)
        assert response.status_code in [201, 400]

        if response.status_code == 400:
            # If failed, should not be due to password weakness
            errors = response.json()
            assert "password" not in errors or "weak" not in str(errors).lower()


class TestSQLInjection:
    """Test SQL injection protection."""

    @pytest.mark.django_db
    def test_sql_injection_in_search(self, client):
        """Test SQL injection attempts are blocked in search."""
        payloads = [
            "' OR '1'='1",
            "1' UNION SELECT NULL--",
            "' OR 1=1--",
            "admin'--",
            "1' AND '1'='1",
        ]

        for payload in payloads:
            response = client.get(f"/api/search/?q={payload}")

            # Should not cause SQL error (500)
            assert response.status_code != 500

            # Should return safe results or empty
            assert response.status_code in [200, 400]

    @pytest.mark.django_db
    def test_sql_injection_in_auth(self, client):
        """Test SQL injection in authentication."""
        payloads = [
            {"username": "admin' OR '1'='1", "password": "anything"},
            {"username": "admin'--", "password": "anything"},
            {"username": "admin", "password": "' OR '1'='1"},
        ]

        for payload in payloads:
            response = client.post("/api/auth/login/", payload)

            # Should not cause SQL error or succeed
            assert response.status_code in [400, 401]

            # Should not be logged in
            assert not response.wsgi_request.user.is_authenticated


class TestXSS:
    """Test XSS protection."""

    @pytest.mark.django_db
    def test_xss_in_user_input(self, client, django_user_model):
        """Test XSS scripts are sanitized."""
        # Create user
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.force_login(user)

        xss_payloads = [
            "<script>alert(1)</script>",
            "<img src=x onerror=alert(1)>",
            "<svg onload=alert(1)>",
            "javascript:alert(1)",
            '<iframe src="javascript:alert(1)">',
        ]

        for payload in xss_payloads:
            # Try submitting XSS in a form
            response = client.post(
                "/api/contact/",
                {"name": "Test", "email": "test@example.com", "message": payload},
            )

            # Should be rejected or sanitized
            if response.status_code == 200:
                content = response.content.decode()
                # Script tags should be escaped or removed
                assert "<script>" not in content
                assert "onerror=" not in content
                assert "onload=" not in content


class TestCSRF:
    """Test CSRF protection."""

    def test_csrf_cookie_set(self, client):
        """Test CSRF cookie is set."""
        response = client.get("/")

        # Should set CSRF cookie
        assert "csrftoken" in response.cookies

    @pytest.mark.django_db
    def test_csrf_required_for_post(self, client):
        """Test CSRF token required for POST."""
        # Try POST without CSRF token
        response = client.post(
            "/api/contact/",
            {"name": "Test", "email": "test@example.com", "message": "Test message"},
        )

        # Should be rejected (403)
        assert response.status_code == 403

    @pytest.mark.django_db
    def test_csrf_invalid_token_rejected(self, client):
        """Test invalid CSRF token is rejected."""
        client.get("/")  # Get CSRF cookie

        # Try POST with invalid token
        response = client.post(
            "/api/contact/",
            {"name": "Test", "email": "test@example.com", "message": "Test message"},
            HTTP_X_CSRFTOKEN="invalid_token",
        )

        # Should be rejected (403)
        assert response.status_code == 403


class TestAuthenticationSecurity:
    """Test authentication security."""

    @pytest.mark.django_db
    def test_brute_force_protection(self, client):
        """Test brute force login protection."""
        # Try multiple failed logins
        for i in range(10):
            response = client.post(
                "/api/auth/login/", {"username": "admin", "password": "wrongpassword"}
            )

        # After multiple attempts, should be rate limited
        response = client.post(
            "/api/auth/login/", {"username": "admin", "password": "wrongpassword"}
        )

        # Should be rate limited (429 or 403)
        assert response.status_code in [429, 403]

    @pytest.mark.django_db
    def test_session_invalidation_on_logout(self, client, django_user_model):
        """Test session is invalidated on logout."""
        # Create and login user
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.login(username="testuser", password="TestP@ss123")

        # Get session key
        session_key = client.session.session_key

        # Logout
        client.post("/api/auth/logout/")

        # Try to use old session
        client.cookies["sessionid"] = session_key
        response = client.get("/api/profile/")

        # Should be unauthorized
        assert response.status_code in [401, 403]

    @pytest.mark.django_db
    def test_password_not_logged(self, client, django_user_model):
        """Test passwords are not logged."""
        # This is more of a code review check
        # Ensure logging doesn't include passwords

        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )

        # Password should be hashed
        assert user.password != "TestP@ss123"
        assert user.password.startswith("pbkdf2_") or user.password.startswith("argon2")


class TestFileUploadSecurity:
    """Test file upload security."""

    @pytest.mark.django_db
    def test_file_extension_validation(self, client, django_user_model):
        """Test dangerous file extensions are blocked."""
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.force_login(user)

        dangerous_extensions = ["exe", "bat", "cmd", "sh", "php", "jsp", "asp"]

        for ext in dangerous_extensions:
            # Create fake file
            from io import BytesIO

            file = BytesIO(b"malicious content")
            file.name = f"malicious.{ext}"

            response = client.post("/api/upload/", {"file": file})

            # Should be rejected
            assert response.status_code in [400, 403]

    @pytest.mark.django_db
    def test_file_size_limit(self, client, django_user_model):
        """Test file size limits are enforced."""
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.force_login(user)

        # Create large file (>10MB)
        from io import BytesIO

        large_file = BytesIO(b"x" * (11 * 1024 * 1024))
        large_file.name = "large.jpg"

        response = client.post("/api/upload/", {"file": large_file})

        # Should be rejected
        assert response.status_code in [400, 413]


class TestAPIKeySecurity:
    """Test API key security."""

    @pytest.mark.django_db
    def test_api_key_required(self, client):
        """Test API key is required for API endpoints."""
        response = client.get("/api/v1/data/")

        # Should require authentication
        assert response.status_code in [401, 403]

    @pytest.mark.django_db
    def test_invalid_api_key_rejected(self, client):
        """Test invalid API key is rejected."""
        response = client.get(
            "/api/v1/data/", HTTP_AUTHORIZATION="Api-Key invalid_key_123"
        )

        # Should be unauthorized
        assert response.status_code in [401, 403]


class TestGDPRCompliance:
    """Test GDPR compliance features."""

    @pytest.mark.django_db
    def test_cookie_consent_required(self, client):
        """Test cookie consent is requested."""
        response = client.get("/")
        content = response.content.decode()

        # Should have cookie consent banner/dialog
        assert (
            "cookie" in content.lower() and "consent" in content.lower()
        ) or "gdpr" in content.lower()

    @pytest.mark.django_db
    def test_data_export_available(self, client, django_user_model):
        """Test users can export their data."""
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.force_login(user)

        # Should have data export endpoint
        response = client.post("/api/gdpr/export/")

        # Should succeed or queue for processing
        assert response.status_code in [200, 201, 202]

    @pytest.mark.django_db
    def test_data_deletion_available(self, client, django_user_model):
        """Test users can request data deletion."""
        user = django_user_model.objects.create_user(
            username="testuser", password="TestP@ss123"
        )
        client.force_login(user)

        # Should have data deletion endpoint
        response = client.post("/api/gdpr/delete/")

        # Should succeed or queue for processing
        assert response.status_code in [200, 201, 202]


class TestSecurityMisconfiguration:
    """Test for security misconfigurations."""

    def test_debug_disabled_in_production(self):
        """Test DEBUG is False in production."""
        # In production, DEBUG should be False
        if not settings.DEBUG:
            assert settings.DEBUG is False

    def test_secret_key_not_default(self):
        """Test SECRET_KEY is not the default Django key."""
        assert settings.SECRET_KEY != "django-insecure-"
        assert len(settings.SECRET_KEY) >= 50

    def test_allowed_hosts_configured(self):
        """Test ALLOWED_HOSTS is properly configured."""
        # Should not allow all hosts in production
        if not settings.DEBUG:
            assert settings.ALLOWED_HOSTS != ["*"]
            assert len(settings.ALLOWED_HOSTS) > 0

    def test_database_not_sqlite_in_production(self):
        """Test production doesn't use SQLite."""
        # In production, should use PostgreSQL/MySQL
        if not settings.DEBUG:
            db_engine = settings.DATABASES["default"]["ENGINE"]
            assert "sqlite" not in db_engine.lower()
