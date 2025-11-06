"""
GDPR Models
===========

Models for GDPR compliance:
- PrivacyPreferences: User privacy settings
- DataCollectionLog: Audit trail for data collection
- ConsentRecord: Consent history
- DataExportRequest: Data portability requests
- DataDeletionRequest: Right to erasure requests
"""

import uuid

from django.contrib.auth import get_user_model
from django.db import models
from django.utils import timezone

User = get_user_model()


class PrivacyPreferences(models.Model):
    """
    User privacy preferences (GDPR Article 7, 21).

    Stores user choices about data processing, retention, and communication.
    """

    user = models.OneToOneField(
        User, on_delete=models.CASCADE, related_name="privacy_preferences"
    )

    # Data retention
    data_retention_period = models.IntegerField(
        default=365, help_text="Days to retain user data (minimum 30, maximum 3650)"
    )

    # Processing preferences
    allow_profiling = models.BooleanField(
        default=False, help_text="Allow user profiling and behavior analysis"
    )
    allow_third_party = models.BooleanField(
        default=False, help_text="Allow sharing data with third parties"
    )
    allow_analytics = models.BooleanField(
        default=False, help_text="Allow analytics and performance tracking"
    )

    # Communication preferences
    communication_preferences = models.JSONField(
        default=dict, help_text="Email, SMS, push notification preferences"
    )

    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Privacy Preferences"
        verbose_name_plural = "Privacy Preferences"
        db_table = "gdpr_privacy_preferences"

    def __str__(self):
        return f"Privacy Preferences for {self.user.username}"


class ConsentRecord(models.Model):
    """
    Consent history (GDPR Article 7).

    Maintains a complete audit trail of consent given/withdrawn.
    """

    CONSENT_TYPES = [
        ("cookie_consent", "Cookie Consent"),
        ("data_processing", "Data Processing"),
        ("marketing", "Marketing Communications"),
        ("analytics", "Analytics Tracking"),
        ("third_party", "Third-Party Data Sharing"),
    ]

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="consent_records",
        null=True,
        blank=True,
    )

    # For anonymous users
    session_id = models.CharField(
        max_length=255, blank=True, help_text="Session ID for anonymous consent"
    )
    ip_address = models.GenericIPAddressField(null=True, blank=True)

    consent_type = models.CharField(max_length=50, choices=CONSENT_TYPES)
    consented = models.BooleanField(
        default=True, help_text="True if consent given, False if withdrawn"
    )

    # Consent details
    consent_text = models.TextField(
        help_text="The exact text shown to user when consent was obtained"
    )
    consent_version = models.CharField(max_length=10, default="1.0")

    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["session_id", "-timestamp"]),
        ]
        db_table = "gdpr_consent_records"

    def __str__(self):
        status = "granted" if self.consented else "withdrawn"
        subject = self.user.username if self.user else self.session_id
        return f"{self.consent_type} {status} by {subject}"


class DataCollectionLog(models.Model):
    """
    Data collection audit log (GDPR Article 30).

    Records all data collection activities for compliance.
    """

    user = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="data_collection_logs",
    )

    # Collection details
    collection_type = models.CharField(
        max_length=100,
        help_text="Type of data collected (e.g., 'contact_form', 'analytics')",
    )
    endpoint = models.CharField(
        max_length=255, help_text="API endpoint or page where data was collected"
    )

    # Data details
    data_categories = models.JSONField(
        default=list,
        help_text="Categories of data collected (e.g., ['email', 'name', 'location'])",
    )
    purpose = models.TextField(help_text="Purpose of data collection")

    # Consent
    has_consent = models.BooleanField(default=False)
    consent_id = models.UUIDField(
        null=True, blank=True, help_text="Link to ConsentRecord"
    )

    # Retention
    retention_period_days = models.IntegerField(
        default=365, help_text="Days to retain this data"
    )
    scheduled_deletion = models.DateTimeField(
        null=True, blank=True, help_text="When this data will be automatically deleted"
    )

    # Metadata
    timestamp = models.DateTimeField(default=timezone.now)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        ordering = ["-timestamp"]
        indexes = [
            models.Index(fields=["user", "-timestamp"]),
            models.Index(fields=["scheduled_deletion"]),
        ]
        db_table = "gdpr_data_collection_logs"

    def __str__(self):
        subject = self.user.username if self.user else "anonymous"
        return f"{self.collection_type} from {subject} at {self.timestamp}"


class DataExportRequest(models.Model):
    """
    Data portability requests (GDPR Article 20).

    Tracks user requests to export their personal data.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="data_export_requests"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Export details
    export_format = models.CharField(
        max_length=10,
        default="json",
        choices=[("json", "JSON"), ("csv", "CSV"), ("xml", "XML")],
    )
    include_categories = models.JSONField(
        default=list, help_text="Categories of data to include in export"
    )

    # File details
    file_path = models.CharField(
        max_length=255, blank=True, help_text="Path to generated export file"
    )
    file_size = models.BigIntegerField(
        null=True, blank=True, help_text="Size of export file in bytes"
    )
    download_url = models.CharField(max_length=500, blank=True)
    download_expires_at = models.DateTimeField(
        null=True, blank=True, help_text="When download link expires (typically 7 days)"
    )

    # Processing metadata
    requested_at = models.DateTimeField(default=timezone.now)
    processed_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["user", "-requested_at"]),
            models.Index(fields=["status"]),
        ]
        db_table = "gdpr_data_export_requests"

    def __str__(self):
        return f"Data export request by {self.user.username} - {self.status}"


class DataDeletionRequest(models.Model):
    """
    Right to erasure requests (GDPR Article 17).

    Tracks user requests to delete their personal data.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("confirmed", "Confirmed"),
        ("processing", "Processing"),
        ("completed", "Completed"),
        ("failed", "Failed"),
        ("cancelled", "Cancelled"),
    ]

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="data_deletion_requests"
    )

    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")

    # Deletion scope
    delete_account = models.BooleanField(
        default=True, help_text="Delete entire account"
    )
    delete_categories = models.JSONField(
        default=list, help_text="Specific data categories to delete"
    )

    # Verification (to prevent accidental deletion)
    verification_code = models.CharField(
        max_length=6, blank=True, help_text="Verification code sent to user's email"
    )
    verification_expires_at = models.DateTimeField(null=True, blank=True)
    verified_at = models.DateTimeField(null=True, blank=True)

    # Processing metadata
    requested_at = models.DateTimeField(default=timezone.now)
    scheduled_deletion_at = models.DateTimeField(
        null=True,
        blank=True,
        help_text="When deletion will be executed (30-day grace period)",
    )
    deleted_at = models.DateTimeField(null=True, blank=True)
    error_message = models.TextField(blank=True)

    # Retention of deleted data info
    deletion_log = models.JSONField(
        default=dict, help_text="Summary of what was deleted (for compliance)"
    )

    class Meta:
        ordering = ["-requested_at"]
        indexes = [
            models.Index(fields=["user", "-requested_at"]),
            models.Index(fields=["status"]),
            models.Index(fields=["scheduled_deletion_at"]),
        ]
        db_table = "gdpr_data_deletion_requests"

    def __str__(self):
        return f"Data deletion request by {self.user.username} - {self.status}"
