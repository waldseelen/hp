"""
CDN Middleware for handling CDN configuration and cache headers.

This middleware adds appropriate cache headers for static and media files
when serving through CDN or directly from Django.
"""

from django.conf import settings
from django.utils.cache import patch_cache_control, patch_response_headers


class CDNMiddleware:
    """
    Middleware to add CDN-friendly cache headers to responses.

    Adds appropriate cache headers for:
    - Static files (CSS, JS, images, fonts)
    - Media files (uploaded content)
    - API responses
    """

    def __init__(self, get_response):
        self.get_response = get_response
        self.cdn_enabled = getattr(settings, "CDN_ENABLED", False)
        self.cdn_domain = getattr(settings, "CDN_DOMAIN", "")

    def __call__(self, request):
        response = self.get_response(request)

        # Add cache headers for static and media files
        if self._is_static_or_media(request.path):
            self._add_static_cache_headers(response)

        # Add CDN-specific headers
        if self.cdn_enabled and self.cdn_domain:
            response["X-CDN-Enabled"] = "true"
            response["X-CDN-Domain"] = self.cdn_domain

        return response

    def _is_static_or_media(self, path):
        """Check if the path is for a static or media file."""
        static_url = getattr(settings, "STATIC_URL", "/static/")
        media_url = getattr(settings, "MEDIA_URL", "/media/")
        return path.startswith(static_url) or path.startswith(media_url)

    def _add_static_cache_headers(self, response):
        """Add cache headers optimized for static files."""
        # Cache for 1 year (immutable files with hashed names)
        max_age = getattr(settings, "WHITENOISE_MAX_AGE", 31536000)

        patch_cache_control(response, public=True, max_age=max_age, immutable=True)

        # Additional headers for CDN optimization
        response["Cache-Control"] = f"public, max-age={max_age}, immutable"
        response["X-Content-Type-Options"] = "nosniff"
        response["Vary"] = "Accept-Encoding"


class CompressionMiddleware:
    """
    Middleware to handle compression settings for responses.

    Works with WhiteNoise to ensure proper compression headers.
    """

    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)

        # Add compression headers if not already present
        if "Content-Encoding" not in response and len(response.content) > 1024:
            # Signal that this response should be compressed
            response["X-Compress"] = "true"

        return response
