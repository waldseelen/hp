"""
API Views for monitoring and performance tracking
Enhanced with comprehensive input validation and sanitization
"""

import json
import logging
import re
from datetime import datetime

from django.core.cache import cache
from django.db import connection
from django.http import JsonResponse
from django.utils.html import strip_tags
from django.views.decorators.cache import cache_page
from django.views.decorators.csrf import csrf_exempt, csrf_protect
from django.views.decorators.http import require_http_methods

from apps.core.validation.input_sanitizer import InputSanitizer, InputValidator
from apps.core.validation.sql_protection import SQLInjectionProtection

from .cache_utils import CacheManager

# Setup logger
logger = logging.getLogger(__name__)


@csrf_protect
@require_http_methods(["POST", "GET"])
def performance_api(request):
    """
    Performance metrics collection endpoint with validation
    """
    if request.method == "POST":
        try:
            # Validate content type
            if not request.content_type.startswith("application/json"):
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Content-Type must be application/json",
                    },
                    status=400,
                )

            # Parse and validate JSON
            data = json.loads(request.body)

            # Validate required fields and sanitize data
            validated_data = validate_performance_data(data)
            if "error" in validated_data:
                return JsonResponse(
                    {"status": "error", "message": validated_data["error"]}, status=400
                )

            # Log performance metrics (safely)
            logger.info(
                f"Performance metrics received from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            # Store validated metrics (implement storage as needed)
            # For now, just acknowledge receipt
            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Performance metrics received",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )
        except Exception as e:
            logger.error(f"Error processing performance data: {e}")
            return JsonResponse(
                {"status": "error", "message": "Internal server error"}, status=500
            )

    # GET request - return current performance stats
    return JsonResponse(
        {"status": "ok", "server_time": datetime.now().isoformat(), "version": "1.0.0"}
    )


@cache_page(CacheManager.TIMEOUTS["short"])
@require_http_methods(["GET"])
def health_check(request):
    """
    Health check endpoint for monitoring
    """
    try:
        # Basic health check - database connectivity
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")

        return JsonResponse(
            {
                "status": "ok",
                "timestamp": datetime.now().isoformat(),
                "checks": {"database": "ok", "server": "running"},
            }
        )

    except Exception:
        return JsonResponse(
            {
                "status": "unhealthy",
                "timestamp": datetime.now().isoformat(),
                "error": "Database connection failed",
            },
            status=503,
        )


@csrf_protect
@require_http_methods(["POST", "GET"])
def notifications_api(request):
    """
    Push notifications handler with validation
    """
    logger = logging.getLogger(__name__)

    if request.method == "POST":
        try:
            # Validate content type
            if not request.content_type.startswith("application/json"):
                return JsonResponse(
                    {
                        "status": "error",
                        "message": "Content-Type must be application/json",
                    },
                    status=400,
                )

            data = json.loads(request.body)

            # Validate notification data
            validated_data = validate_notification_data(data)
            if "error" in validated_data:
                return JsonResponse(
                    {"status": "error", "message": validated_data["error"]}, status=400
                )

            # Log notification data (safely)
            logger.info(
                f"Notification data received from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            # Here you would implement actual notification sending
            # For now, just acknowledge receipt
            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Notification processed",
                    "timestamp": datetime.now().isoformat(),
                }
            )

        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )
        except Exception as e:
            logger.error(f"Error processing notification: {e}")
            return JsonResponse(
                {"status": "error", "message": "Internal server error"}, status=500
            )

    # GET request - return notification status
    return JsonResponse(
        {
            "status": "ok",
            "notifications_enabled": True,
            "timestamp": datetime.now().isoformat(),
        }
    )


@csrf_exempt
@require_http_methods(["GET", "POST"])
def analytics_api(request):
    """
    Analytics data endpoint - handles both GET and POST requests
    """
    if request.method == "GET":
        return JsonResponse(
            {
                "status": "ok",
                "message": "Analytics endpoint ready",
                "timestamp": datetime.now().isoformat(),
            }
        )
    elif request.method == "POST":
        try:
            # Handle POST requests for analytics data
            if request.content_type == "application/json":
                data = json.loads(request.body)
            else:
                data = request.POST.dict()

            # Log analytics data (implement your analytics logic here)
            logger.info(f"Analytics data received: {len(data)} fields")

            return JsonResponse(
                {
                    "status": "ok",
                    "message": "Analytics data processed",
                    "timestamp": datetime.now().isoformat(),
                }
            )
        except json.JSONDecodeError:
            return JsonResponse(
                {"status": "error", "message": "Invalid JSON data"}, status=400
            )
        except Exception as e:
            logger.error(f"Error processing analytics data: {e}")
            return JsonResponse(
                {"status": "error", "message": "Internal server error"}, status=500
            )


