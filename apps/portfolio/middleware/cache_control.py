import re

from django.utils.cache import patch_response_headers
from django.utils.deprecation import MiddlewareMixin


class CacheControlMiddleware(MiddlewareMixin):
    """Add appropriate cache control headers based on content type and URL patterns"""

    def process_response(self, request, response):
        # Don't cache admin, auth, or API endpoints
        no_cache_patterns = [
            r"^/admin/",
            r"^/api/",
            r"^/logout/",
            r"^/s/",  # Short URLs shouldn't be cached
        ]

        path = request.path
        for pattern in no_cache_patterns:
            if re.match(pattern, path):
                response["Cache-Control"] = "no-cache, no-store, must-revalidate"
                response["Pragma"] = "no-cache"
                response["Expires"] = "0"
                return response

        # Cache static files for long time
        if path.startswith("/static/") or path.startswith("/media/"):
            # 1 year cache for static files
            patch_response_headers(response, cache_timeout=31536000)
            response["Cache-Control"] = "public, max-age=31536000, immutable"
            return response

        # Cache feeds for shorter time
        if "/feed/" in path or path.endswith(".xml"):
            # 1 hour cache for feeds and XML
            patch_response_headers(response, cache_timeout=3600)
            response["Cache-Control"] = "public, max-age=3600"
            return response

        # Cache regular pages
        content_type = response.get("Content-Type", "").lower()
        if "text/html" in content_type:
            # 5 minutes cache for HTML pages
            patch_response_headers(response, cache_timeout=300)
            response["Cache-Control"] = "public, max-age=300"
        elif "application/json" in content_type:
            # 1 minute cache for JSON
            patch_response_headers(response, cache_timeout=60)
            response["Cache-Control"] = "public, max-age=60"

        return response
