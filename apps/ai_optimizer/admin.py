"""
AI Optimizer Admin Configuration
===============================

Django admin interface for managing AI optimization results and settings.
"""

from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html

from .models import (
    AIOptimizerSettings,
    OptimizationMetrics,
    OptimizationResult,
    OptimizationSession,
)


@admin.register(AIOptimizerSettings)
class AIOptimizerSettingsAdmin(admin.ModelAdmin):
    """Admin interface for AI Optimizer Settings"""

    list_display = [
        "enabled",
        "auto_optimization",
        "min_confidence_threshold",
        "max_sessions_per_hour",
        "updated_at",
    ]

    fieldsets = [
        ("Feature Controls", {"fields": ["enabled", "auto_optimization"]}),
        (
            "Analysis Modules",
            {
                "fields": [
                    "image_analysis_enabled",
                    "content_analysis_enabled",
                    "performance_prediction_enabled",
                    "accessibility_analysis_enabled",
                ]
            },
        ),
        (
            "Thresholds & Limits",
            {
                "fields": [
                    "min_confidence_threshold",
                    "max_sessions_per_hour",
                    "cache_timeout",
                ]
            },
        ),
        ("External APIs", {"fields": ["external_apis"], "classes": ["collapse"]}),
        (
            "Timestamps",
            {
                "fields": ["created_at", "updated_at"],
                "classes": ["collapse"],
            },
        ),
    ]

    readonly_fields = ["created_at", "updated_at"]

    def has_add_permission(self, request):
        # Only allow one settings instance
        return not AIOptimizerSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of the settings instance
        return False


class OptimizationResultInline(admin.TabularInline):
    """Inline admin for optimization results within sessions"""

    model = OptimizationResult
    extra = 0
    readonly_fields = ["created_at", "updated_at"]
    fields = [
        "category",
        "title",
        "priority",
        "status",
        "impact_score",
        "confidence_score",
    ]


class OptimizationMetricsInline(admin.TabularInline):
    """Inline admin for optimization metrics within results"""

    model = OptimizationMetrics
    extra = 0
    readonly_fields = ["improvement_percent", "measured_at"]
    fields = [
        "metric_type",
        "before_value",
        "after_value",
        "improvement_percent",
        "measured_at",
    ]


@admin.register(OptimizationSession)
class OptimizationSessionAdmin(admin.ModelAdmin):
    """Admin interface for Optimization Sessions"""

    list_display = [
        "session_id_short",
        "optimization_type",
        "status",
        "target_url_short",
        "started_at",
        "duration_display",
        "results_count",
    ]

    list_filter = ["status", "optimization_type", "started_at"]

    search_fields = ["session_id", "target_url", "optimization_type"]

    readonly_fields = [
        "session_id",
        "started_at",
        "completed_at",
        "duration_display",
        "results_count",
        "config_display",
        "results_display",
    ]

    fieldsets = [
        (
            "Session Info",
            {"fields": ["session_id", "optimization_type", "status", "target_url"]},
        ),
        (
            "Content Object",
            {"fields": ["content_type", "object_id"], "classes": ["collapse"]},
        ),
        ("Timing", {"fields": ["started_at", "completed_at", "duration_display"]}),
        (
            "Results",
            {
                "fields": ["results_count", "config_display", "results_display"],
                "classes": ["collapse"],
            },
        ),
        ("Errors", {"fields": ["error_message"], "classes": ["collapse"]}),
    ]

    inlines = [OptimizationResultInline]

    def session_id_short(self, obj):
        return str(obj.session_id)[:8] + "..."

    session_id_short.short_description = "Session ID"

    def target_url_short(self, obj):
        if obj.target_url:
            return obj.target_url[:50] + ("..." if len(obj.target_url) > 50 else "")
        return "-"

    target_url_short.short_description = "Target URL"

    def duration_display(self, obj):
        duration = obj.duration
        if duration:
            return str(duration)
        elif obj.status == "running":
            return "Running..."
        return "-"

    duration_display.short_description = "Duration"

    def results_count(self, obj):
        count = obj.optimization_results.count()
        if count > 0:
            url = reverse("admin:ai_optimizer_optimizationresult_changelist")
            return format_html(
                '<a href="{}?session__id__exact={}">{} results</a>', url, obj.id, count
            )
        return "0 results"

    results_count.short_description = "Results"

    def config_display(self, obj):
        if obj.config:
            return format_html("<pre>{}</pre>", str(obj.config))
        return "-"

    config_display.short_description = "Configuration"

    def results_display(self, obj):
        if obj.results:
            return format_html("<pre>{}</pre>", str(obj.results))
        return "-"

    results_display.short_description = "Results Data"


