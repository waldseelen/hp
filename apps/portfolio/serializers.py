"""
==========================================================================
DJANGO REST FRAMEWORK SERIALIZERS
==========================================================================
Serializers for performance monitoring, push notifications, and error logging
Handles validation and data processing for API endpoints
==========================================================================
"""

from rest_framework import serializers

from .models import (
    AITool,
    CybersecurityResource,
    ErrorLog,
    NotificationLog,
    PerformanceMetric,
    PersonalInfo,
    SocialLink,
    UsefulResource,
    WebPushSubscription,
)

# ==========================================================================
# PERFORMANCE MONITORING SERIALIZERS
# ==========================================================================


class PerformanceMetricSerializer(serializers.ModelSerializer):
    """Serializer for performance metrics collected from the frontend"""

    class Meta:
        model = PerformanceMetric
        fields = [
            "id",
            "metric_type",
            "value",
            "url",
            "user_agent",
            "device_type",
            "connection_type",
            "screen_resolution",
            "viewport_size",
            "additional_data",
            "session_id",
            "ip_address",
            "country_code",
            "timestamp",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]

    def validate_value(self, value):
        """Validate that performance metric values are reasonable"""
        if value < 0:
            raise serializers.ValidationError(
                "Performance metric values cannot be negative"
            )

        # Set reasonable upper bounds for different metrics
        metric_type = self.initial_data.get("metric_type")
        if metric_type in ["lcp", "fcp", "ttfb"] and value > 60000:  # 60 seconds max
            raise serializers.ValidationError(
                f"{metric_type} value seems too high (max 60s)"
            )
        elif metric_type == "cls" and value > 5.0:  # CLS max reasonable value
            raise serializers.ValidationError("CLS value seems too high (max 5.0)")
        elif metric_type in ["fid", "inp"] and value > 10000:  # 10 seconds max
            raise serializers.ValidationError(
                f"{metric_type} value seems too high (max 10s)"
            )

        return value

    def validate_url(self, value):
        """Ensure URL is from the same domain or allowed domains"""
        from django.conf import settings

        allowed_domains = getattr(settings, "PERFORMANCE_ALLOWED_DOMAINS", [])

        if allowed_domains:
            from urllib.parse import urlparse

            domain = urlparse(value).netloc
            if domain not in allowed_domains:
                raise serializers.ValidationError(
                    "URL domain not allowed for performance tracking"
                )

        return value

    def create(self, validated_data):
        """Create performance metric with additional context"""
        request = self.context.get("request")
        if request:
            # Add IP address if not provided
            if not validated_data.get("ip_address"):
                validated_data["ip_address"] = self.get_client_ip(request)

            # Add user agent if not provided
            if not validated_data.get("user_agent"):
                validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

        return super().create(validated_data)

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "")


class PerformanceMetricSummarySerializer(serializers.Serializer):
    """Serializer for performance metric summaries and analytics"""

    metric_type = serializers.CharField()
    count = serializers.IntegerField()
    average = serializers.FloatField()
    median = serializers.FloatField()
    p75 = serializers.FloatField()
    p95 = serializers.FloatField()
    good_count = serializers.IntegerField()
    needs_improvement_count = serializers.IntegerField()
    poor_count = serializers.IntegerField()
    period_start = serializers.DateTimeField()
    period_end = serializers.DateTimeField()


# ==========================================================================
# PUSH NOTIFICATIONS SERIALIZERS
# ==========================================================================


