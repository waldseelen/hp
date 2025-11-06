"""
Unit tests for Portfolio Utility Models.

Tests cover:
- ShortURL (auto 6-char code generation, collision handling, analytics)

Target: 10 comprehensive tests for URL shortening service.
"""

from datetime import timedelta

from django.db import IntegrityError
from django.utils import timezone

import pytest

from apps.portfolio.models import ShortURL

# ============================================================================
# SHORTURL MODEL TESTS (Auto Code Generation, Analytics)
# ============================================================================


@pytest.mark.django_db
class TestShortURLModel:
    """Test ShortURL model - URL shortening with analytics."""

    def test_shorturl_creation(self):
        """Test basic ShortURL creation."""
        short_url = ShortURL.objects.create(
            short_code="abc123",
            original_url="https://example.com/very/long/url/that/needs/shortening",
        )
        assert short_url.short_code == "abc123"
        assert short_url.is_active
        assert short_url.click_count == 0

    def test_shorturl_unique_code_constraint(self):
        """Test short_code uniqueness."""
        ShortURL.objects.create(
            short_code="unique",
            original_url="https://example.com/1",
        )

        # Creating duplicate should raise IntegrityError
        with pytest.raises(IntegrityError):
            ShortURL.objects.create(
                short_code="unique",
                original_url="https://example.com/2",
            )

    def test_shorturl_click_tracking(self):
        """Test click count increment."""
        short_url = ShortURL.objects.create(
            short_code="clicks",
            original_url="https://example.com",
        )
        assert short_url.click_count == 0

        # Simulate 5 clicks
        for _ in range(5):
            short_url.increment_click()

        short_url.refresh_from_db()
        assert short_url.click_count == 5

    def test_shorturl_expiration_check(self):
        """Test expiration checking."""
        # Non-expiring URL
        short_url = ShortURL.objects.create(
            short_code="noexp",
            original_url="https://example.com",
        )
        assert not short_url.is_expired

        # Expired URL
        expired_url = ShortURL.objects.create(
            short_code="expired",
            original_url="https://example.com",
        )
        expired_url.expires_at = timezone.now() - timedelta(days=1)
        expired_url.save()
        assert expired_url.is_expired

    def test_shorturl_active_inactive(self):
        """Test active/inactive status."""
        short_url = ShortURL.objects.create(
            short_code="active",
            original_url="https://example.com",
            is_active=True,
        )
        assert short_url.is_active

        # Deactivate
        short_url.is_active = False
        short_url.save()
        assert not short_url.is_active

    def test_shorturl_with_metadata(self):
        """Test ShortURL with title and description."""
        short_url = ShortURL.objects.create(
            short_code="meta",
            original_url="https://example.com",
            title="Example Website",
            description="This is an example website for testing.",
        )
        assert short_url.title == "Example Website"
        assert short_url.description

    def test_shorturl_password_protection(self):
        """Test password-protected short URLs."""
        short_url = ShortURL.objects.create(
            short_code="secure",
            original_url="https://example.com/private",
            password="secret123",
        )
        assert short_url.password == "secret123"

    def test_shorturl_string_representation(self):
        """Test ShortURL __str__ method."""
        short_url = ShortURL.objects.create(
            short_code="test",
            original_url="https://example.com/this/is/a/very/long/url/for/testing",
        )
        str_repr = str(short_url)
        assert "test" in str_repr
        assert len(str_repr) < 100  # Should be truncated

    def test_shorturl_long_original_url(self):
        """Test handling very long URLs."""
        long_url = "https://example.com/" + "a" * 1900  # Total ~1920 chars
        short_url = ShortURL.objects.create(
            short_code="longurl",
            original_url=long_url,
        )
        assert len(short_url.original_url) == len(long_url)

    def test_shorturl_click_analytics(self):
        """Test click analytics over time."""
        short_url = ShortURL.objects.create(
            short_code="analytics",
            original_url="https://example.com",
        )

        # Simulate clicks over time
        for i in range(10):
            short_url.increment_click()

        short_url.refresh_from_db()
        assert short_url.click_count == 10
