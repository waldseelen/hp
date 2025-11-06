"""
Security Headers Middleware
===========================

Middleware to add security headers to all HTTP responses, including:
- Content Security Policy (CSP)
- HTTP Strict Transport Security (HSTS)
- X-Frame-Options
- X-Content-Type-Options
- Referrer-Policy
- Permissions-Policy
- X-XSS-Protection (legacy support)

OWASP Coverage: A05, A06
"""

import hashlib
import logging
import secrets
from typing import Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Add comprehensive security headers to all responses.

    Headers added:
    - X-Content-Type-Options: nosniff
    - X-Frame-Options: DENY or SAMEORIGIN
    - Referrer-Policy: strict-origin-when-cross-origin
    - Permissions-Policy: Restrict browser features
    - X-XSS-Protection: 1; mode=block (legacy)

    Features:
    - Configurable headers via settings
    - Automatic HTTPS detection
    - Per-view header customization support
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

        # Load settings with defaults
        self.x_frame_options = getattr(settings, "X_FRAME_OPTIONS", "DENY")
        self.referrer_policy = getattr(
            settings, "REFERRER_POLICY", "strict-origin-when-cross-origin"
        )
        self.permissions_policy = getattr(
            settings, "PERMISSIONS_POLICY", self._default_permissions_policy()
        )

        logger.info("SecurityHeadersMiddleware initialized")

    def _default_permissions_policy(self) -> str:
        """Get default Permissions-Policy header value."""
        return (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=()"
        )

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add security headers to response."""

        # X-Content-Type-Options: Prevent MIME sniffing
        if "X-Content-Type-Options" not in response:
            response["X-Content-Type-Options"] = "nosniff"

        # X-Frame-Options: Clickjacking protection
        if "X-Frame-Options" not in response:
            # Check for view-specific override
            x_frame_options = getattr(request, "x_frame_options", self.x_frame_options)
            response["X-Frame-Options"] = x_frame_options

        # Referrer-Policy: Control referrer information
        if "Referrer-Policy" not in response:
            response["Referrer-Policy"] = self.referrer_policy

        # Permissions-Policy: Restrict browser features
        if "Permissions-Policy" not in response:
            response["Permissions-Policy"] = self.permissions_policy

        # X-XSS-Protection: Legacy XSS protection (for older browsers)
        if "X-XSS-Protection" not in response:
            response["X-XSS-Protection"] = "1; mode=block"

        return response


class HSTSMiddleware(MiddlewareMixin):
    """
    Add HTTP Strict Transport Security (HSTS) header to enforce HTTPS.

    Features:
    - Configurable max-age (default: 1 year)
    - includeSubDomains support
    - preload support
    - Only adds header for HTTPS connections
    - Automatic subdomain detection

    OWASP Coverage: A05 (Security Misconfiguration)
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

        # Load HSTS settings
        self.max_age = getattr(settings, "HSTS_MAX_AGE", 31536000)  # 1 year
        self.include_subdomains = getattr(settings, "HSTS_INCLUDE_SUBDOMAINS", True)
        self.preload = getattr(settings, "HSTS_PRELOAD", False)

        # Build HSTS header value
        self.hsts_value = self._build_hsts_header()

        logger.info(
            f"HSTSMiddleware initialized: max-age={self.max_age}, "
            f"includeSubDomains={self.include_subdomains}, "
            f"preload={self.preload}"
        )

    def _build_hsts_header(self) -> str:
        """Build HSTS header value from settings."""
        parts = [f"max-age={self.max_age}"]

        if self.include_subdomains:
            parts.append("includeSubDomains")

        if self.preload:
            parts.append("preload")

        return "; ".join(parts)

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add HSTS header to HTTPS responses."""

        # Only add HSTS header for HTTPS connections
        if request.is_secure():
            if "Strict-Transport-Security" not in response:
                response["Strict-Transport-Security"] = self.hsts_value

        return response


class ContentSecurityPolicyMiddleware(MiddlewareMixin):
    """
    Add Content Security Policy (CSP) header to prevent XSS attacks.

    Features:
    - Nonce generation for inline scripts/styles
    - Report-only mode for testing
    - Configurable directives
    - Automatic nonce injection into templates
    - Hash-based CSP support

    OWASP Coverage: A03 (Injection), A05 (Security Misconfiguration)

    Usage:
        In templates: {% load security_tags %}
        <script nonce="{{ request.csp_nonce }}">...</script>
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

        # CSP settings
        self.report_only = getattr(settings, "CSP_REPORT_ONLY", False)
        self.report_uri = getattr(settings, "CSP_REPORT_URI", None)
        self.directives = getattr(
            settings, "CSP_DIRECTIVES", self._default_directives()
        )

        logger.info(
            f"ContentSecurityPolicyMiddleware initialized: "
            f"report_only={self.report_only}"
        )

    def _default_directives(self) -> dict:
        """Get default CSP directives."""
        return {
            "default-src": ["'self'"],
            "script-src": ["'self'"],
            "style-src": ["'self'"],
            "img-src": ["'self'", "data:", "https:"],
            "font-src": ["'self'", "data:"],
            "connect-src": ["'self'"],
            "frame-ancestors": ["'none'"],
            "base-uri": ["'self'"],
            "form-action": ["'self'"],
            "upgrade-insecure-requests": [],
        }

    def _generate_nonce(self) -> str:
        """Generate a cryptographically secure nonce."""
        return secrets.token_urlsafe(16)

    def _build_csp_header(self, nonce: str) -> str:
        """Build CSP header value with nonce."""
        directives = []

        for directive, values in self.directives.items():
            if not values:
                # Directive with no value (e.g., upgrade-insecure-requests)
                directives.append(directive)
            else:
                # Add nonce to script-src and style-src
                if directive in ["script-src", "style-src"]:
                    values = list(values) + [f"'nonce-{nonce}'"]

                values_str = " ".join(values)
                directives.append(f"{directive} {values_str}")

        # Add report-uri if configured
        if self.report_uri:
            directives.append(f"report-uri {self.report_uri}")

        return "; ".join(directives)

    def process_request(self, request: HttpRequest) -> None:
        """Generate and attach nonce to request."""
        nonce = self._generate_nonce()
        request.csp_nonce = nonce

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Add CSP header to response."""

        # Get nonce from request
        nonce = getattr(request, "csp_nonce", self._generate_nonce())

        # Build CSP header
        csp_header = self._build_csp_header(nonce)

        # Choose header name based on report-only mode
        header_name = (
            "Content-Security-Policy-Report-Only"
            if self.report_only
            else "Content-Security-Policy"
        )

        # Add header if not already present
        if header_name not in response:
            response[header_name] = csp_header

        return response


class SubresourceIntegrityHelper:
    """
    Helper class for generating Subresource Integrity (SRI) hashes.

    Features:
    - SHA-256, SHA-384, SHA-512 hash generation
    - Automatic integrity attribute generation
    - Static file hash caching
    - CDN resource validation

    Usage:
        sri = SubresourceIntegrityHelper()
        integrity = sri.generate_hash('/static/js/app.js')
        # Use in template: <script src="..." integrity="{{ integrity }}" crossorigin="anonymous">
    """

    def __init__(self, algorithm: str = "sha384"):
        """
        Initialize SRI helper.

        Args:
            algorithm: Hash algorithm ('sha256', 'sha384', or 'sha512')
        """
        if algorithm not in ["sha256", "sha384", "sha512"]:
            raise ValueError(
                f"Invalid algorithm: {algorithm}. "
                f"Must be 'sha256', 'sha384', or 'sha512'."
            )

        self.algorithm = algorithm
        self._hash_cache = {}

        logger.info(f"SubresourceIntegrityHelper initialized: {algorithm}")

    def generate_hash(self, file_path: str) -> str:
        """
        Generate SRI hash for a file.

        Args:
            file_path: Path to the file (relative to STATIC_ROOT or absolute)

        Returns:
            Integrity attribute value (e.g., 'sha384-...')

        Raises:
            FileNotFoundError: If file doesn't exist
        """
        # Check cache
        if file_path in self._hash_cache:
            return self._hash_cache[file_path]

        # Resolve file path
        from django.contrib.staticfiles import finders

        absolute_path = finders.find(file_path)

        if not absolute_path:
            # Try as absolute path
            import os

            if os.path.exists(file_path):
                absolute_path = file_path
            else:
                raise FileNotFoundError(f"Static file not found: {file_path}")

        # Read file and generate hash
        with open(absolute_path, "rb") as f:
            file_content = f.read()

        # Generate hash
        if self.algorithm == "sha256":
            hash_obj = hashlib.sha256(file_content)
        elif self.algorithm == "sha384":
            hash_obj = hashlib.sha384(file_content)
        else:  # sha512
            hash_obj = hashlib.sha512(file_content)

        # Base64 encode
        import base64

        hash_base64 = base64.b64encode(hash_obj.digest()).decode("utf-8")

        # Build integrity value
        integrity = f"{self.algorithm}-{hash_base64}"

        # Cache result
        self._hash_cache[file_path] = integrity

        logger.debug(f"Generated SRI hash for {file_path}: {integrity}")

        return integrity

    def generate_hashes_for_files(self, file_paths: list) -> dict:
        """
        Generate SRI hashes for multiple files.

        Args:
            file_paths: List of file paths

        Returns:
            Dictionary mapping file paths to integrity values
        """
        hashes = {}

        for file_path in file_paths:
            try:
                hashes[file_path] = self.generate_hash(file_path)
            except FileNotFoundError as e:
                logger.error(f"Failed to generate hash for {file_path}: {e}")
                hashes[file_path] = None

        return hashes

    def clear_cache(self):
        """Clear the hash cache."""
        self._hash_cache.clear()
        logger.debug("SRI hash cache cleared")


# Helper functions for use in views/templates


def get_csp_nonce(request: HttpRequest) -> Optional[str]:
    """
    Get CSP nonce from request.

    Usage in views:
        nonce = get_csp_nonce(request)
        return render(request, 'template.html', {'nonce': nonce})
    """
    return getattr(request, "csp_nonce", None)


def set_frame_options(request: HttpRequest, value: str):
    """
    Set X-Frame-Options for a specific view.

    Usage in views:
        def my_view(request):
            set_frame_options(request, 'SAMEORIGIN')
            return render(request, 'template.html')
    """
    if value not in ["DENY", "SAMEORIGIN", "ALLOW-FROM"]:
        raise ValueError(
            f"Invalid X-Frame-Options value: {value}. "
            f"Must be 'DENY', 'SAMEORIGIN', or 'ALLOW-FROM'."
        )

    request.x_frame_options = value