class WebPushSubscriptionSerializer(serializers.ModelSerializer):
    """Serializer for web push subscriptions"""

    class Meta:
        model = WebPushSubscription
        fields = [
            "id",
            "endpoint",
            "p256dh",
            "auth",
            "user_agent",
            "browser",
            "platform",
            "enabled",
            "topics",
            "ip_address",
            "country_code",
            "total_sent",
            "total_delivered",
            "total_failed",
            "last_success",
            "last_failure",
            "failure_reason",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "total_sent",
            "total_delivered",
            "total_failed",
            "last_success",
            "last_failure",
            "failure_reason",
            "created_at",
            "updated_at",
        ]

    def validate_endpoint(self, value):
        """Validate push subscription endpoint"""
        if not value.startswith("https://"):
            raise serializers.ValidationError(
                "Push subscription endpoint must use HTTPS"
            )

        # Check for known push service domains
        known_services = [
            "fcm.googleapis.com",
            "web.push.apple.com",
            "push.services.mozilla.com",
            "wns2-par02p.notify.windows.com",
        ]

        from urllib.parse import urlparse

        domain = urlparse(value).netloc
        if not any(service in domain for service in known_services):
            # Log unknown push service for monitoring
            import logging

            logger = logging.getLogger("main.security")
            logger.warning(f"Unknown push service domain: {domain}")

        return value

    def validate_p256dh(self, value):
        """Validate P-256 ECDH public key format"""
        import base64
        import re

        if not re.match(r"^[A-Za-z0-9+/]+=*$", value):
            raise serializers.ValidationError("Invalid base64 format for p256dh key")

        try:
            decoded = base64.b64decode(value)
            if len(decoded) != 65:  # P-256 public key should be 65 bytes
                raise serializers.ValidationError("Invalid P-256 public key length")
        except Exception:
            raise serializers.ValidationError("Invalid base64 encoding for p256dh key")

        return value

    def validate_auth(self, value):
        """Validate authentication secret format"""
        import base64
        import re

        if not re.match(r"^[A-Za-z0-9+/]+=*$", value):
            raise serializers.ValidationError("Invalid base64 format for auth secret")

        try:
            decoded = base64.b64decode(value)
            if len(decoded) != 16:  # Auth secret should be 16 bytes
                raise serializers.ValidationError(
                    "Invalid authentication secret length"
                )
        except Exception:
            raise serializers.ValidationError("Invalid base64 encoding for auth secret")

        return value

    def create(self, validated_data):
        """Create subscription with additional context"""
        request = self.context.get("request")
        if request:
            # Add IP address if not provided
            if not validated_data.get("ip_address"):
                validated_data["ip_address"] = (
                    PerformanceMetricSerializer.get_client_ip(request)
                )

            # Parse user agent for browser and platform info
            if not validated_data.get("browser") or not validated_data.get("platform"):
                user_agent = validated_data.get("user_agent") or request.META.get(
                    "HTTP_USER_AGENT", ""
                )
                browser_info = self.parse_user_agent(user_agent)
                if not validated_data.get("browser"):
                    validated_data["browser"] = browser_info.get("browser", "Unknown")
                if not validated_data.get("platform"):
                    validated_data["platform"] = browser_info.get("platform", "Unknown")

        return super().create(validated_data)

    @staticmethod
    def parse_user_agent(user_agent):
        """Parse browser and platform info from user agent string"""
        browser = "Unknown"
        platform = "Unknown"

        if "Chrome" in user_agent:
            browser = "Chrome"
        elif "Firefox" in user_agent:
            browser = "Firefox"
        elif "Safari" in user_agent and "Chrome" not in user_agent:
            browser = "Safari"
        elif "Edge" in user_agent:
            browser = "Edge"

        if "Windows" in user_agent:
            platform = "Windows"
        elif "Macintosh" in user_agent or "Mac OS" in user_agent:
            platform = "macOS"
        elif "Linux" in user_agent:
            platform = "Linux"
        elif "Android" in user_agent:
            platform = "Android"
        elif "iPhone" in user_agent or "iPad" in user_agent:
            platform = "iOS"

        return {"browser": browser, "platform": platform}


class NotificationLogSerializer(serializers.ModelSerializer):
    """Serializer for notification logs and history"""

    subscription_info = serializers.SerializerMethodField()

    class Meta:
        model = NotificationLog
        fields = [
            "id",
            "title",
            "body",
            "icon",
            "image",
            "badge",
            "notification_type",
            "tag",
            "actions",
            "url",
            "subscription",
            "subscription_info",
            "topics",
            "status",
            "sent_at",
            "delivered_at",
            "error_message",
            "additional_data",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_subscription_info(self, obj):
        """Get basic info about the target subscription"""
        if obj.subscription:
            return {
                "browser": obj.subscription.browser,
                "platform": obj.subscription.platform,
                "enabled": obj.subscription.enabled,
            }
        return None


class SendNotificationSerializer(serializers.Serializer):
    """Serializer for sending push notifications"""

    title = serializers.CharField(max_length=200)
    body = serializers.CharField(max_length=500)
    icon = serializers.URLField(required=False, allow_blank=True)
    image = serializers.URLField(required=False, allow_blank=True)
    badge = serializers.URLField(required=False, allow_blank=True)
    url = serializers.URLField(required=False, allow_blank=True)
    tag = serializers.CharField(max_length=100, required=False, allow_blank=True)
    notification_type = serializers.ChoiceField(
        choices=NotificationLog.NOTIFICATION_TYPE_CHOICES, default="custom"
    )
    topics = serializers.ListField(
        child=serializers.CharField(max_length=50), required=False, allow_empty=True
    )
    actions = serializers.ListField(
        child=serializers.DictField(), required=False, allow_empty=True
    )
    target_subscription_ids = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        allow_empty=True,
        help_text="Specific subscription IDs to target (if not provided, sends to all active)",
    )

    def validate_actions(self, value):
        """Validate notification action buttons"""
        if len(value) > 2:
            raise serializers.ValidationError(
                "Maximum 2 action buttons allowed per notification"
            )

        for action in value:
            if "action" not in action or "title" not in action:
                raise serializers.ValidationError(
                    "Each action must have 'action' and 'title' fields"
                )

        return value


