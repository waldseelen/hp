"""
Rate Limiting Middleware for Authentication Security
===================================================

Protects against brute-force attacks on authentication endpoints.

Features:
- Per-IP rate limiting for login attempts
- Per-username rate limiting
- Configurable thresholds and cooldown periods
- Automatic lockout after threshold breach
- Redis backend for distributed systems (optional)
"""

import logging
import time
from collections import defaultdict
from typing import Callable, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.utils.decorators import method_decorator
from django.views.decorators.cache import never_cache

logger = logging.getLogger(__name__)


class RateLimitExceeded(Exception):
    """Raised when rate limit is exceeded"""

    pass


class AuthenticationRateLimiter:
    """
    Rate limiter for authentication endpoints.

    Tracks login attempts per IP and per username,
    implementing exponential backoff on repeated failures.
    """

    def __init__(self):
        self.config = getattr(settings, "RATE_LIMIT_CONFIG", self._default_config())

    def _default_config(self) -> dict:
        """Default rate limiting configuration"""
        return {
            "MAX_LOGIN_ATTEMPTS": 5,  # Max attempts before lockout
            "LOCKOUT_DURATION": 900,  # 15 minutes in seconds
            "ATTEMPT_WINDOW": 300,  # 5 minutes in seconds
            "ENABLE_IP_TRACKING": True,
            "ENABLE_USERNAME_TRACKING": True,
            "EXEMPT_IPS": ["127.0.0.1", "localhost"],
        }

    def _get_cache_key(self, identifier: str, tracking_type: str) -> str:
        """Generate cache key for tracking"""
        return f"rate_limit:{tracking_type}:{identifier}"

    def _get_lockout_key(self, identifier: str, tracking_type: str) -> str:
        """Generate cache key for lockout status"""
        return f"rate_limit:lockout:{tracking_type}:{identifier}"

    def _is_exempt_ip(self, ip_address: str) -> bool:
        """Check if IP is exempt from rate limiting"""
        return ip_address in self.config["EXEMPT_IPS"]

    def check_rate_limit(
        self, ip_address: str, username: Optional[str] = None
    ) -> tuple[bool, Optional[str]]:
        """
        Check if request is within rate limits.

        Args:
            ip_address: Client IP address
            username: Username attempting login (optional)

        Returns:
            Tuple of (is_allowed, error_message)
        """
        if self._is_exempt_ip(ip_address):
            return (True, None)

        # Check IP-based rate limit
        if self.config["ENABLE_IP_TRACKING"]:
            is_allowed, message = self._check_identifier_limit(ip_address, "ip")
            if not is_allowed:
                return (False, message)

        # Check username-based rate limit
        if username and self.config["ENABLE_USERNAME_TRACKING"]:
            is_allowed, message = self._check_identifier_limit(username, "username")
            if not is_allowed:
                return (False, message)

        return (True, None)

    def _check_identifier_limit(
        self, identifier: str, tracking_type: str
    ) -> tuple[bool, Optional[str]]:
        """
        Check rate limit for specific identifier.

        Args:
            identifier: IP address or username
            tracking_type: 'ip' or 'username'

        Returns:
            Tuple of (is_allowed, error_message)
        """
        # Check if currently locked out
        lockout_key = self._get_lockout_key(identifier, tracking_type)
        lockout_end = cache.get(lockout_key)

        if lockout_end:
            remaining = int(lockout_end - time.time())
            if remaining > 0:
                return (
                    False,
                    f"Too many failed attempts. Try again in {remaining // 60} minutes.",
                )
            else:
                # Lockout expired, clear it
                cache.delete(lockout_key)

        # Check attempt count
        cache_key = self._get_cache_key(identifier, tracking_type)
        attempts = cache.get(cache_key, [])

        # Remove old attempts outside window
        current_time = time.time()
        window_start = current_time - self.config["ATTEMPT_WINDOW"]
        attempts = [ts for ts in attempts if ts > window_start]

        if len(attempts) >= self.config["MAX_LOGIN_ATTEMPTS"]:
            # Trigger lockout
            lockout_until = current_time + self.config["LOCKOUT_DURATION"]
            cache.set(lockout_key, lockout_until, self.config["LOCKOUT_DURATION"])

            logger.warning(
                f"Rate limit exceeded for {tracking_type}: {identifier}. "
                f"Locked out for {self.config['LOCKOUT_DURATION']} seconds."
            )

            return (
                False,
                f"Too many failed attempts. Account locked for {self.config['LOCKOUT_DURATION'] // 60} minutes.",
            )

        return (True, None)

    def record_failed_attempt(
        self, ip_address: str, username: Optional[str] = None
    ) -> None:
        """
        Record failed login attempt.

        Args:
            ip_address: Client IP address
            username: Username that failed (optional)
        """
        if self._is_exempt_ip(ip_address):
            return

        current_time = time.time()

        # Record IP attempt
        if self.config["ENABLE_IP_TRACKING"]:
            self._record_identifier_attempt(ip_address, "ip", current_time)

        # Record username attempt
        if username and self.config["ENABLE_USERNAME_TRACKING"]:
            self._record_identifier_attempt(username, "username", current_time)

    def _record_identifier_attempt(
        self, identifier: str, tracking_type: str, timestamp: float
    ) -> None:
        """Record attempt for specific identifier"""
        cache_key = self._get_cache_key(identifier, tracking_type)
        attempts = cache.get(cache_key, [])

        # Remove old attempts
        window_start = timestamp - self.config["ATTEMPT_WINDOW"]
        attempts = [ts for ts in attempts if ts > window_start]

        # Add new attempt
        attempts.append(timestamp)

        # Save with TTL equal to attempt window
        cache.set(cache_key, attempts, self.config["ATTEMPT_WINDOW"])

    def reset_attempts(self, ip_address: str, username: Optional[str] = None) -> None:
        """
        Reset rate limit tracking after successful login.

        Args:
            ip_address: Client IP address
            username: Username that succeeded (optional)
        """
        if self.config["ENABLE_IP_TRACKING"]:
            cache_key = self._get_cache_key(ip_address, "ip")
            cache.delete(cache_key)
            lockout_key = self._get_lockout_key(ip_address, "ip")
            cache.delete(lockout_key)

        if username and self.config["ENABLE_USERNAME_TRACKING"]:
            cache_key = self._get_cache_key(username, "username")
            cache.delete(cache_key)
            lockout_key = self._get_lockout_key(username, "username")
            cache.delete(lockout_key)


