"""
Cache middleware for API responses and request optimization.
"""

import hashlib
import json
import logging
import time

from django.conf import settings
from django.http import HttpResponse, JsonResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

from apps.main.cache import cache_manager

logger = logging.getLogger(__name__)


class APIResponseCacheMiddleware(MiddlewareMixin):
    """Middleware for caching API responses."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.cache_timeout = getattr(settings, "API_CACHE_TIMEOUT", 300)  # 5 minutes
        self.cacheable_paths = getattr(
            settings,
            "API_CACHEABLE_PATHS",
            [
                "/api/posts/",
                "/api/personal-info/",
                "/api/social-links/",
                "/api/ai-tools/",
                "/api/performance/",
            ],
        )
        super().__init__(get_response)

    def process_request(self, request):
        """Process incoming request for cache lookup."""
        # Only cache GET requests for API endpoints
        if request.method != "GET" or not self.is_cacheable_path(request.path):
            return None

        # Generate cache key
        cache_key = self.generate_cache_key(request)

        # Try to get cached response
        cached_response = cache_manager.get(cache_key)
        if cached_response:
            logger.debug(f"API Cache HIT: {request.path}")

            # Reconstruct response
            response_data, content_type, status_code = cached_response

            if content_type == "application/json":
                response = JsonResponse(response_data, safe=False)
            else:
                response = HttpResponse(
                    (
                        json.dumps(response_data)
                        if isinstance(response_data, (dict, list))
                        else response_data
                    ),
                    content_type=content_type,
                )

            response.status_code = status_code

            # Add cache headers
            response["X-Cache-Status"] = "HIT"
            response["X-Cache-Key"] = cache_key[:50]  # Truncate for header

            return response

        # Cache miss - store key for process_response
        request._api_cache_key = cache_key
        return None

    def process_response(self, request, response):
        """Process response for caching."""
        # Only cache successful API responses
        if not hasattr(request, "_api_cache_key") or response.status_code != 200:
            return response

        cache_key = request._api_cache_key

        try:
            # Determine content type and extract data
            content_type = response.get("Content-Type", "text/html")

            if content_type.startswith("application/json"):
                # JSON response
                if hasattr(response, "data"):
                    # DRF Response
                    response_data = response.data
                else:
                    # JsonResponse
                    response_data = json.loads(response.content.decode("utf-8"))
            else:
                # Other response types
                response_data = response.content.decode("utf-8")

            # Cache the response data
            cached_data = (response_data, content_type, response.status_code)
            cache_manager.set(cache_key, cached_data, self.cache_timeout)

            logger.debug(f"API Cache SET: {request.path}")

            # Add cache headers
            response["X-Cache-Status"] = "MISS"
            response["X-Cache-Key"] = cache_key[:50]

        except Exception as e:
            logger.error(f"API caching error for {request.path}: {e}")

        return response

    def is_cacheable_path(self, path):
        """Check if path is cacheable."""
        return any(
            path.startswith(cacheable_path) for cacheable_path in self.cacheable_paths
        )

    def generate_cache_key(self, request):
        """Generate cache key for request."""
        # Include path and query parameters
        key_parts = ["api_response", request.path, request.GET.urlencode()]

        # Include user information for personalized content
        if hasattr(request, "user") and request.user.is_authenticated:
            key_parts.append(f"user_{request.user.pk}")

        # Create hash for long keys
        cache_key = "_".join(filter(None, key_parts))
        if len(cache_key) > 200:
            cache_key = f"api_response_{hashlib.md5(cache_key.encode(), usedforsecurity=False).hexdigest()}"

        return cache_key


class CacheHeadersMiddleware(MiddlewareMixin):
    """Middleware for setting cache headers."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.static_cache_timeout = 86400 * 30  # 30 days
        self.dynamic_cache_timeout = 300  # 5 minutes
        super().__init__(get_response)

    def process_response(self, request, response):
        """Add appropriate cache headers."""
        # Skip for admin and debug pages
        if request.path.startswith("/admin/") or (
            hasattr(settings, "DEBUG") and settings.DEBUG
        ):
            return response

        # Static files
        if self.is_static_file(request.path):
            response["Cache-Control"] = f"public, max-age={self.static_cache_timeout}"
            response["Expires"] = self.get_expires_header(self.static_cache_timeout)

        # API endpoints
        elif request.path.startswith("/api/"):
            if response.status_code == 200 and request.method == "GET":
                response["Cache-Control"] = (
                    f"public, max-age={self.dynamic_cache_timeout}"
                )
                response["Expires"] = self.get_expires_header(
                    self.dynamic_cache_timeout
                )
            else:
                response["Cache-Control"] = "no-cache, no-store, must-revalidate"

        # Dynamic pages
        elif response.status_code == 200:
            response["Cache-Control"] = "public, max-age=60, stale-while-revalidate=300"

        # Add ETag for better caching
        if not response.has_header("ETag") and response.status_code == 200:
            etag = hashlib.md5(
                f"{request.path}_{response.content}".encode(), usedforsecurity=False
            ).hexdigest()[:16]
            response["ETag"] = f'"{etag}"'

        return response

    def is_static_file(self, path):
        """Check if path is a static file."""
        static_extensions = [
            ".css",
            ".js",
            ".png",
            ".jpg",
            ".jpeg",
            ".gif",
            ".svg",
            ".ico",
            ".woff",
            ".woff2",
        ]
        return any(path.endswith(ext) for ext in static_extensions)

    def get_expires_header(self, seconds):
        """Generate Expires header."""
        expires_time = timezone.now() + timezone.timedelta(seconds=seconds)
        return expires_time.strftime("%a, %d %b %Y %H:%M:%S GMT")