# ==========================================================================
# ERROR LOGGING SERIALIZERS
# ==========================================================================


class ErrorLogSerializer(serializers.ModelSerializer):
    """Serializer for error logs from frontend and backend"""

    class Meta:
        model = ErrorLog
        fields = [
            "id",
            "error_type",
            "level",
            "message",
            "stack_trace",
            "url",
            "user_agent",
            "ip_address",
            "file_name",
            "line_number",
            "function_name",
            "additional_data",
            "is_resolved",
            "resolved_at",
            "resolution_notes",
            "occurrence_count",
            "first_occurred",
            "last_occurred",
            "created_at",
            "updated_at",
        ]
        read_only_fields = [
            "id",
            "occurrence_count",
            "first_occurred",
            "last_occurred",
            "created_at",
            "updated_at",
        ]

    def create(self, validated_data):
        """Create error log with additional context"""
        request = self.context.get("request")
        if request:
            # Add IP address if not provided
            if not validated_data.get("ip_address"):
                validated_data["ip_address"] = (
                    PerformanceMetricSerializer.get_client_ip(request)
                )

            # Add user agent if not provided
            if not validated_data.get("user_agent"):
                validated_data["user_agent"] = request.META.get("HTTP_USER_AGENT", "")

        # Check if similar error already exists
        similar_error = ErrorLog.objects.filter(
            error_type=validated_data["error_type"],
            message=validated_data["message"],
            url=validated_data.get("url", ""),
            is_resolved=False,
        ).first()

        if similar_error:
            # Update existing error occurrence
            similar_error.increment_occurrence()
            return similar_error

        return super().create(validated_data)


# ==========================================================================
# CONTENT SERIALIZERS (For API access to existing content)
# ==========================================================================


class PersonalInfoSerializer(serializers.ModelSerializer):
    """Serializer for personal information"""

    class Meta:
        model = PersonalInfo
        fields = ["id", "key", "value", "type", "is_public", "created_at", "updated_at"]
        read_only_fields = ["id", "created_at", "updated_at"]


class SocialLinkSerializer(serializers.ModelSerializer):
    """Serializer for social media links"""

    class Meta:
        model = SocialLink
        fields = [
            "id",
            "platform",
            "username",
            "url",
            "is_active",
            "order",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class AIToolSerializer(serializers.ModelSerializer):
    """Serializer for AI tools"""

    class Meta:
        model = AITool
        fields = [
            "id",
            "name",
            "description",
            "url",
            "category",
            "icon_url",
            "image",
            "is_featured",
            "is_free",
            "rating",
            "tags",
            "order",
            "is_visible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class CybersecurityResourceSerializer(serializers.ModelSerializer):
    """Serializer for cybersecurity resources"""

    class Meta:
        model = CybersecurityResource
        fields = [
            "id",
            "title",
            "description",
            "content",
            "type",
            "difficulty",
            "url",
            "image",
            "tags",
            "is_featured",
            "is_urgent",
            "severity_level",
            "order",
            "is_visible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class UsefulResourceSerializer(serializers.ModelSerializer):
    """Serializer for useful resources"""

    class Meta:
        model = UsefulResource
        fields = [
            "id",
            "name",
            "description",
            "url",
            "type",
            "category",
            "icon_url",
            "image",
            "is_free",
            "is_featured",
            "rating",
            "tags",
            "order",
            "is_visible",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


# ==========================================================================
# HEALTH CHECK SERIALIZER
# ==========================================================================


class HealthCheckSerializer(serializers.Serializer):
    """Serializer for health check endpoint responses"""

    status = serializers.CharField()
    timestamp = serializers.DateTimeField()
    version = serializers.CharField()
    database = serializers.CharField()
    cache = serializers.CharField()
    features = serializers.DictField()
    performance = serializers.DictField(required=False)
