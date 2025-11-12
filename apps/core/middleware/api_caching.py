"""
API Response Caching Middleware

This middleware provides comprehensive caching for API responses including:
- ETag generation and validation
- Cache-Control headers
- Conditional requests (If-Modified-Since, If-None-Match)
- Redis-based response caching
- Cache versioning
- Automatic cache invalidation
"""

import hashlib
import json
from datetime import datetime

from django.conf import settings
from django.core.cache import caches
from django.http import HttpResponse, JsonResponse
from django.utils.cache import patch_cache_control
from django.utils.http import http_date, parse_http_date


class APICachingMiddleware:
    """
    Middleware for API response caching with ETag and conditional requests.

    Features:
    - Automatic ETag generation
    - Cache-Control headers
    - 304 Not Modified responses
    - Redis caching for GET requests
    - Version-based cache keys
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cache = caches["api_cache"]
        self.api_version = getattr(settings, "API_VERSION", "v1")
        self.cache_timeout = 900  # 15 minutes default

    def __call__(self, request):  # noqa: C901
        # Only cache API endpoints
        if not self._is_api_request(request):
            return self.get_response(request)

        # Handle non-GET requests
        if request.method != "GET":
            return self._handle_mutation_request(request)

        # Try to return cached response
        cache_key = self._generate_cache_key(request)
        cached_response = self._try_cached_response(request, cache_key)
        if cached_response:
            return cached_response

        # Get and cache fresh response
        return self._get_and_cache_response(request, cache_key)

    def _handle_mutation_request(self, request):
        """Handle POST/PUT/PATCH/DELETE requests and invalidate cache."""
        response = self.get_response(request)
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            self._invalidate_related_cache(request)
        return response

    def _try_cached_response(self, request, cache_key):
        """Try to return cached response if available and valid."""
        cached_data = self.cache.get(cache_key)
        if not cached_data:
            return None

        # Check conditional request headers
        conditional_response = self._check_conditional_headers(request, cached_data)
        if conditional_response:
            return conditional_response

        # Return cached response
        return self._build_cached_response(cached_data)

    def _check_conditional_headers(self, request, cached_data):
        """Check If-None-Match and If-Modified-Since headers."""
        # Check ETag
        if "etag" in cached_data:
            if_none_match = request.META.get("HTTP_IF_NONE_MATCH")
            if if_none_match == cached_data["etag"]:
                return self._not_modified_response(cached_data["etag"])

        # Check Last-Modified
        if "last_modified" in cached_data:
            not_modified = self._check_if_modified_since(request, cached_data)
            if not_modified:
                return not_modified

        return None

    def _check_if_modified_since(self, request, cached_data):
        """Check If-Modified-Since header against cached last_modified."""
        if_modified_since = request.META.get("HTTP_IF_MODIFIED_SINCE")
        if not if_modified_since:
            return None

        try:
            if_modified_since_time = parse_http_date(if_modified_since)
            if cached_data["last_modified"] <= if_modified_since_time:
                return self._not_modified_response(
                    cached_data.get("etag"), cached_data["last_modified"]
                )
        except (ValueError, TypeError):
            pass

        return None

    def _build_cached_response(self, cached_data):
        """Build response from cached data."""
        response = JsonResponse(cached_data["content"], safe=False)
        self._add_cache_headers(
            response, cached_data.get("etag"), cached_data.get("last_modified")
        )
        response["X-Cache-Status"] = "HIT"
        return response

    def _get_and_cache_response(self, request, cache_key):
        """Get fresh response and cache if appropriate."""
        response = self.get_response(request)

        # Only cache successful JSON responses
        is_cacheable = response.status_code == 200 and isinstance(
            response, JsonResponse
        )
        if is_cacheable:
            self._cache_response(request, response, cache_key)

        return response

    def _is_api_request(self, request):
        """Check if request is for an API endpoint."""
        api_paths = ["/api/", "/ajax/"]
        return any(request.path.startswith(path) for path in api_paths)

    def _generate_cache_key(self, request):
        """Generate a unique cache key for the request."""
        # Include version, path, query params, and user auth status
        key_parts = [
            self.api_version,
            request.path,
            request.GET.urlencode(),
            "auth" if request.user.is_authenticated else "anon",
        ]
        key_string = "|".join(key_parts)
        key_hash = hashlib.md5(
            key_string.encode(), usedforsecurity=False
        ).hexdigest()  # nosec
        return f"api_cache:{self.api_version}:{key_hash}"

    def _generate_etag(self, content):
        """Generate ETag from content."""
        if isinstance(content, (dict, list)):
            content = json.dumps(content, sort_keys=True)
        elif not isinstance(content, (str, bytes)):
            content = str(content)

        if isinstance(content, str):
            content = content.encode("utf-8")

        return f'"{hashlib.md5(content).hexdigest()}"'  # nosec

    def _cache_response(self, request, response, cache_key):
        """Cache the response with metadata."""
        try:
            content = json.loads(response.content)
        except (json.JSONDecodeError, AttributeError):
            return

        etag = self._generate_etag(content)
        last_modified = int(datetime.now().timestamp())

        cache_data = {
            "content": content,
            "etag": etag,
            "last_modified": last_modified,
            "cached_at": datetime.now().isoformat(),
        }

        # Determine cache timeout based on endpoint
        timeout = self._get_cache_timeout(request.path)
        self.cache.set(cache_key, cache_data, timeout)

        # Add headers to response
        self._add_cache_headers(response, etag, last_modified)
        response["X-Cache-Status"] = "MISS"

    def _get_cache_timeout(self, path):
        """Get appropriate cache timeout for endpoint."""
        # Configure per-endpoint timeouts
        timeout_config = {
            "/api/posts/": 600,  # 10 minutes
            "/api/tools/": 1800,  # 30 minutes
            "/api/categories/": 3600,  # 1 hour
            "/api/search/": 300,  # 5 minutes
        }

        for pattern, timeout in timeout_config.items():
            if pattern in path:
                return timeout

        return self.cache_timeout  # Default

    def _add_cache_headers(self, response, etag=None, last_modified=None):
        """Add caching headers to response."""
        # ETag
        if etag:
            response["ETag"] = etag

        # Last-Modified
        if last_modified:
            response["Last-Modified"] = http_date(last_modified)

        # Cache-Control
        patch_cache_control(
            response, public=True, max_age=self.cache_timeout, must_revalidate=True
        )

        # Additional headers
        response["Vary"] = "Accept, Accept-Encoding, Authorization"
        response["X-API-Version"] = self.api_version

    def _not_modified_response(self, etag=None, last_modified=None):
        """Create a 304 Not Modified response."""
        response = HttpResponse(status=304)

        if etag:
            response["ETag"] = etag
        if last_modified:
            response["Last-Modified"] = http_date(last_modified)

        response["X-Cache-Status"] = "NOT-MODIFIED"
        return response

    def _invalidate_related_cache(self, request):
        """Invalidate cache for related endpoints after mutations."""
        # Extract resource type from path (e.g., /api/posts/123/ -> posts)
        path_parts = [p for p in request.path.split("/") if p]

        if len(path_parts) >= 2 and path_parts[0] == "api":
            # Resource type can be used for future granular cache invalidation
            # resource = path_parts[1]

            # Note: This is a simple invalidation. For production,
            # consider using cache tagging or more sophisticated invalidation
            try:
                # Clear the entire api_cache for simplicity
                # In production, use more granular invalidation
                self.cache.clear()
            except Exception:  # nosec B110 - Cache clearing failure is non-critical
                pass  # Fail silently if cache clearing fails


class CacheInvalidationMiddleware:
    """
    Middleware to handle cache invalidation on data updates.

    Automatically invalidates relevant caches when data is modified.
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.api_cache = caches["api_cache"]
        self.query_cache = caches["query_cache"]

    def __call__(self, request):
        response = self.get_response(request)

        # Invalidate cache on successful mutations
        is_mutation = request.method in ["POST", "PUT", "PATCH", "DELETE"]
        is_successful = 200 <= response.status_code < 300
        if is_mutation and is_successful:
            self._invalidate_caches(request, response)

        return response

    def _invalidate_caches(self, request, response):
        """Invalidate relevant caches based on the request."""
        # Determine what to invalidate based on path
        if "/api/" in request.path:
            # Invalidate API cache
            try:
                self.api_cache.clear()
            except Exception:  # nosec B110 - Cache clearing failure is non-critical
                pass

        # Also invalidate query cache for database changes
        if request.method in ["POST", "PUT", "PATCH", "DELETE"]:
            try:
                self.query_cache.clear()
            except Exception:  # nosec B110 - Cache clearing failure is non-critical
                pass


class ResponseTimeMiddleware:
    """
    Middleware to track API response times.

    Adds X-Response-Time header and logs slow responses.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        import time

        start_time = time.time()
        response = self.get_response(request)
        duration = time.time() - start_time

        # Add response time header
        response["X-Response-Time"] = f"{duration * 1000:.2f}ms"

        # Log slow API responses (>500ms)
        if duration > 0.5 and "/api/" in request.path:
            import logging

            logger = logging.getLogger("performance")
            logger.warning(
                f"Slow API response: {request.path} took {duration * 1000:.2f}ms",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "duration_ms": duration * 1000,
                    "user": (
                        request.user.username
                        if request.user.is_authenticated
                        else "anonymous"
                    ),
                },
            )

        return response