@admin.register(OptimizationResult)
class OptimizationResultAdmin(admin.ModelAdmin):
    """Admin interface for Optimization Results"""

    list_display = [
        "title_short",
        "category",
        "priority",
        "status",
        "impact_score",
        "confidence_score",
        "session_link",
        "created_at",
    ]

    list_filter = ["category", "priority", "status", "created_at"]

    search_fields = ["title", "description", "session__session_id"]

    readonly_fields = [
        "session",
        "created_at",
        "updated_at",
        "metrics_count",
        "before_metrics_display",
        "after_metrics_display",
    ]

    fieldsets = [
        ("Basic Info", {"fields": ["session", "category", "title", "description"]}),
        (
            "Status & Priority",
            {"fields": ["priority", "status", "implementation_notes"]},
        ),
        ("Scores", {"fields": ["impact_score", "confidence_score"]}),
        (
            "Metrics",
            {
                "fields": [
                    "metrics_count",
                    "before_metrics_display",
                    "after_metrics_display",
                ],
                "classes": ["collapse"],
            },
        ),
        (
            "Timestamps",
            {"fields": ["created_at", "updated_at"], "classes": ["collapse"]},
        ),
    ]

    inlines = [OptimizationMetricsInline]

    def title_short(self, obj):
        return obj.title[:50] + ("..." if len(obj.title) > 50 else "")

    title_short.short_description = "Title"

    def session_link(self, obj):
        url = reverse(
            "admin:ai_optimizer_optimizationsession_change", args=[obj.session.id]
        )
        return format_html(
            '<a href="{}">{}</a>', url, str(obj.session.session_id)[:8] + "..."
        )

    session_link.short_description = "Session"

    def metrics_count(self, obj):
        count = obj.metrics.count()
        if count > 0:
            url = reverse("admin:ai_optimizer_optimizationmetrics_changelist")
            return format_html(
                '<a href="{}?optimization_result__id__exact={}">{} metrics</a>',
                url,
                obj.id,
                count,
            )
        return "0 metrics"

    metrics_count.short_description = "Metrics"

    def before_metrics_display(self, obj):
        if obj.before_metrics:
            return format_html("<pre>{}</pre>", str(obj.before_metrics))
        return "-"

    before_metrics_display.short_description = "Before Metrics"

    def after_metrics_display(self, obj):
        if obj.after_metrics:
            return format_html("<pre>{}</pre>", str(obj.after_metrics))
        return "-"

    after_metrics_display.short_description = "After Metrics"


@admin.register(OptimizationMetrics)
class OptimizationMetricsAdmin(admin.ModelAdmin):
    """Admin interface for Optimization Metrics"""

    list_display = [
        "optimization_result_short",
        "metric_type",
        "before_value",
        "after_value",
        "improvement_percent",
        "measured_at",
    ]

    list_filter = ["metric_type", "measured_at"]

    search_fields = ["optimization_result__title", "metric_type"]

    readonly_fields = ["improvement_percent", "measured_at"]

    def optimization_result_short(self, obj):
        title = obj.optimization_result.title
        return title[:30] + ("..." if len(title) > 30 else "")

    optimization_result_short.short_description = "Optimization Result"
