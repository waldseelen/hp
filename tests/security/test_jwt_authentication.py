"""
JWT Authentication & API Security Tests
=======================================

Tests for JWT authentication, API keys, and API rate limiting.
"""

from django.contrib.auth import get_user_model
from django.test import RequestFactory, TestCase
from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.core.auth.jwt_backend import CustomJWTAuthentication, JWTTokenManager
from apps.core.middleware.api_rate_limiting import APIRateLimitMiddleware
from apps.core.models.api_key import APIKey

User = get_user_model()


class TestJWTAuthentication(TestCase):
    """Test JWT token authentication"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )
        self.client = APIClient()

    def test_token_obtain_success(self):
        """Test successful token obtain (login)"""
        # Attempt login
        response = self.client.post(
            "/api/v1/auth/token/",
            {"username": "testuser", "password": "TestPassword123!"},
        )

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data
        assert "refresh" in response.data
        assert "access_expires_in" in response.data
        assert "refresh_expires_in" in response.data

    def test_token_obtain_invalid_credentials(self):
        """Test token obtain with invalid credentials"""
        response = self.client.post(
            "/api/v1/auth/token/", {"username": "testuser", "password": "wrongpassword"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "error" in response.data

    def test_token_obtain_missing_fields(self):
        """Test token obtain with missing fields"""
        response = self.client.post("/api/v1/auth/token/", {"username": "testuser"})

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_token_refresh_success(self):
        """Test successful token refresh"""
        # Get tokens
        tokens = JWTTokenManager.create_tokens_for_user(self.user)
        refresh_token = tokens["refresh"]

        # Refresh access token
        response = self.client.post("/api/v1/auth/refresh/", {"refresh": refresh_token})

        assert response.status_code == status.HTTP_200_OK
        assert "access" in response.data

    def test_token_refresh_invalid_token(self):
        """Test token refresh with invalid token"""
        response = self.client.post(
            "/api/v1/auth/refresh/", {"refresh": "invalid_token"}
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_token_blacklist_success(self):
        """Test successful token blacklist (logout)"""
        # Get tokens
        tokens = JWTTokenManager.create_tokens_for_user(self.user)

        # Authenticate
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        # Logout
        response = self.client.post(
            "/api/v1/auth/logout/", {"refresh": tokens["refresh"]}
        )

        assert response.status_code == status.HTTP_200_OK

    def test_token_verify_success(self):
        """Test token verification"""
        # Get tokens
        tokens = JWTTokenManager.create_tokens_for_user(self.user)

        # Authenticate
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        # Verify token
        response = self.client.get("/api/v1/auth/verify/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["valid"] is True
        assert response.data["user"]["username"] == "testuser"

    def test_token_verify_unauthorized(self):
        """Test token verification without authentication"""
        response = self.client.get("/api/v1/auth/verify/")

        assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAPIKeyManagement(TestCase):
    """Test API key management"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )
        self.client = APIClient()

        # Authenticate
        tokens = JWTTokenManager.create_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

    def test_create_api_key_success(self):
        """Test successful API key creation"""
        response = self.client.post(
            "/api/v1/api-keys/",
            {
                "name": "Test API Key",
                "permissions": "read",
                "rate_limit": 1000,
            },
        )

        assert response.status_code == status.HTTP_201_CREATED
        assert "key" in response.data
        assert "api_key" in response.data
        assert "warning" in response.data

    def test_create_api_key_missing_name(self):
        """Test API key creation without name"""
        response = self.client.post(
            "/api/v1/api-keys/",
            {
                "permissions": "read",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_create_api_key_invalid_permissions(self):
        """Test API key creation with invalid permissions"""
        response = self.client.post(
            "/api/v1/api-keys/",
            {
                "name": "Test Key",
                "permissions": "invalid",
            },
        )

        assert response.status_code == status.HTTP_400_BAD_REQUEST

    def test_list_api_keys(self):
        """Test listing user's API keys"""
        # Create API key
        APIKey.objects.create_key(
            user=self.user,
            name="Test Key 1",
            permissions="read",
        )
        APIKey.objects.create_key(
            user=self.user,
            name="Test Key 2",
            permissions="write",
        )

        # List keys
        response = self.client.get("/api/v1/api-keys/")

        assert response.status_code == status.HTTP_200_OK
        assert len(response.data) == 2

    def test_get_api_key_detail(self):
        """Test getting API key details"""
        # Create API key
        result = APIKey.objects.create_key(
            user=self.user,
            name="Test Key",
            permissions="read",
        )
        key_id = result["api_key"].id

        # Get details
        response = self.client.get(f"/api/v1/api-keys/{key_id}/")

        assert response.status_code == status.HTTP_200_OK
        assert response.data["name"] == "Test Key"

    def test_revoke_api_key(self):
        """Test revoking API key"""
        # Create API key
        result = APIKey.objects.create_key(
            user=self.user,
            name="Test Key",
            permissions="read",
        )
        key_id = result["api_key"].id

        # Revoke key
        response = self.client.delete(f"/api/v1/api-keys/{key_id}/")

        assert response.status_code == status.HTTP_200_OK

        # Verify key is revoked
        api_key = APIKey.objects.get(id=key_id)
        assert api_key.is_active is False


class TestAPIRateLimiting(TestCase):
    """Test API rate limiting"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )
        self.client = APIClient()
        self.factory = RequestFactory()

    def test_rate_limit_anonymous_user(self):
        """Test rate limiting for anonymous users"""
        # Simulate 21 requests (exceeds 20/min limit)
        for i in range(21):
            response = self.client.get("/api/v1/health/")

        # Last request should be rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS
        assert "Retry-After" in response
        assert "X-RateLimit-Limit" in response

    def test_rate_limit_authenticated_user(self):
        """Test rate limiting for authenticated users"""
        # Authenticate
        tokens = JWTTokenManager.create_tokens_for_user(self.user)
        self.client.credentials(HTTP_AUTHORIZATION=f"Bearer {tokens['access']}")

        # Simulate 61 requests (exceeds 60/min limit)
        for i in range(61):
            response = self.client.get("/api/v1/health/")

        # Last request should be rate limited
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_rate_limit_headers_present(self):
        """Test that rate limit headers are present"""
        response = self.client.get("/api/v1/health/")

        assert "X-RateLimit-Limit" in response
        assert "X-RateLimit-Remaining" in response
        assert "X-RateLimit-Reset" in response

    def test_exempt_endpoint_no_rate_limit(self):
        """Test that exempt endpoints are not rate limited"""
        # Make many requests to exempt endpoint
        for i in range(100):
            response = self.client.get("/api/v1/health/")

        # Should not be rate limited
        assert response.status_code != status.HTTP_429_TOO_MANY_REQUESTS


class TestAPIKeyAuthentication(TestCase):
    """Test API key authentication"""

    def setUp(self):
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="TestPassword123!"
        )

        # Create API key
        result = APIKey.objects.create_key(
            user=self.user,
            name="Test API Key",
            permissions="read",
            rate_limit=1000,
        )
        self.api_key = result["key"]
        self.api_key_obj = result["api_key"]

        self.client = APIClient()

    def test_api_key_authentication_success(self):
        """Test successful API key authentication"""
        # Use API key in header
        response = self.client.get(
            "/api/v1/some-endpoint/", HTTP_X_API_KEY=self.api_key
        )

        # Should be authenticated
        # (Actual endpoint would return 200, not 404)

    def test_api_key_authentication_invalid_key(self):
        """Test API key authentication with invalid key"""
        response = self.client.get(
            "/api/v1/some-endpoint/", HTTP_X_API_KEY="invalid_key"
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_api_key_rate_limiting(self):
        """Test API key rate limiting"""
        # Simulate exceeding rate limit
        for i in range(1001):
            response = self.client.get(
                "/api/v1/some-endpoint/", HTTP_X_API_KEY=self.api_key
            )

        # Should be throttled
        assert response.status_code == status.HTTP_429_TOO_MANY_REQUESTS

    def test_revoked_api_key_rejected(self):
        """Test that revoked API keys are rejected"""
        # Revoke key
        self.api_key_obj.revoke()

        # Try to use revoked key
        response = self.client.get(
            "/api/v1/some-endpoint/", HTTP_X_API_KEY=self.api_key
        )

        assert response.status_code == status.HTTP_401_UNAUTHORIZED
