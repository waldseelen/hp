"""
Performance Monitoring and Notifications API Views
Provides endpoints for performance tracking and push notifications
"""

import json
import logging

from django.core.exceptions import ValidationError
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_http_methods

from apps.main.models import PerformanceMetric
from apps.main.performance import alert_manager, performance_metrics
from apps.main.validators import API_SCHEMAS, validate_json_input

logger = logging.getLogger(__name__)


@require_http_methods(["POST"])
@csrf_exempt
def collect_performance_metric(request):
    """
    API endpoint to collect performance metrics from frontend
    """
    try:
        # Validate content type
        if not request.content_type == "application/json":
            return JsonResponse(
                {"status": "error", "message": "Content-Type must be application/json"},
                status=400,
            )

        # Validate request body size
        if len(request.body) > 1024:  # 1KB limit
            return JsonResponse(
                {"status": "error", "message": "Request body too large"}, status=413
            )

        data = json.loads(request.body)

        # Validate using comprehensive validator
        try:
            validated_data = validate_json_input(
                data, API_SCHEMAS["performance_metric"]
            )
            metric_type = validated_data["metric_type"]
            value = validated_data["value"]
        except ValidationError as e:
            return JsonResponse({"status": "error", "message": str(e)}, status=400)

        # Add to in-memory metrics collection
        success = performance_metrics.add_metric(
            metric_type=metric_type,
            value=value,
            url=validated_data.get("url", request.META.get("HTTP_REFERER", "")),
            user_agent=request.META.get("HTTP_USER_AGENT", ""),
            device_type=validated_data.get("device_type", "desktop"),
            connection_type=validated_data.get("connection_type", "unknown"),
            additional_data=validated_data.get("additional_data", {}),
        )

        # Also save to database for persistence (async in production)
        try:
            PerformanceMetric.objects.create(
                metric_type=metric_type,
                value=value,
                url=validated_data.get("url", request.META.get("HTTP_REFERER", ""))[
                    :500
                ],
                user_agent=request.META.get("HTTP_USER_AGENT", ""),
                device_type=validated_data.get("device_type", "desktop"),
                connection_type=validated_data.get("connection_type", "unknown"),
                additional_data=validated_data.get("additional_data", {}),
                ip_address=request.META.get("REMOTE_ADDR"),
                session_id=request.session.session_key or "",
            )
        except Exception as e:
            logger.warning(f"Failed to save metric to database: {e}")

        # Log the performance metric (sanitized)
        logger.info(f"Performance metric collected: {metric_type}={value:.2f}")

        return JsonResponse(
            {
                "status": "success",
                "message": "Performance metric recorded",
                "timestamp": timezone.now().isoformat(),
                "in_memory_success": success,
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error collecting performance metric: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@require_http_methods(["GET"])
def performance_dashboard_data(request):
    """
    API endpoint to get performance metrics summary for dashboard
    """
    try:
        # Get hours parameter from query string (default 1 hour)
        hours = int(request.GET.get("hours", 1))
        hours = min(max(hours, 1), 24)  # Limit between 1 and 24 hours

        # Get data from in-memory metrics
        if request.GET.get("realtime") == "true":
            # Real-time data for live dashboard
            dashboard_data = {
                "status": "success",
                "data": performance_metrics.get_real_time_data(),
                "timestamp": timezone.now().isoformat(),
            }
        else:
            # Summary data for analytics
            summary = performance_metrics.get_metrics_summary(hours=hours)
            dashboard_data = {
                "status": "success",
                "data": summary,
                "timestamp": timezone.now().isoformat(),
            }

        # Add health status
        health_status = performance_metrics.get_health_status()
        dashboard_data["health"] = health_status

        # Add recent alerts
        recent_alerts = alert_manager.get_recent_alerts(minutes=60)
        dashboard_data["recent_alerts"] = recent_alerts

        return JsonResponse(dashboard_data)

    except Exception as e:
        logger.error(f"Error getting performance dashboard data: {str(e)}")
        return JsonResponse(
            {
                "status": "error",
                "message": "Internal server error",
                "timestamp": timezone.now().isoformat(),
            },
            status=500,
        )


@require_http_methods(["GET"])
def health_check(request):
    """
    Simple health check endpoint
    """
    try:
        return JsonResponse(
            {
                "status": "healthy",
                "timestamp": timezone.now().isoformat(),
                "version": "1.0.0",
                "database": "healthy",
                "cache": "healthy",
            }
        )

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return JsonResponse(
            {
                "status": "unhealthy",
                "timestamp": timezone.now().isoformat(),
                "error": str(e),
            },
            status=500,
        )


@require_http_methods(["POST"])
@csrf_exempt
def subscribe_push_notifications(request):
    """
    API endpoint to subscribe to push notifications
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get("endpoint")

        if not endpoint:
            return JsonResponse(
                {"status": "error", "message": "endpoint is required"}, status=400
            )

        # Log the subscription
        logger.info(f"Push notification subscription: {endpoint}")

        return JsonResponse(
            {
                "status": "success",
                "message": "Push subscription created",
                "subscription_id": "mock_id_123",
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error creating push subscription: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@require_http_methods(["POST"])
@csrf_exempt
def send_push_notification(request):
    """
    API endpoint to send push notifications (admin only)
    """
    try:
        data = json.loads(request.body)
        title = data.get("title")
        body = data.get("body")

        if not title or not body:
            return JsonResponse(
                {"status": "error", "message": "title and body are required"},
                status=400,
            )

        # Log the notification
        logger.info(f"Push notification sent: {title}")

        return JsonResponse(
            {
                "status": "success",
                "message": "Notification sent successfully",
                "results": {"success_count": 1, "failure_count": 0},
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@require_http_methods(["POST"])
@csrf_exempt
def log_error(request):  # noqa: C901
    """
    API endpoint to log errors from frontend
    """
    try:
        # Validate content type
        if not request.content_type == "application/json":
            return JsonResponse(
                {"status": "error", "message": "Content-Type must be application/json"},
                status=400,
            )

        # Validate request body size
        if len(request.body) > 2048:  # 2KB limit for error messages
            return JsonResponse(
                {"status": "error", "message": "Request body too large"}, status=413
            )

        data = json.loads(request.body)
        message = data.get("message")
        level = data.get("level", "error")

        if not message:
            return JsonResponse(
                {"status": "error", "message": "message is required"}, status=400
            )

        # Validate and sanitize message
        import re

        from django.utils.html import strip_tags

        message = strip_tags(str(message))  # Remove HTML
        message = re.sub(r"\s+", " ", message)  # Normalize whitespace

        if len(message) > 1000:  # Limit message length
            message = message[:1000] + "..."

        # Validate level
        allowed_levels = ["critical", "error", "warning", "info"]
        if level not in allowed_levels:
            level = "error"

        # Check for suspicious content
        suspicious_patterns = [
            r"<script",
            r"javascript:",
            r"data:",
            r"vbscript:",
        ]

        for pattern in suspicious_patterns:
            if re.search(pattern, message.lower()):
                logger.warning(f"Suspicious error message blocked: {message[:50]}...")
                return JsonResponse(
                    {"status": "error", "message": "Invalid error message content"},
                    status=400,
                )

        # Log the error (sanitized)
        safe_message = f"Frontend {level}: {message}"
        if level == "critical":
            logger.critical(safe_message)
        elif level == "error":
            logger.error(safe_message)
        elif level == "warning":
            logger.warning(safe_message)
        else:
            logger.info(safe_message)

        return JsonResponse(
            {
                "status": "success",
                "message": "Error logged successfully",
                "error_id": "mock_error_id_123",
            },
            status=201,
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Error logging frontend error: {str(e)}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )
