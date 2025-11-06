"""
Cache control, security headers, compression, and performance middleware.
"""

import logging
import re
import time

from django.utils.cache import patch_response_headers
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("performance")


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


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security and performance headers"""

    def process_response(self, request, response):
        # Security headers
        response["X-Content-Type-Options"] = "nosniff"
        response["X-Frame-Options"] = "DENY"
        response["X-XSS-Protection"] = "1; mode=block"
        response["Referrer-Policy"] = "strict-origin-when-cross-origin"

        # Performance headers
        response["X-DNS-Prefetch-Control"] = "on"

        # HSTS for HTTPS (only add in production)
        if request.is_secure():
            response["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains"
            )

        # Content Security Policy (basic)
        csp_directives = [
            "default-src 'self'",
            "script-src 'self' 'unsafe-inline' https://cdn.tailwindcss.com https://unpkg.com",
            "style-src 'self' 'unsafe-inline' https://fonts.googleapis.com",
            "font-src 'self' https://fonts.gstatic.com",
            "img-src 'self' data: https: http:",
            "media-src 'self' https:",
            "object-src 'none'",
            "base-uri 'self'",
            "frame-ancestors 'none'",
        ]
        response["Content-Security-Policy"] = "; ".join(csp_directives)

        # Preload hints for critical resources
        if request.path == "/":
            preload_links = [
                "</static/css/custom.css>; rel=preload; as=style",
                "</static/js/main.js>; rel=preload; as=script",
            ]
            if preload_links:
                response["Link"] = ", ".join(preload_links)

        return response


class CompressionMiddleware(MiddlewareMixin):
    """Additional compression settings"""

    def process_response(self, request, response):
        # Add Vary header for better caching
        vary_headers = (
            response.get("Vary", "").split(", ") if response.get("Vary") else []
        )

        # Add encoding to vary for compressed responses
        if "Accept-Encoding" not in vary_headers:
            vary_headers.append("Accept-Encoding")

        # Add User-Agent for mobile optimization
        if "User-Agent" not in vary_headers:
            vary_headers.append("User-Agent")

        response["Vary"] = ", ".join(filter(None, vary_headers))

        return response


class PerformanceMiddleware(MiddlewareMixin):
    """Performance monitoring and optimization middleware"""

    def process_request(self, request):
        # Store request start time
        request._start_time = time.time()
        return None

    def process_response(self, request, response):
        # Calculate request processing time
        if hasattr(request, "_start_time"):
            duration = time.time() - request._start_time

            # Add timing header
            response["X-Processing-Time"] = f"{duration:.3f}s"

            # Log slow requests
            if duration > 2.0:  # Log requests taking more than 2 seconds
                logger.warning(
                    f"Slow request: {request.method} {request.path} took {duration:.3f}s"
                )

        return response
