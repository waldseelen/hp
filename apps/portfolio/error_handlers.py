"""
ENHANCED ERROR HANDLING SYSTEM
================================================================================

Advanced error handling, logging, and monitoring system for the Django portfolio.
Provides structured error handling, custom error pages, and comprehensive logging.

FEATURES:
- Structured error logging with JSON format
- Custom error pages for 404, 500, 403, etc.
- Error monitoring and alerting integration
- Context-aware error responses
- Performance tracking for error pages
- User-friendly error messages with fallback content

USAGE:
- Import error handlers in views
- Use decorators for automatic error handling
- Configure custom error pages in settings
"""

import json
import logging
import traceback
from typing import Any, Dict

from django.conf import settings
from django.core.mail import mail_admins
from django.http import HttpResponse, JsonResponse
from django.shortcuts import render
from django.template import TemplateDoesNotExist
from django.utils import timezone
from django.views.decorators.csrf import requires_csrf_token

# Configure structured logger
logger = logging.getLogger(__name__)


class StructuredLogger:
    """Enhanced logger with structured JSON formatting"""

    @staticmethod
    def log_error(error: Exception, request=None, extra_context: Dict[str, Any] = None):
        """Log error with structured format and context"""
        error_data = {
            "timestamp": timezone.now().isoformat(),
            "error_type": type(error).__name__,
            "error_message": str(error),
            "traceback": traceback.format_exc(),
        }

        # Add request context if available
        if request:
            error_data.update(
                {
                    "request": {
                        "method": request.method,
                        "path": request.path,
                        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                        "ip_address": get_client_ip(request),
                        "user_id": (
                            getattr(request.user, "id", None)
                            if hasattr(request, "user")
                            else None
                        ),
                        "is_authenticated": (
                            getattr(request.user, "is_authenticated", False)
                            if hasattr(request, "user")
                            else False
                        ),
                    }
                }
            )

        # Add extra context
        if extra_context:
            error_data.update(extra_context)

        # Log the structured error
        logger.error(f"Application Error: {error}", extra=error_data)

        # Send to monitoring service (Sentry, etc.) if configured
        if hasattr(settings, "SENTRY_DSN") and settings.SENTRY_DSN:
            try:
                import sentry_sdk

                sentry_sdk.capture_exception(error)
            except ImportError:
                pass

        return error_data

    @staticmethod
    def log_performance_issue(view_name: str, execution_time: float, request=None):
        """Log performance issues for slow views"""
        if execution_time > 1.0:  # Log if over 1 second
            perf_data = {
                "timestamp": timezone.now().isoformat(),
                "view_name": view_name,
                "execution_time": execution_time,
                "severity": "warning" if execution_time < 2.0 else "critical",
            }

            if request:
                perf_data["request"] = {
                    "path": request.path,
                    "method": request.method,
                    "ip_address": get_client_ip(request),
                }

            logger.warning(f"Slow view detected: {view_name}", extra=perf_data)


def get_client_ip(request):
    """Get the real client IP address"""
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        ip = x_forwarded_for.split(",")[0].strip()
    else:
        ip = request.META.get("REMOTE_ADDR", "127.0.0.1")
    return ip