@require_http_methods(["GET"])
def cache_stats_api(request):
    """
    Cache statistics and monitoring endpoint
    """
    try:
        from .cache_utils import CacheMonitor

        # Get cache statistics
        stats = CacheMonitor.get_cache_stats()

        # Add additional runtime stats
        stats.update(
            {
                "timestamp": datetime.now().isoformat(),
                "cache_keys_info": {
                    "home_data_cached": cache.get("home_page_data") is not None,
                    "blog_data_cached": cache.get("blog_published_posts") is not None,
                    "tools_data_cached": cache.get("tools_visible_tools") is not None,
                },
            }
        )

        return JsonResponse({"status": "ok", "cache_stats": stats})

    except Exception as e:
        return JsonResponse(
            {
                "status": "error",
                "error": str(e),
                "timestamp": datetime.now().isoformat(),
            },
            status=500,
        )


def _validate_metric_type(data, allowed_metrics):
    """
    Validate metric_type field with enhanced security.
    Uses InputValidator for comprehensive validation.
    """
    metric_type = data.get("metric_type")
    if not metric_type:
        return (None, {"error": "metric_type is required"})

    # Check for SQL injection patterns
    is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(str(metric_type))
    if is_suspicious:
        logger.warning(f"Suspicious metric_type detected: {reason}")
        return (None, {"error": "Invalid metric_type format"})

    # Validate type and choice
    is_valid, error = InputValidator.validate_field_type(data, "metric_type", str)
    if not is_valid:
        return (None, {"error": error})

    is_valid, error = InputValidator.validate_choice(
        data, "metric_type", allowed_metrics
    )
    if not is_valid:
        return (None, {"error": error})

    # Sanitize and return
    sanitized = InputSanitizer.sanitize_text(metric_type, max_length=50)
    return (sanitized, None)


def _validate_metric_value(data):
    """
    Validate value field with enhanced security.
    Uses InputSanitizer for numeric validation.
    """
    value = data.get("value")
    if value is None:
        return (None, {"error": "value is required"})

    # Validate type and range using InputValidator
    is_valid, error = InputValidator.validate_field_type(data, "value", (int, float))
    if not is_valid:
        return (None, {"error": error})

    is_valid, error = InputValidator.validate_number_range(
        data, "value", min_value=0, max_value=1000000
    )
    if not is_valid:
        return (None, {"error": error})

    # Sanitize numeric value
    if isinstance(value, float):
        sanitized = InputSanitizer.sanitize_float(
            value, min_value=0.0, max_value=1000000.0
        )
    else:
        sanitized = InputSanitizer.sanitize_integer(
            value, min_value=0, max_value=1000000
        )

    return (sanitized, None)


def _validate_optional_url(data):
    """
    Validate optional URL field with enhanced security.
    Uses InputSanitizer for URL validation and sanitization.
    """
    url = data.get("url")
    if not url:
        return (None, None)

    # Validate type and length
    is_valid, error = InputValidator.validate_field_type(data, "url", str)
    if not is_valid:
        return (None, {"error": error})

    is_valid, error = InputValidator.validate_string_length(
        data, "url", max_length=2000
    )
    if not is_valid:
        return (None, {"error": error})

    # Sanitize and validate URL format
    sanitized_url = InputSanitizer.sanitize_url(url)
    if sanitized_url is None:
        return (None, {"error": "Invalid URL format. Must use http:// or https://"})

    return (sanitized_url, None)


def _validate_optional_fields(data):
    """
    Validate optional user_agent and viewport_size with enhanced security.
    Uses InputSanitizer for comprehensive sanitization.
    """
    validated = {}

    # Validate user_agent
    user_agent = data.get("user_agent")
    if user_agent:
        is_valid, error = InputValidator.validate_field_type(
            {"user_agent": user_agent}, "user_agent", str
        )
        if not is_valid:
            return (None, {"error": error})

        is_valid, error = InputValidator.validate_string_length(
            {"user_agent": user_agent}, "user_agent", max_length=500
        )
        if not is_valid:
            return (None, {"error": error})

        # Check for suspicious patterns
        is_suspicious, reason = SQLInjectionProtection.is_suspicious_input(user_agent)
        if is_suspicious:
            logger.warning(f"Suspicious user_agent detected: {reason}")
            return (None, {"error": "Invalid user_agent format"})

        sanitized_ua = InputSanitizer.sanitize_text(user_agent, max_length=500)
        validated["user_agent"] = sanitized_ua

    # Validate viewport_size
    viewport_size = data.get("viewport_size")
    if viewport_size:
        is_valid, error = InputValidator.validate_field_type(
            {"viewport_size": viewport_size}, "viewport_size", str
        )
        if not is_valid:
            return (None, {"error": error})

        is_valid, error = InputValidator.validate_pattern(
            {"viewport_size": viewport_size},
            "viewport_size",
            r"^\d{1,5}x\d{1,5}$",
            "WIDTHxHEIGHT format (e.g., 1920x1080)",
        )
        if not is_valid:
            return (None, {"error": error})

        validated["viewport_size"] = viewport_size

    return (validated, None)