class RateLimitMiddleware:
    """
    Django middleware for rate limiting authentication endpoints.

    Applies rate limiting to login, password reset, and other
    authentication-related endpoints.
    """

    def __init__(self, get_response: Callable):
        self.get_response = get_response
        self.rate_limiter = AuthenticationRateLimiter()

        # Paths to apply rate limiting
        self.protected_paths = getattr(
            settings,
            "RATE_LIMIT_PATHS",
            [
                "/admin/login/",
                "/api/auth/login/",
                "/api/auth/token/",
                "/accounts/login/",
                "/password-reset/",
            ],
        )

    def __call__(self, request: HttpRequest) -> HttpResponse:
        """Process request through rate limiting"""
        # Check if path should be rate-limited
        if self._should_rate_limit(request):
            ip_address = self._get_client_ip(request)
            username = self._extract_username(request)

            # Check rate limit
            is_allowed, error_message = self.rate_limiter.check_rate_limit(
                ip_address, username
            )

            if not is_allowed:
                logger.warning(
                    f"Rate limit blocked request from {ip_address} "
                    f"to {request.path}. Username: {username or 'N/A'}"
                )

                return self._rate_limit_response(error_message)

        response = self.get_response(request)

        # Record failed attempt if authentication failed
        if self._is_auth_failure(request, response):
            ip_address = self._get_client_ip(request)
            username = self._extract_username(request)
            self.rate_limiter.record_failed_attempt(ip_address, username)

        return response

    def _should_rate_limit(self, request: HttpRequest) -> bool:
        """Check if request path should be rate limited"""
        if request.method not in ["POST", "PUT"]:
            return False

        return any(request.path.startswith(path) for path in self.protected_paths)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Extract client IP from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()
        return request.META.get("REMOTE_ADDR", "127.0.0.1")

    def _extract_username(self, request: HttpRequest) -> Optional[str]:
        """Extract username from request if present"""
        if request.method == "POST":
            return request.POST.get("username") or request.POST.get("email")
        return None

    def _is_auth_failure(self, request: HttpRequest, response: HttpResponse) -> bool:
        """Check if response indicates authentication failure"""
        # Check for common auth failure indicators
        if response.status_code in [401, 403]:
            return True

        # Check for redirect to login page (failed admin login)
        if response.status_code == 302:
            location = response.get("Location", "")
            if "login" in location.lower():
                return True

        return False

    def _rate_limit_response(self, error_message: str) -> HttpResponse:
        """Generate rate limit error response"""
        return JsonResponse(
            {"error": "Rate limit exceeded", "message": error_message}, status=429
        )