def safe_render(
    request,
    template_name: str,
    context: Dict[str, Any] = None,
    fallback_template: str = None,
):
    """Safe render with fallback template and error handling"""
    context = context or {}

    try:
        return render(request, template_name, context)
    except TemplateDoesNotExist:
        logger.warning(f"Template not found: {template_name}")

        # Try fallback template
        if fallback_template:
            try:
                return render(request, fallback_template, context)
            except TemplateDoesNotExist:
                pass

        # Ultimate fallback - minimal HTML response
        html_content = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Page Unavailable</title>
            <meta charset="utf-8">
            <meta name="viewport" content="width=device-width, initial-scale=1">
        </head>
        <body>
            <h1>Page Temporarily Unavailable</h1>
            <p>We're experiencing technical difficulties. Please try again later.</p>
        </body>
        </html>
        """
        return HttpResponse(html_content, status=503)


def handle_view_error(view_func):
    """Decorator for comprehensive view error handling"""

    def wrapper(request, *args, **kwargs):
        import time

        start_time = time.time()

        try:
            response = view_func(request, *args, **kwargs)

            # Log performance issues
            execution_time = time.time() - start_time
            if execution_time > 1.0:
                StructuredLogger.log_performance_issue(
                    view_func.__name__, execution_time, request
                )

            return response

        except Exception as e:
            # Log the error with full context
            error_data = StructuredLogger.log_error(
                e,
                request,
                extra_context={
                    "view_name": view_func.__name__,
                    "view_args": args,
                    "view_kwargs": kwargs,
                    "execution_time": time.time() - start_time,
                },
            )

            # Return appropriate error response
            if request.headers.get("Accept", "").startswith("application/json"):
                return JsonResponse(
                    {
                        "error": "An error occurred while processing your request.",
                        "error_id": error_data.get("timestamp"),
                        "status": "error",
                    },
                    status=500,
                )
            else:
                # Return user-friendly error page
                return safe_render(
                    request,
                    "errors/500.html",
                    {"error_id": error_data.get("timestamp")},
                    fallback_template="500.html",
                )

    return wrapper


# Custom Error Page Handlers
# ===========================


@requires_csrf_token
def custom_404_handler(request, exception=None):
    """Custom 404 error handler with enhanced logging"""
    error_data = {
        "timestamp": timezone.now().isoformat(),
        "path": request.path,
        "method": request.method,
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
        "referer": request.META.get("HTTP_REFERER", ""),
    }

    logger.warning(f"404 Not Found: {request.path}", extra=error_data)

    # Check if it's an API request
    if request.headers.get("Accept", "").startswith(
        "application/json"
    ) or request.path.startswith("/api/"):
        return JsonResponse(
            {
                "error": "Resource not found",
                "path": request.path,
                "status": "not_found",
            },
            status=404,
        )

    # Render custom 404 page
    return safe_render(
        request,
        "errors/404.html",
        {
            "request_path": request.path,
            "page_title": "Sayfa Bulunamadı",
        },
        fallback_template="404.html",
    )


@requires_csrf_token
def custom_500_handler(request):
    """Custom 500 error handler with comprehensive logging"""
    error_id = timezone.now().isoformat()

    error_data = {
        "timestamp": error_id,
        "path": request.path,
        "method": request.method,
        "ip_address": get_client_ip(request),
        "user_agent": request.META.get("HTTP_USER_AGENT", ""),
    }

    logger.error(f"500 Internal Server Error: {request.path}", extra=error_data)

    # Send email to admins in production
    if not settings.DEBUG:
        try:
            mail_admins(
                "Server Error (500)",
                f"Internal server error at {request.path}\nError ID: {error_id}\nTime: {timezone.now()}",
                fail_silently=True,
            )
        except Exception:
            # Email sending may fail, don't crash
            pass

    # Check if it's an API request
    if request.headers.get("Accept", "").startswith(
        "application/json"
    ) or request.path.startswith("/api/"):
        return JsonResponse(
            {
                "error": "Internal server error",
                "error_id": error_id,
                "status": "server_error",
            },
            status=500,
        )

    # Render custom 500 page
    return safe_render(
        request,
        "errors/500.html",
        {
            "error_id": error_id,
            "page_title": "Sunucu Hatası",
        },
        fallback_template="500.html",
    )


@requires_csrf_token
def custom_403_handler(request, exception=None):
    """Custom 403 forbidden error handler"""
    error_data = {
        "timestamp": timezone.now().isoformat(),
        "path": request.path,
        "method": request.method,
        "ip_address": get_client_ip(request),
        "user_id": (
            getattr(request.user, "id", None) if hasattr(request, "user") else None
        ),
    }

    logger.warning(f"403 Forbidden: {request.path}", extra=error_data)

    # Check if it's an API request
    if request.headers.get("Accept", "").startswith(
        "application/json"
    ) or request.path.startswith("/api/"):
        return JsonResponse(
            {"error": "Access forbidden", "path": request.path, "status": "forbidden"},
            status=403,
        )

    # Render custom 403 page
    return safe_render(
        request,
        "errors/403.html",
        {
            "page_title": "Erişim Engellendi",
        },
        fallback_template="403.html",
    )


@requires_csrf_token
def custom_400_handler(request, exception=None):
    """Custom 400 bad request error handler"""
    error_data = {
        "timestamp": timezone.now().isoformat(),
        "path": request.path,
        "method": request.method,
        "ip_address": get_client_ip(request),
    }

    logger.warning(f"400 Bad Request: {request.path}", extra=error_data)

    # Check if it's an API request
    if request.headers.get("Accept", "").startswith(
        "application/json"
    ) or request.path.startswith("/api/"):
        return JsonResponse(
            {"error": "Bad request", "path": request.path, "status": "bad_request"},
            status=400,
        )

    # Render custom 400 page
    return safe_render(
        request,
        "errors/400.html",
        {
            "page_title": "Geçersiz İstek",
        },
        fallback_template="400.html",
    )


# Error Monitoring and Alerting
# ==============================


class ErrorMonitor:
    """Error monitoring and alerting system"""

    @staticmethod
    def should_alert(error_type: str, count: int = 1) -> bool:
        """Determine if error should trigger alert"""
        alert_thresholds = {
            "DatabaseError": 1,  # Immediate alert
            "ConnectionError": 3,  # Alert after 3 occurrences
            "TemplateDoesNotExist": 5,  # Alert after 5 occurrences
            "PermissionDenied": 10,  # Alert after 10 occurrences
        }

        threshold = alert_thresholds.get(error_type, 5)  # Default threshold
        return count >= threshold

    @staticmethod
    def send_alert(error_data: Dict[str, Any]):
        """Send alert notification"""
        try:
            # Send email alert
            if hasattr(settings, "ADMINS") and settings.ADMINS:
                subject = (
                    f"Error Alert: {error_data.get('error_type', 'Unknown Error')}"
                )
                message = f"""
                Error Type: {error_data.get('error_type')}
                Error Message: {error_data.get('error_message')}
                Path: {error_data.get('request', {}).get('path', 'Unknown')}
                Time: {error_data.get('timestamp')}
                IP: {error_data.get('request', {}).get('ip_address', 'Unknown')}

                Full Details:
                {json.dumps(error_data, indent=2)}
                """

                mail_admins(subject, message, fail_silently=True)

            # Integration with external monitoring services
            # (Slack, Discord, PagerDuty, etc.)

        except Exception as e:
            logger.error(f"Failed to send error alert: {e}")


# Utility Functions
# =================


def create_error_context(error: Exception, request=None) -> Dict[str, Any]:
    """Create standardized error context for templates"""
    return {
        "error_type": type(error).__name__,
        "error_message": str(error),
        "timestamp": timezone.now(),
        "debug_mode": settings.DEBUG,
        "support_email": getattr(settings, "SUPPORT_EMAIL", "support@example.com"),
        "request_path": getattr(request, "path", "") if request else "",
    }


def is_api_request(request) -> bool:
    """Check if request is for API endpoint"""
    return (
        request.headers.get("Accept", "").startswith("application/json")
        or request.path.startswith("/api/")
        or "json" in request.headers.get("Content-Type", "").lower()
    )
