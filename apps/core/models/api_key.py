"""
API Key Model for Server-to-Server Authentication
=================================================

Provides API key-based authentication with:
- Secure key generation and hashing
- Scoped permissions (read, write, admin)
- Rate limiting per key
- Usage tracking and analytics
- Key expiration
"""

import hashlib
import secrets
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

User = get_user_model()


class APIKeyManager(models.Manager):
    """
    Manager for API Key model
    """

    def get_from_key(self, key: str) -> Optional["APIKey"]:
        """
        Get API key object from raw key string
        """
        # Hash the key
        key_hash = self._hash_key(key)

        try:
            return self.get(key_hash=key_hash, is_active=True)
        except APIKey.DoesNotExist:
            return None

    @staticmethod
    def _hash_key(key: str) -> str:
        """
        Hash API key using SHA-256
        """
        return hashlib.sha256(key.encode()).hexdigest()

    def create_key(
        self,
        user,
        name: str,
        permissions: str = "read",
        rate_limit: int = 1000,
        expires_days: Optional[int] = None,
    ) -> Dict[str, Any]:
        """
        Create new API key

        Returns: Dict with 'key' (raw key - show only once) and 'api_key' object
        """
        # Generate secure random key
        raw_key = self._generate_key()
        key_hash = self._hash_key(raw_key)

        # Calculate expiry
        expires_at = None
        if expires_days:
            expires_at = timezone.now() + timedelta(days=expires_days)

        # Create API key object
        api_key = self.create(
            user=user,
            name=name,
            key_hash=key_hash,
            key_prefix=raw_key[:8],  # Store prefix for identification
            permissions=permissions,
            rate_limit_per_hour=rate_limit,
            expires_at=expires_at,
        )

        return {
            "key": raw_key,  # Show only once!
            "api_key": api_key,
        }

    @staticmethod
    def _generate_key(length: int = 40) -> str:
        """
        Generate secure random API key
        """
        return secrets.token_urlsafe(length)


class APIKey(models.Model):
    """
    API Key model for server-to-server authentication
    """

    class Permissions(models.TextChoices):
        READ = "read", _("Read Only")
        WRITE = "write", _("Read/Write")
        ADMIN = "admin", _("Full Access")

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="api_keys",
        help_text=_("User who owns this API key"),
    )

    name = models.CharField(
        max_length=200, help_text=_("Descriptive name for this API key")
    )

    key_hash = models.CharField(
        max_length=64,
        unique=True,
        db_index=True,
        help_text=_("SHA-256 hash of the API key"),
    )

    key_prefix = models.CharField(
        max_length=8, help_text=_("First 8 characters of key for identification")
    )

    permissions = models.CharField(
        max_length=10,
        choices=Permissions.choices,
        default=Permissions.READ,
        help_text=_("Permission level for this API key"),
    )

    is_active = models.BooleanField(
        default=True, help_text=_("Whether this API key is active")
    )

    rate_limit_per_hour = models.IntegerField(
        default=1000, help_text=_("Maximum requests per hour for this key")
    )

    created_at = models.DateTimeField(
        auto_now_add=True, help_text=_("When this API key was created")
    )

    last_used_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When this API key was last used")
    )

    expires_at = models.DateTimeField(
        null=True, blank=True, help_text=_("When this API key expires")
    )

    usage_count = models.IntegerField(
        default=0, help_text=_("Total number of requests using this key")
    )

    objects = APIKeyManager()

    class Meta:
        verbose_name = _("API Key")
        verbose_name_plural = _("API Keys")
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["key_hash", "is_active"]),
            models.Index(fields=["user", "is_active"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.key_prefix}...)"

    @property
    def is_expired(self) -> bool:
        """
        Check if API key has expired
        """
        if not self.expires_at:
            return False
        return timezone.now() > self.expires_at

    def check_rate_limit(self) -> bool:
        """
        Check if API key is within rate limit
        """
        # Use Redis cache for rate limiting
        cache_key = f"api_key_rate_limit:{self.key_hash}"
        current_count = cache.get(cache_key, 0)

        if current_count >= self.rate_limit_per_hour:
            return False

        return True

    def record_usage(self, endpoint: str, ip_address: str) -> None:
        """
        Record API key usage
        """
        # Update rate limit counter
        cache_key = f"api_key_rate_limit:{self.key_hash}"
        current_count = cache.get(cache_key, 0)
        cache.set(cache_key, current_count + 1, timeout=3600)  # 1 hour

        # Update last used timestamp and usage count
        self.last_used_at = timezone.now()
        self.usage_count += 1
        self.save(update_fields=["last_used_at", "usage_count"])

        # Log usage (optional - can be stored in separate model)
        APIKeyUsage.objects.create(
            api_key=self,
            endpoint=endpoint,
            ip_address=ip_address,
        )

    def revoke(self) -> None:
        """
        Revoke API key
        """
        self.is_active = False
        self.save(update_fields=["is_active"])

    def has_permission(self, required_permission: str) -> bool:
        """
        Check if API key has required permission
        """
        permission_hierarchy = {
            "read": 0,
            "write": 1,
            "admin": 2,
        }

        current_level = permission_hierarchy.get(self.permissions, 0)
        required_level = permission_hierarchy.get(required_permission, 0)

        return current_level >= required_level


class APIKeyUsage(models.Model):
    """
    Track API key usage for analytics
    """

    api_key = models.ForeignKey(
        APIKey, on_delete=models.CASCADE, related_name="usage_logs"
    )

    endpoint = models.CharField(max_length=500, help_text=_("API endpoint accessed"))

    ip_address = models.GenericIPAddressField(help_text=_("IP address of the request"))

    timestamp = models.DateTimeField(
        auto_now_add=True, help_text=_("When the request was made")
    )

    class Meta:
        verbose_name = _("API Key Usage")
        verbose_name_plural = _("API Key Usages")
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["api_key", "-timestamp"]),
            models.Index(fields=["-timestamp"]),
        ]

    def __str__(self):
        return f"{self.api_key.name} - {self.endpoint} at {self.timestamp}"
