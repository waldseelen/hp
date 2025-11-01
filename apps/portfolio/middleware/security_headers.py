import base64
import secrets

from django.utils.deprecation import MiddlewareMixin


class SecurityHeadersMiddleware(MiddlewareMixin):
    """Add security and performance headers with nonce-based CSP"""

    def process_request(self, request):
        # Generate a unique nonce for each request
        nonce_bytes = secrets.token_bytes(32)
        nonce = base64.b64encode(nonce_bytes).decode("utf-8")
        request.csp_nonce = nonce
        return None

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

        # Get the nonce from request
        nonce = getattr(request, "csp_nonce", "")

        # Enhanced Content Security Policy with nonce-based inline allowlist
        # More restrictive and secure CSP directives
        csp_directives = [
            "default-src 'self'",
            # Script sources - only allow specific CDNs and self with nonce
            f"script-src 'self' 'nonce-{nonce}' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com https://cdnjs.cloudflare.com https://cdn.tailwindcss.com",
            # Style sources - only allow specific style sources with nonce and Alpine.js inline styles
            f"style-src 'self' 'nonce-{nonce}' 'unsafe-inline' 'unsafe-hashes' https://fonts.googleapis.com https://cdn.jsdelivr.net",
            # Font sources - restrict to Google Fonts and self
            "font-src 'self' https://fonts.gstatic.com https://r2cdn.perplexity.ai data:",
            # Image sources - restrict to self, data URIs and HTTPS only
            "img-src 'self' data: https: blob:",
            # Media sources - self and HTTPS only
            "media-src 'self' https:",
            # Connection sources - restrict API calls
            "connect-src 'self' https://api.github.com https://cdn.jsdelivr.net",
            # Worker sources - self and blob URLs only
            "worker-src 'self' blob:",
            # Frame/child sources - none to prevent iframe embedding
            "child-src 'none'",
            "frame-src 'none'",
            # Object sources - completely disabled
            "object-src 'none'",
            # Base URI - restrict to self only
            "base-uri 'self'",
            # Frame ancestors - prevent clickjacking
            "frame-ancestors 'none'",
            # Form actions - restrict to self
            "form-action 'self'",
            # Manifest source - self only
            "manifest-src 'self'",
            # Upgrade insecure requests
            "upgrade-insecure-requests",
            # Block mixed content
            "block-all-mixed-content",
        ]

        # Add report-uri and report-to in production
        if not getattr(request, "DEBUG", True):
            csp_directives.append("report-uri /api/security/csp-report/")
            csp_directives.append("report-to default")

        response["Content-Security-Policy"] = "; ".join(csp_directives)

        # Add additional security headers
        response["X-Permitted-Cross-Domain-Policies"] = "none"

        # Use less restrictive COEP in development to allow CDN resources
        from django.conf import settings

        if getattr(settings, "DEBUG", False):
            response["Cross-Origin-Embedder-Policy"] = "credentialless"
        else:
            response["Cross-Origin-Embedder-Policy"] = "require-corp"
        response["Cross-Origin-Opener-Policy"] = "same-origin"
        response["Cross-Origin-Resource-Policy"] = "same-origin"

        # Additional security headers
        response["Permissions-Policy"] = (
            "accelerometer=(), "
            "camera=(), "
            "geolocation=(self), "
            "gyroscope=(), "
            "magnetometer=(), "
            "microphone=(), "
            "payment=(), "
            "usb=(), "
            "interest-cohort=()"
        )

        # Add Report-To header for multiple security violation reporting
        if not getattr(request, "DEBUG", True):
            import json

            report_endpoints = [
                {
                    "group": "default",
                    "max_age": 10886400,
                    "endpoints": [{"url": "/api/security/csp-report/"}],
                    "include_subdomains": True,
                },
                {
                    "group": "network-errors",
                    "max_age": 10886400,
                    "endpoints": [{"url": "/api/security/network-error-report/"}],
                    "include_subdomains": True,
                },
            ]
            response["Report-To"] = json.dumps(report_endpoints)
            response["NEL"] = json.dumps(
                {
                    "report_to": "network-errors",
                    "max_age": 10886400,
                    "include_subdomains": True,
                    "failure_fraction": 0.1,
                }
            )

        # Preload hints for critical resources
        if request.path == "/":
            preload_links = [
                "</static/css/output.css>; rel=preload; as=style",
                "</static/css/custom.min.css>; rel=preload; as=style",
                "</static/js/main.min.js>; rel=preload; as=script",
            ]
            if preload_links:
                response["Link"] = ", ".join(preload_links)

        return response