def validate_performance_data(data):
    """
    Validate and sanitize performance metrics data.

    Refactored to reduce complexity: C:19 → C:6
    Uses validator functions for each field group.
    """
    if not isinstance(data, dict):
        return {"error": "Data must be a JSON object"}

    allowed_fields = {
        "metric_type",
        "value",
        "url",
        "user_agent",
        "viewport_size",
        "connection_type",
        "device_type",
        "additional_data",
        "timestamp",
    }

    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        return {"error": f'Unknown fields: {", ".join(unknown_fields)}'}

    allowed_metrics = {
        "lcp",
        "fid",
        "cls",
        "fcp",
        "ttfb",
        "long_task",
        "resource_load",
        "network_online",
        "network_offline",
        "cache_hit_rate",
    }

    validated_data = {}

    metric_type, error = _validate_metric_type(data, allowed_metrics)
    if error:
        return error
    validated_data["metric_type"] = metric_type

    value, error = _validate_metric_value(data)
    if error:
        return error
    validated_data["value"] = value

    url, error = _validate_optional_url(data)
    if error:
        return error
    if url:
        validated_data["url"] = url

    optional_fields, error = _validate_optional_fields(data)
    if error:
        return error
    validated_data.update(optional_fields)

    return validated_data


def _validate_subscription_data(subscription):
    """Validate push subscription object."""
    if not isinstance(subscription, dict):
        return (None, {"error": "subscription must be an object"})

    required_fields = {"endpoint", "keys"}
    if not all(field in subscription for field in required_fields):
        return (None, {"error": "subscription missing required fields"})

    endpoint = subscription.get("endpoint")
    if not isinstance(endpoint, str) or not endpoint.startswith("https://"):
        return (None, {"error": "subscription endpoint must be a valid HTTPS URL"})

    return (subscription, None)


def _validate_topics_list(topics):
    """Validate topics array."""
    if not isinstance(topics, list):
        return (None, {"error": "topics must be an array"})

    allowed_topics = {"blog_posts", "portfolio_updates", "general"}
    for topic in topics:
        if not isinstance(topic, str) or topic not in allowed_topics:
            return (
                None,
                {
                    "error": f'Invalid topic. Must be one of: {", ".join(allowed_topics)}'
                },
            )

    return (topics, None)


def _validate_notification_content(data):
    """Validate message and title fields."""
    validated = {}

    message = data.get("message")
    if message:
        if not isinstance(message, str) or len(message) > 1000:
            return (None, {"error": "message must be a string under 1000 characters"})
        validated["message"] = strip_tags(message)

    title = data.get("title")
    if title:
        if not isinstance(title, str) or len(title) > 200:
            return (None, {"error": "title must be a string under 200 characters"})
        validated["title"] = strip_tags(title)

    return (validated, None)


def validate_notification_data(data):
    """
    Validate and sanitize notification data.

    Refactored to reduce complexity: C:20 → C:6
    Uses validator functions for subscription, topics, and content.
    """
    if not isinstance(data, dict):
        return {"error": "Data must be a JSON object"}

    allowed_fields = {
        "subscription",
        "topics",
        "user_agent",
        "url",
        "endpoint",
        "message",
        "title",
        "icon",
        "badge",
    }

    unknown_fields = set(data.keys()) - allowed_fields
    if unknown_fields:
        return {"error": f'Unknown fields: {", ".join(unknown_fields)}'}

    validated_data = {}

    subscription = data.get("subscription")
    if subscription:
        sub_data, error = _validate_subscription_data(subscription)
        if error:
            return error
        validated_data["subscription"] = sub_data

    topics = data.get("topics")
    if topics:
        topics_data, error = _validate_topics_list(topics)
        if error:
            return error
        validated_data["topics"] = topics_data

    content, error = _validate_notification_content(data)
    if error:
        return error
    validated_data.update(content)

    return validated_data
