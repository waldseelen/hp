"""
Middleware for static file optimization and caching headers.
"""

import hashlib
import logging
import mimetypes
from pathlib import Path

from django.conf import settings
from django.http import FileResponse
from django.utils import timezone
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class StaticFileOptimizationMiddleware(MiddlewareMixin):
    """Middleware for optimizing static file delivery."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.static_url = getattr(settings, "STATIC_URL", "/static/")
        self.media_url = getattr(settings, "MEDIA_URL", "/media/")
        self.enable_compression = getattr(settings, "STATIC_COMPRESSION", True)
        self.enable_webp = getattr(settings, "STATIC_WEBP_SUPPORT", True)
        super().__init__(get_response)

    def process_request(self, request):
        """Process static file requests for optimization."""
        path = request.path

        # Only process static and media files
        if not (path.startswith(self.static_url) or path.startswith(self.media_url)):
            return None

        # Check for WebP support for images
        if self.enable_webp and self.is_image_request(path):
            webp_response = self.try_serve_webp(request, path)
            if webp_response:
                return webp_response

        # Check for compressed versions
        if self.enable_compression and self.is_compressible(path):
            compressed_response = self.try_serve_compressed(request, path)
            if compressed_response:
                return compressed_response

        return None

    def process_response(self, request, response):
        """Add optimization headers to static file responses."""
        path = request.path

        # Only process static and media files
        if not (path.startswith(self.static_url) or path.startswith(self.media_url)):
            return response

        # Add caching headers for static files
        if path.startswith(self.static_url):
            self.add_static_file_headers(request, response, path)
        elif path.startswith(self.media_url):
            self.add_media_file_headers(request, response, path)

        return response

    def is_image_request(self, path):
        """Check if request is for an image."""
        image_extensions = [".jpg", ".jpeg", ".png", ".gif"]
        return any(path.lower().endswith(ext) for ext in image_extensions)

    def is_compressible(self, path):
        """Check if file is compressible."""
        compressible_extensions = [".css", ".js", ".html", ".svg", ".json", ".xml"]
        return any(path.lower().endswith(ext) for ext in compressible_extensions)

    def try_serve_webp(self, request, path):
        """Try to serve WebP version if available."""
        # Check if client supports WebP
        accept = request.META.get("HTTP_ACCEPT", "")
        if "image/webp" not in accept:
            return None

        # Get WebP version path
        webp_path = self.get_webp_path(path)
        if not webp_path:
            return None

        try:
            # Serve WebP file if it exists
            webp_file = Path(webp_path)
            if webp_file.exists():
                return self.serve_static_file(webp_file, "image/webp")
        except Exception as e:
            logger.error(f"Error serving WebP file {webp_path}: {e}")

        return None

    def try_serve_compressed(self, request, path):
        """Try to serve compressed version if available."""
        # Check client encoding support
        encoding = request.META.get("HTTP_ACCEPT_ENCODING", "")

        # Prefer Brotli over Gzip
        if "br" in encoding:
            brotli_response = self.try_serve_brotli(path)
            if brotli_response:
                return brotli_response

        if "gzip" in encoding:
            gzip_response = self.try_serve_gzip(path)
            if gzip_response:
                return gzip_response

        return None

    def try_serve_brotli(self, path):
        """Try to serve Brotli compressed version."""
        brotli_path = self.get_file_path(path + ".br")
        if not brotli_path or not Path(brotli_path).exists():
            return None

        try:
            response = self.serve_static_file(Path(brotli_path))
            response["Content-Encoding"] = "br"
            response["Vary"] = "Accept-Encoding"
            return response
        except Exception as e:
            logger.error(f"Error serving Brotli file {brotli_path}: {e}")
            return None

    def try_serve_gzip(self, path):
        """Try to serve Gzip compressed version."""
        gzip_path = self.get_file_path(path + ".gz")
        if not gzip_path or not Path(gzip_path).exists():
            return None

        try:
            response = self.serve_static_file(Path(gzip_path))
            response["Content-Encoding"] = "gzip"
            response["Vary"] = "Accept-Encoding"
            return response
        except Exception as e:
            logger.error(f"Error serving Gzip file {gzip_path}: {e}")
            return None

    def serve_static_file(self, file_path, content_type=None):
        """Serve static file with proper headers."""
        if not content_type:
            content_type, _ = mimetypes.guess_type(str(file_path))
            content_type = content_type or "application/octet-stream"

        response = FileResponse(open(file_path, "rb"), content_type=content_type)

        # Add file size header
        response["Content-Length"] = file_path.stat().st_size

        return response

    def add_static_file_headers(self, request, response, path):
        """Add caching headers for static files."""
        # Long-term caching for static files (1 year)
        cache_control = "public, max-age=31536000, immutable"

        # Shorter cache for development
        if hasattr(settings, "DEBUG") and settings.DEBUG:
            cache_control = "public, max-age=3600"  # 1 hour

        response["Cache-Control"] = cache_control

        # Add ETag for better caching
        if not response.has_header("ETag"):
            etag = self.generate_etag(request, path)
            if etag:
                response["ETag"] = etag

        # Add Last-Modified header
        if not response.has_header("Last-Modified"):
            last_modified = self.get_last_modified(path)
            if last_modified:
                response["Last-Modified"] = last_modified

        # Add compression info if compressed
        if response.has_header("Content-Encoding"):
            response["Vary"] = "Accept-Encoding"

        # Security headers for static files
        if path.endswith(".js"):
            response["X-Content-Type-Options"] = "nosniff"

    def add_media_file_headers(self, request, response, path):
        """Add caching headers for media files."""
        # Medium-term caching for media files (1 week)
        cache_control = "public, max-age=604800"

        # Shorter cache for development
        if hasattr(settings, "DEBUG") and settings.DEBUG:
            cache_control = "public, max-age=1800"  # 30 minutes

        response["Cache-Control"] = cache_control

        # Add ETag
        if not response.has_header("ETag"):
            etag = self.generate_etag(request, path)
            if etag:
                response["ETag"] = etag

    def generate_etag(self, request, path):
        """Generate ETag for file."""
        try:
            file_path = self.get_file_path(path)
            if file_path and Path(file_path).exists():
                file_stat = Path(file_path).stat()
                etag_data = f"{file_stat.st_mtime}_{file_stat.st_size}_{path}"
                etag = hashlib.md5(
                    etag_data.encode(), usedforsecurity=False
                ).hexdigest()[:16]
                return f'"{etag}"'
        except Exception as e:
            logger.error(f"Error generating ETag for {path}: {e}")

        return None

    def get_last_modified(self, path):
        """Get last modified time for file."""
        try:
            file_path = self.get_file_path(path)
            if file_path and Path(file_path).exists():
                mtime = Path(file_path).stat().st_mtime
                return timezone.datetime.fromtimestamp(mtime, tz=timezone.utc).strftime(
                    "%a, %d %b %Y %H:%M:%S GMT"
                )
        except Exception as e:
            logger.error(f"Error getting last modified time for {path}: {e}")

        return None

    def get_file_path(self, path):
        """Get file system path for URL path."""
        try:
            if path.startswith(self.static_url):
                # Static file
                relative_path = path[len(self.static_url) :]
                if hasattr(settings, "STATIC_ROOT") and settings.STATIC_ROOT:
                    return Path(settings.STATIC_ROOT) / relative_path
                else:
                    # Development - check STATICFILES_DIRS
                    for static_dir in getattr(settings, "STATICFILES_DIRS", []):
                        full_path = Path(static_dir) / relative_path
                        if full_path.exists():
                            return str(full_path)

            elif path.startswith(self.media_url):
                # Media file
                relative_path = path[len(self.media_url) :]
                if hasattr(settings, "MEDIA_ROOT"):
                    return str(Path(settings.MEDIA_ROOT) / relative_path)

        except Exception as e:
            logger.error(f"Error getting file path for {path}: {e}")

        return None

    def get_webp_path(self, path):
        """Get WebP version path for image."""
        if not self.is_image_request(path):
            return None

        # Replace extension with .webp
        base_path = path.rsplit(".", 1)[0]
        webp_path = base_path + ".webp"

        return self.get_file_path(webp_path)


class TTFBOptimizationMiddleware(MiddlewareMixin):
    """Middleware for Time To First Byte (TTFB) optimization."""

    def __init__(self, get_response):
        self.get_response = get_response
        super().__init__(get_response)

    def process_request(self, request):
        """Start request timing."""
        import time

        request._start_time = time.time()

    def process_response(self, request, response):
        """Optimize TTFB with early response techniques."""
        # Add server timing header for debugging
        if hasattr(request, "_start_time"):
            import time

            duration = time.time() - request._start_time
            response["Server-Timing"] = f"total;dur={duration * 1000:.1f}"

            # Log slow requests
            if duration > 1.0:
                logger.warning(f"Slow response: {request.path} took {duration:.3f}s")

        # Enable HTTP/2 Server Push hints for critical resources
        if not getattr(settings, "DEBUG", False):
            self.add_server_push_hints(request, response)

        # Add performance hints
        response["X-DNS-Prefetch-Control"] = "on"

        return response

    def add_server_push_hints(self, request, response):
        """Add Link headers for HTTP/2 Server Push."""
        # Only for HTML responses
        if not response.get("Content-Type", "").startswith("text/html"):
            return

        # Critical CSS
        css_files = [
            "/static/css/critical/base.css",
            "/static/css/optimized/main.min.css",
        ]

        # Critical JS
        js_files = [
            "/static/js/minified/main.min.js",
        ]

        link_headers = []

        for css_file in css_files:
            link_headers.append(f"<{css_file}>; rel=preload; as=style")

        for js_file in js_files:
            link_headers.append(f"<{js_file}>; rel=preload; as=script")

        if link_headers:
            response["Link"] = ", ".join(link_headers)


class ResourceHintsMiddleware(MiddlewareMixin):
    """Middleware for adding resource hints."""

    def process_response(self, request, response):
        """Add resource hints to HTML responses."""
        if not response.get("Content-Type", "").startswith("text/html"):
            return response

        # Add DNS prefetch for external domains
        external_domains = [
            "fonts.googleapis.com",
            "fonts.gstatic.com",
            "cdn.jsdelivr.net",
        ]

        dns_prefetch_links = []
        for domain in external_domains:
            dns_prefetch_links.append(f"<https://{domain}>; rel=dns-prefetch")

        # Add preconnect for critical external resources
        preconnect_links = [
            "<https://fonts.googleapis.com>; rel=preconnect; crossorigin",
            "<https://fonts.gstatic.com>; rel=preconnect; crossorigin",
        ]

        # Combine existing Link header
        existing_links = response.get("Link", "")
        all_links = []

        if existing_links:
            all_links.append(existing_links)

        all_links.extend(dns_prefetch_links)
        all_links.extend(preconnect_links)

        if all_links:
            response["Link"] = ", ".join(all_links)

        return response


class StaticFileMetricsMiddleware(MiddlewareMixin):
    """Middleware for collecting static file performance metrics."""

    def __init__(self, get_response):
        self.get_response = get_response
        self.static_url = getattr(settings, "STATIC_URL", "/static/")
        super().__init__(get_response)

    def process_response(self, request, response):
        """Collect metrics for static file requests."""
        if not request.path.startswith(self.static_url):
            return response

        # Collect metrics (sampling to avoid overhead)
        if hash(request.path) % 100 == 0:  # 1% sampling
            self.record_static_file_metric(request, response)

        return response

    def record_static_file_metric(self, request, response):
        """Record static file performance metric."""
        try:
            from apps.main.models import PerformanceMetric

            # Get file size
            content_length = response.get("Content-Length", 0)
            if hasattr(response, "content"):
                content_length = len(response.content)

            # Determine file type
            file_extension = Path(request.path).suffix.lower()

            PerformanceMetric.objects.create(
                metric_type="static_file_request",
                value=int(content_length) if content_length else 0,
                url=request.path,
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
                additional_data={
                    "file_extension": file_extension,
                    "status_code": response.status_code,
                    "cache_hit": (
                        "HIT" if response.get("X-Cache-Status") == "HIT" else "MISS"
                    ),
                    "compressed": bool(response.get("Content-Encoding")),
                },
            )

        except Exception as e:
            logger.error(f"Error recording static file metric: {e}")
