"""
API Rate Limiting Middleware
============================

Provides API-specific rate limiting with:
- Stricter limits for API endpoints (60 req/min authenticated, 20 req/min anonymous)
- Per-endpoint rate limits (read vs write operations)
- Rate limit by API key + IP combination
- Graceful degradation with retry-after headers
"""

import logging
import time
from typing import Optional, Tuple

from django.core.cache import cache
from django.http import JsonResponse
from django.utils import timezone

logger = logging.getLogger(__name__)


class APIRateLimitMiddleware:
    """
    Rate limiting middleware specifically for API endpoints
    """

    # API-specific rate limits (more restrictive than web)
    RATE_LIMITS = {
        "authenticated": {
            "requests": 60,
            "window": 60,  # 60 requests per minute
        },
        "anonymous": {
            "requests": 20,
            "window": 60,  # 20 requests per minute
        },
        "api_key": {
            "requests": 1000,
            "window": 3600,  # 1000 requests per hour
        },
    }

    # Per-endpoint rate limits
    ENDPOINT_LIMITS = {
        "/api/v1/search/": {"requests": 30, "window": 60},  # 30/min
        "/api/v1/analytics/": {"requests": 100, "window": 60},  # 100/min
        "/api/v1/performance/": {"requests": 120, "window": 60},  # 120/min
        "/api/v1/auth/token/": {"requests": 5, "window": 300},  # 5 per 5min
        "/api/v1/auth/refresh/": {"requests": 10, "window": 300},  # 10 per 5min
    }

    # Exempt endpoints (no rate limiting)
    EXEMPT_ENDPOINTS = [
        "/api/v1/health/",
        "/api/v1/status/",
    ]

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Check if endpoint is API endpoint
        if not self._is_api_endpoint(request.path):
            return self.get_response(request)

        # Check if endpoint is exempt
        if self._is_exempt_endpoint(request.path):
            return self.get_response(request)

        # Check rate limit
        is_allowed, retry_after = self._check_rate_limit(request)

        if not is_allowed:
            logger.warning(
                f"API rate limit exceeded for {request.META.get('REMOTE_ADDR')} "
                f"on {request.path}"
            )

            response = JsonResponse(
                {
                    "error": "Rate limit exceeded",
                    "message": "Too many requests. Please try again later.",
                    "retry_after": retry_after,
                },
                status=429,
            )
            response["Retry-After"] = retry_after
            response["X-RateLimit-Limit"] = self._get_limit_for_request(request)[0]
            response["X-RateLimit-Remaining"] = 0
            response["X-RateLimit-Reset"] = int(time.time() + retry_after)

            return response

        # Add rate limit headers to response
        response = self.get_response(request)
        self._add_rate_limit_headers(response, request)

        return response

    def _is_api_endpoint(self, path: str) -> bool:
        """
        Check if path is an API endpoint
        """
        return path.startswith("/api/")

    def _is_exempt_endpoint(self, path: str) -> bool:
        """
        Check if endpoint is exempt from rate limiting
        """
        return any(path.startswith(exempt) for exempt in self.EXEMPT_ENDPOINTS)

    def _check_rate_limit(self, request) -> Tuple[bool, int]:
        """
        Check if request is within rate limit

        Returns: (is_allowed, retry_after_seconds)
        """
        # Get rate limit configuration
        limit, window = self._get_limit_for_request(request)

        # Get cache key
        cache_key = self._get_cache_key(request)

        # Get current request count
        current_count = cache.get(cache_key, 0)

        if current_count >= limit:
            # Rate limit exceeded - calculate retry_after
            ttl = cache.ttl(cache_key)
            retry_after = max(ttl, window) if ttl else window
            return (False, retry_after)

        # Increment counter
        if current_count == 0:
            # First request in window - set with expiry
            cache.set(cache_key, 1, timeout=window)
        else:
            # Increment existing counter
            cache.incr(cache_key)

        return (True, 0)

    def _get_limit_for_request(self, request) -> Tuple[int, int]:
        """
        Get rate limit for request (requests, window)
        """
        # Check endpoint-specific limits first
        for endpoint, limit_config in self.ENDPOINT_LIMITS.items():
            if request.path.startswith(endpoint):
                return (limit_config["requests"], limit_config["window"])

        # Check if request uses API key
        if hasattr(request, "auth") and hasattr(request.auth, "rate_limit_per_hour"):
            # API key with custom rate limit
            return (request.auth.rate_limit_per_hour, 3600)

        # Default limits based on authentication
        if request.user and request.user.is_authenticated:
            config = self.RATE_LIMITS["authenticated"]
        else:
            config = self.RATE_LIMITS["anonymous"]

        return (config["requests"], config["window"])

    def _get_cache_key(self, request) -> str:
        """
        Generate cache key for rate limiting
        """
        # Use API key if available
        if hasattr(request, "auth") and hasattr(request.auth, "key_hash"):
            identifier = f"api_key:{request.auth.key_hash}"
        # Use user ID if authenticated
        elif request.user and request.user.is_authenticated:
            identifier = f"user:{request.user.id}"
        # Use IP for anonymous
        else:
            ip_address = self._get_client_ip(request)
            identifier = f"ip:{ip_address}"

        # Include endpoint in key for endpoint-specific limits
        endpoint_key = request.path.split("?")[0]  # Remove query params

        return f"api_rate_limit:{identifier}:{endpoint_key}"

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip

    def _add_rate_limit_headers(self, response, request) -> None:
        """
        Add rate limit headers to response
        """
        limit, window = self._get_limit_for_request(request)
        cache_key = self._get_cache_key(request)
        current_count = cache.get(cache_key, 0)
        remaining = max(0, limit - current_count)

        response["X-RateLimit-Limit"] = limit
        response["X-RateLimit-Remaining"] = remaining
        response["X-RateLimit-Reset"] = int(time.time() + window)