class RequestTimingMiddleware(MiddlewareMixin):
    """Middleware for request timing and performance monitoring."""

    def process_request(self, request):
        """Start timing request."""
        request._start_time = time.time()

    def process_response(self, request, response):
        """Complete timing and add headers."""
        if hasattr(request, "_start_time"):
            duration = time.time() - request._start_time

            # Add timing header
            response["X-Response-Time"] = f"{duration:.3f}s"

            # Log slow requests
            if duration > 1.0:  # Log requests taking more than 1 second
                logger.warning(f"Slow request: {request.path} took {duration:.3f}s")

            # Store performance metrics
            if request.path.startswith("/api/"):
                self.store_api_performance_metric(request, response, duration)

        return response

    def store_api_performance_metric(self, request, response, duration):
        """Store performance metrics for API endpoints."""
        try:
            # Only store metrics for successful requests periodically
            if (
                response.status_code == 200 and hash(request.path) % 10 == 0
            ):  # 10% sampling

                from apps.main.models import PerformanceMetric

                PerformanceMetric.objects.create(
                    metric_type="api_response_time",
                    value=duration * 1000,  # Convert to milliseconds
                    url=request.path,
                    user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                    additional_data={
                        "method": request.method,
                        "status_code": response.status_code,
                        "content_length": (
                            len(response.content) if hasattr(response, "content") else 0
                        ),
                    },
                )
        except Exception as e:
            logger.error(f"Error storing API performance metric: {e}")


class CacheWarmupMiddleware(MiddlewareMixin):
    """Middleware for cache warmup on application startup."""

    def __init__(self, get_response):
        self.get_response = get_response
        self._warmed_up = False
        super().__init__(get_response)

    def process_request(self, request):
        """Warm up cache on first request."""
        if not self._warmed_up and not request.path.startswith("/admin/"):
            try:
                from apps.main.cache import CacheWarmer

                CacheWarmer.warm_all_caches()
                self._warmed_up = True
                logger.info("Cache warmup completed on first request")
            except Exception as e:
                logger.error(f"Cache warmup failed: {e}")
                self._warmed_up = True  # Don't retry on every request

        return None


class ConditionalGetMiddleware(MiddlewareMixin):
    """Middleware for conditional GET requests (ETag/Last-Modified)."""

    def process_response(self, request, response):
        """Handle conditional GET requests."""
        if request.method != "GET" or response.status_code != 200:
            return response

        # Check ETag
        etag = response.get("ETag")
        if etag and request.META.get("HTTP_IF_NONE_MATCH") == etag:
            response.status_code = 304
            response.content = b""
            return response

        # Check Last-Modified
        last_modified = response.get("Last-Modified")
        if last_modified and request.META.get("HTTP_IF_MODIFIED_SINCE"):
            try:
                if_modified_since = request.META.get("HTTP_IF_MODIFIED_SINCE")
                # Simple string comparison for now
                if if_modified_since == last_modified:
                    response.status_code = 304
                    response.content = b""
                    return response
            except Exception:
                pass

        return response


# Decorator for caching function results
def cache_function_result(timeout=300, key_prefix="func"):
    """Decorator for caching function results."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix, func.__name__]
            key_parts.extend(str(arg) for arg in args)
            key_parts.extend(f"{k}_{v}" for k, v in sorted(kwargs.items()))

            cache_key = "_".join(key_parts)
            if len(cache_key) > 200:
                cache_key = f"{key_prefix}_{func.__name__}_{hashlib.md5(cache_key.encode(), usedforsecurity=False).hexdigest()}"

            # Try cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute and cache
            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


# View decorator for API response caching
def cache_api_response(timeout=300, vary_on=None, key_func=None):  # noqa: C901
    """Decorator for caching API responses."""

    def decorator(view_func):
        def wrapper(request, *args, **kwargs):
            # Skip caching for non-GET requests
            if request.method != "GET":
                return view_func(request, *args, **kwargs)

            # Generate cache key
            if key_func:
                cache_key = key_func(request, *args, **kwargs)
            else:
                key_parts = ["api_view", view_func.__name__, request.path]

                if vary_on:
                    for var in vary_on:
                        if hasattr(request, var):
                            key_parts.append(f"{var}_{getattr(request, var)}")
                        elif var in request.GET:
                            key_parts.append(f"{var}_{request.GET[var]}")

                cache_key = "_".join(key_parts)

            # Try cache
            cached_response = cache_manager.get(cache_key)
            if cached_response:
                return JsonResponse(cached_response, safe=False)

            # Execute view and cache result
            response = view_func(request, *args, **kwargs)

            # Cache successful JSON responses
            if hasattr(response, "data") and response.status_code == 200:
                cache_manager.set(cache_key, response.data, timeout)
            elif isinstance(response, JsonResponse) and response.status_code == 200:
                response_data = json.loads(response.content.decode("utf-8"))
                cache_manager.set(cache_key, response_data, timeout)

            return response

        return wrapper

    return decorator
