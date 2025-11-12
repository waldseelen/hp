"""
Rate Limiting Module
===================

Implements comprehensive rate limiting for all endpoints with
different limits based on endpoint sensitivity.
"""

import hashlib
import logging
import time

from django.conf import settings
from django.core.cache import cache
from django.http import JsonResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class RateLimitMiddleware(MiddlewareMixin):
    """
    Global rate limiting middleware with configurable limits per endpoint pattern.
    """

    # Define rate limits for different endpoint patterns
    # Format: (pattern, requests_per_minute, burst_size)
    RATE_LIMITS = [
        # Authentication endpoints - very strict
        (r"^/admin/login/", 5, 10),
        (r"^/login/", 10, 20),
        (r"^/register/", 5, 10),
        (r"^/password-reset/", 3, 5),
        # API endpoints - moderate
        (r"^/api/contact/", 5, 10),
        (r"^/api/chat/", 30, 60),
        (r"^/api/search/", 60, 120),
        (r"^/api/performance/", 100, 200),
        (r"^/api/notifications/", 30, 60),
        # Static and media files - lenient
        (r"^/static/", 500, 1000),
        (r"^/media/", 500, 1000),
        # Blog and content - moderate
        (r"^/blog/", 100, 200),
        (r"^/tools/", 100, 200),
        # Security reporting endpoints - moderate
        (r"^/api/security/", 20, 40),
        # Short URLs - strict to prevent abuse
        (r"^/s/", 30, 60),
        # Default for all other endpoints
        (r".*", 200, 400),
    ]

    def get_client_ip(self, request):
        """Get the client's IP address from the request."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip

    def get_rate_limit_key(self, request):
        """Generate a unique key for rate limiting."""
        ip = self.get_client_ip(request)
        path = request.path
        user_agent = request.META.get("HTTP_USER_AGENT", "")

        # Create a unique identifier combining IP, path, and user agent
        identifier = f"{ip}:{path}:{user_agent}"
        key_hash = hashlib.md5(identifier.encode(), usedforsecurity=False).hexdigest()
        return f"ratelimit:{key_hash}"

    def get_limit_for_path(self, path):
        """Get the rate limit for a given path."""
        import re

        for pattern, limit, burst in self.RATE_LIMITS:
            if re.match(pattern, path):
                return limit, burst

        # Default limit if no pattern matches
        return 200, 400

    def check_rate_limit(self, request):
        """
        Check if the request exceeds the rate limit.
        Returns (is_allowed, remaining_requests, reset_time)
        """
        key = self.get_rate_limit_key(request)
        limit, burst = self.get_limit_for_path(request.path)

        # TODO: Use timestamp for advanced rate limiting logic
        _now = time.time()  # noqa: F841
        minute_key = f"{key}:minute"
        burst_key = f"{key}:burst"

        # Check minute-based rate limit
        minute_count = cache.get(minute_key, 0)
        burst_count = cache.get(burst_key, 0)

        if minute_count >= limit:
            # Rate limit exceeded for the minute
            return False, 0, 60

        if burst_count >= burst:
            # Burst limit exceeded
            return False, 0, 10

        # Increment counters
        cache.set(minute_key, minute_count + 1, 60)  # Reset after 60 seconds
        cache.set(burst_key, burst_count + 1, 10)  # Reset after 10 seconds

        remaining = limit - minute_count - 1
        return True, remaining, 60

    def process_request(self, request):
        """Process the request and apply rate limiting."""
        # Skip rate limiting for debug mode if configured
        if settings.DEBUG and not getattr(
            settings, "ENABLE_RATE_LIMIT_IN_DEBUG", False
        ):
            return None

        # Check rate limit
        is_allowed, remaining, reset_time = self.check_rate_limit(request)

        if not is_allowed:
            # Log rate limit violation
            logger.warning(
                "Rate limit exceeded",
                extra={
                    "ip": self.get_client_ip(request),
                    "path": request.path,
                    "method": request.method,
                    "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                },
            )

            # Return rate limit error response
            response = JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please slow down.",
                    "retry_after": reset_time,
                },
                status=429,
            )

            # Add rate limit headers
            response["X-RateLimit-Limit"] = str(
                self.get_limit_for_path(request.path)[0]
            )
            response["X-RateLimit-Remaining"] = "0"
            response["X-RateLimit-Reset"] = str(int(time.time() + reset_time))
            response["Retry-After"] = str(reset_time)

            return response

        # Add rate limit info to request for later use
        request.rate_limit_remaining = remaining
        request.rate_limit_reset = reset_time

        return None

    def process_response(self, request, response):
        """Add rate limit headers to successful responses."""
        if hasattr(request, "rate_limit_remaining"):
            limit, _ = self.get_limit_for_path(request.path)
            response["X-RateLimit-Limit"] = str(limit)
            response["X-RateLimit-Remaining"] = str(request.rate_limit_remaining)
            response["X-RateLimit-Reset"] = str(
                int(time.time() + request.rate_limit_reset)
            )

        return response


class APIRateLimitMiddleware(MiddlewareMixin):
    """
    Specialized rate limiting for API endpoints with user-based limits.
    """

    def process_request(self, request):
        """Apply API-specific rate limiting."""
        # Only apply to API endpoints
        if not request.path.startswith("/api/"):
            return None

        # Get user identifier (authenticated user ID or IP)
        if request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
            # Higher limits for authenticated users
            limit = 1000
            window = 3600  # 1 hour
        else:
            # Use IP for anonymous users
            ip = request.META.get("REMOTE_ADDR", "")
            identifier = f"ip:{ip}"
            limit = 100
            window = 3600  # 1 hour

        # Create cache key
        cache_key = f"api_ratelimit:{identifier}"

        # Get current count
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            logger.warning(f"API rate limit exceeded for {identifier}")

            response = JsonResponse(
                {
                    "error": "API rate limit exceeded",
                    "message": f"Maximum {limit} requests per hour exceeded",
                    "retry_after": window,
                },
                status=429,
            )

            response["X-API-RateLimit-Limit"] = str(limit)
            response["X-API-RateLimit-Remaining"] = "0"
            response["Retry-After"] = str(window)

            return response

        # Increment counter
        cache.set(cache_key, current_count + 1, window)

        # Store for response headers
        request.api_rate_limit_remaining = limit - current_count - 1
        request.api_rate_limit_limit = limit

        return None

    def process_response(self, request, response):
        """Add API rate limit headers."""
        if hasattr(request, "api_rate_limit_remaining"):
            response["X-API-RateLimit-Limit"] = str(request.api_rate_limit_limit)
            response["X-API-RateLimit-Remaining"] = str(
                request.api_rate_limit_remaining
            )

        return response


def ratelimit_view(key="ip", rate="10/m", method="ALL", block=True):
    """
    Decorator for rate limiting individual views.

    Usage:
        @ratelimit_view(key='ip', rate='5/m')
        def my_view(request):
            ...
    """

    def decorator(view_func):
        def wrapped_view(request, *args, **kwargs):
            # Parse rate string (e.g., "10/m" = 10 per minute)
            import re

            match = re.match(r"(\d+)/([mhd])", rate)
            if not match:
                return view_func(request, *args, **kwargs)

            limit = int(match.group(1))
            period = match.group(2)

            # Convert period to seconds
            periods = {"m": 60, "h": 3600, "d": 86400}
            window = periods.get(period, 60)

            # Check method
            if method != "ALL" and request.method != method:
                return view_func(request, *args, **kwargs)

            # Get identifier based on key
            if key == "ip":
                identifier = request.META.get("REMOTE_ADDR", "")
            elif key == "user":
                identifier = (
                    str(request.user.id)
                    if request.user.is_authenticated
                    else request.META.get("REMOTE_ADDR", "")
                )
            else:
                identifier = request.META.get("REMOTE_ADDR", "")

            # Create cache key
            cache_key = f"view_ratelimit:{view_func.__name__}:{identifier}"

            # Check rate limit
            current_count = cache.get(cache_key, 0)

            if current_count >= limit and block:
                return JsonResponse(
                    {
                        "error": "Rate limit exceeded",
                        "message": f"Maximum {limit} requests per {period} exceeded",
                    },
                    status=429,
                )

            # Increment counter
            cache.set(cache_key, current_count + 1, window)

            # Call the view
            response = view_func(request, *args, **kwargs)

            # Add rate limit headers
            response["X-View-RateLimit-Limit"] = str(limit)
            response["X-View-RateLimit-Remaining"] = str(
                max(0, limit - current_count - 1)
            )

            return response

        return wrapped_view

    return decorator
