"""
AI Optimizer Models
==================

Models for storing AI optimization results and configurations.
"""

from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import models
from django.utils import timezone


class OptimizationSession(models.Model):
    """
    Tracks AI optimization sessions for analytics and debugging.
    """

    STATUS_CHOICES = [
        ("pending", "Pending"),
        ("running", "Running"),
        ("completed", "Completed"),
        ("failed", "Failed"),
    ]

    session_id = models.UUIDField(unique=True, editable=False)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default="pending")
    optimization_type = models.CharField(max_length=50)
    target_url = models.URLField(blank=True)

    # Generic foreign key to link to any model
    content_type = models.ForeignKey(
        ContentType, on_delete=models.CASCADE, null=True, blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    content_object = GenericForeignKey("content_type", "object_id")

    started_at = models.DateTimeField(default=timezone.now)
    completed_at = models.DateTimeField(null=True, blank=True)

    # Store configuration and results as JSON
    config = models.JSONField(default=dict, blank=True)
    results = models.JSONField(default=dict, blank=True)
    error_message = models.TextField(blank=True)

    class Meta:
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["status", "optimization_type"]),
            models.Index(fields=["started_at"]),
        ]

    def __str__(self):
        return f"{self.optimization_type} - {self.session_id}"

    @property
    def duration(self):
        """Calculate session duration if completed"""
        if self.completed_at:
            return self.completed_at - self.started_at
        return None


class OptimizationResult(models.Model):
    """
    Stores individual optimization recommendations and their implementation status.
    """

    PRIORITY_CHOICES = [
        ("low", "Low"),
        ("medium", "Medium"),
        ("high", "High"),
        ("critical", "Critical"),
    ]

    STATUS_CHOICES = [
        ("suggested", "Suggested"),
        ("approved", "Approved"),
        ("implemented", "Implemented"),
        ("rejected", "Rejected"),
    ]

    session = models.ForeignKey(
        OptimizationSession,
        on_delete=models.CASCADE,
        related_name="optimization_results",
    )

    category = models.CharField(
        max_length=50
    )  # image, content, performance, accessibility
    title = models.CharField(max_length=200)
    description = models.TextField()

    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="medium"
    )
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default="suggested"
    )

    # Optimization metrics
    impact_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Expected impact score (0.0 - 1.0)",
    )
    confidence_score = models.FloatField(
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="AI confidence in this recommendation (0.0 - 1.0)",
    )

    # Implementation details
    implementation_notes = models.TextField(blank=True)
    before_metrics = models.JSONField(default=dict, blank=True)
    after_metrics = models.JSONField(default=dict, blank=True)

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-impact_score", "-confidence_score"]
        indexes = [
            models.Index(fields=["session", "category"]),
            models.Index(fields=["priority", "status"]),
            models.Index(fields=["impact_score"]),
        ]

    def __str__(self):
        return f"{self.title} ({self.category})"


class AIOptimizerSettings(models.Model):
    """
    Global settings for the AI optimizer system.
    """

    # Feature toggles
    enabled = models.BooleanField(
        default=False, help_text="Enable AI optimization features"
    )
    auto_optimization = models.BooleanField(
        default=False, help_text="Auto-apply low-risk optimizations"
    )

    # Thresholds and limits
    min_confidence_threshold = models.FloatField(
        default=0.7,
        validators=[MinValueValidator(0.0), MaxValueValidator(1.0)],
        help_text="Minimum confidence score for suggestions",
    )
    max_sessions_per_hour = models.IntegerField(
        default=10, help_text="Rate limit for optimization sessions"
    )
    cache_timeout = models.IntegerField(
        default=3600, help_text="Cache timeout in seconds"
    )

    # Model configurations
    image_analysis_enabled = models.BooleanField(default=True)
    content_analysis_enabled = models.BooleanField(default=True)
    performance_prediction_enabled = models.BooleanField(default=True)
    accessibility_analysis_enabled = models.BooleanField(default=True)

    # API keys and external service configs (stored as JSON for flexibility)
    external_apis = models.JSONField(
        default=dict, blank=True, help_text="External API configurations"
    )

    created_at = models.DateTimeField(default=timezone.now)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "AI Optimizer Settings"
        verbose_name_plural = "AI Optimizer Settings"

    def __str__(self):
        return f"AI Optimizer Settings (Updated: {self.updated_at.strftime('%Y-%m-%d %H:%M')})"

    def save(self, *args, **kwargs):
        # Ensure only one settings instance exists
        if not self.pk and AIOptimizerSettings.objects.exists():
            raise ValueError("Only one AIOptimizerSettings instance allowed")
        super().save(*args, **kwargs)


class OptimizationMetrics(models.Model):
    """
    Tracks metrics before and after optimizations for performance analysis.
    """

    METRIC_TYPES = [
        ("lcp", "Largest Contentful Paint"),
        ("fid", "First Input Delay"),
        ("cls", "Cumulative Layout Shift"),
        ("fcp", "First Contentful Paint"),
        ("ttfb", "Time to First Byte"),
        ("seo_score", "SEO Score"),
        ("accessibility_score", "Accessibility Score"),
        ("performance_score", "Performance Score"),
        ("image_size", "Image Size"),
        ("page_size", "Page Size"),
    ]

    optimization_result = models.ForeignKey(
        OptimizationResult, on_delete=models.CASCADE, related_name="metrics"
    )
    metric_type = models.CharField(max_length=50, choices=METRIC_TYPES)

    before_value = models.FloatField(null=True, blank=True)
    after_value = models.FloatField(null=True, blank=True)
    improvement_percent = models.FloatField(
        null=True, blank=True, help_text="Calculated improvement percentage"
    )

    measured_at = models.DateTimeField(default=timezone.now)

    class Meta:
        unique_together = ["optimization_result", "metric_type"]
        indexes = [
            models.Index(fields=["metric_type", "measured_at"]),
        ]

    def __str__(self):
        return f"{self.get_metric_type_display()}: {self.before_value} → {self.after_value}"

    def save(self, *args, **kwargs):
        # Calculate improvement percentage
        if self.before_value and self.after_value:
            if self.metric_type in ["lcp", "fid", "ttfb", "image_size", "page_size"]:
                # Lower is better for these metrics
                self.improvement_percent = (
                    (self.before_value - self.after_value) / self.before_value
                ) * 100
            else:
                # Higher is better for these metrics
                self.improvement_percent = (
                    (self.after_value - self.before_value) / self.before_value
                ) * 100
        super().save(*args, **kwargs)