class DDoSProtectionMiddleware:
    """
    Additional DDoS protection for API endpoints
    """

    # Block IP if more than this many requests in short window
    DDOS_THRESHOLD = 200  # requests
    DDOS_WINDOW = 60  # seconds
    BLOCK_DURATION = 900  # 15 minutes

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        # Only check API endpoints
        if not request.path.startswith("/api/"):
            return self.get_response(request)

        ip_address = self._get_client_ip(request)

        # Check if IP is blocked
        if self._is_blocked(ip_address):
            logger.warning(f"Blocked DDoS attempt from {ip_address}")
            return JsonResponse(
                {
                    "error": "Access denied",
                    "message": "Your IP has been temporarily blocked due to suspicious activity.",
                },
                status=403,
            )

        # Check if IP exceeds DDoS threshold
        if self._check_ddos_threshold(ip_address):
            self._block_ip(ip_address)
            logger.error(f"DDoS detected from {ip_address} - IP blocked")
            return JsonResponse(
                {
                    "error": "Too many requests",
                    "message": "Excessive request rate detected. Your IP has been temporarily blocked.",
                },
                status=429,
            )

        return self.get_response(request)

    def _get_client_ip(self, request) -> str:
        """
        Get client IP address
        """
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR", "unknown")
        return ip

    def _is_blocked(self, ip_address: str) -> bool:
        """
        Check if IP is currently blocked
        """
        block_key = f"ddos_block:{ip_address}"
        return cache.get(block_key, False)

    def _check_ddos_threshold(self, ip_address: str) -> bool:
        """
        Check if IP exceeds DDoS threshold
        """
        ddos_key = f"ddos_check:{ip_address}"
        request_count = cache.get(ddos_key, 0)

        if request_count >= self.DDOS_THRESHOLD:
            return True

        # Increment counter
        if request_count == 0:
            cache.set(ddos_key, 1, timeout=self.DDOS_WINDOW)
        else:
            cache.incr(ddos_key)

        return False

    def _block_ip(self, ip_address: str) -> None:
        """
        Block IP address for BLOCK_DURATION
        """
        block_key = f"ddos_block:{ip_address}"
        cache.set(block_key, True, timeout=self.BLOCK_DURATION)
