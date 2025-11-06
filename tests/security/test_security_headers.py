"""
Security Headers Tests
======================

Comprehensive tests for security headers middleware:
- SecurityHeadersMiddleware
- HSTSMiddleware
- ContentSecurityPolicyMiddleware
- SubresourceIntegrityHelper

Coverage: OWASP A05, A06
"""

from django.http import HttpResponse
from django.test import RequestFactory, TestCase, override_settings

import pytest

from apps.core.middleware.security_headers import (
    ContentSecurityPolicyMiddleware,
    HSTSMiddleware,
    SecurityHeadersMiddleware,
    SubresourceIntegrityHelper,
    get_csp_nonce,
    set_frame_options,
)


@pytest.mark.django_db
class TestSecurityHeadersMiddleware(TestCase):
    """Test SecurityHeadersMiddleware functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse()
        self.middleware = SecurityHeadersMiddleware(self.get_response)

    def test_x_content_type_options_header(self):
        """Test X-Content-Type-Options header is added."""
        request = self.factory.get("/")
        response = self.middleware(request)

        assert "X-Content-Type-Options" in response
        assert response["X-Content-Type-Options"] == "nosniff"

    def test_x_frame_options_header_default(self):
        """Test X-Frame-Options header with default value."""
        request = self.factory.get("/")
        response = self.middleware(request)

        assert "X-Frame-Options" in response
        assert response["X-Frame-Options"] == "DENY"

    @override_settings(X_FRAME_OPTIONS="SAMEORIGIN")
    def test_x_frame_options_header_custom(self):
        """Test X-Frame-Options header with custom value."""
        middleware = SecurityHeadersMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        assert response["X-Frame-Options"] == "SAMEORIGIN"

    def test_x_frame_options_per_view_override(self):
        """Test per-view X-Frame-Options override."""
        request = self.factory.get("/")
        set_frame_options(request, "SAMEORIGIN")
        response = self.middleware(request)

        assert response["X-Frame-Options"] == "SAMEORIGIN"

    def test_referrer_policy_header(self):
        """Test Referrer-Policy header is added."""
        request = self.factory.get("/")
        response = self.middleware(request)

        assert "Referrer-Policy" in response
        assert response["Referrer-Policy"] == "strict-origin-when-cross-origin"

    def test_permissions_policy_header(self):
        """Test Permissions-Policy header is added."""
        request = self.factory.get("/")
        response = self.middleware(request)

        assert "Permissions-Policy" in response
        assert "camera=()" in response["Permissions-Policy"]
        assert "microphone=()" in response["Permissions-Policy"]
        assert "geolocation=()" in response["Permissions-Policy"]

    def test_x_xss_protection_header(self):
        """Test X-XSS-Protection header for legacy browsers."""
        request = self.factory.get("/")
        response = self.middleware(request)

        assert "X-XSS-Protection" in response
        assert response["X-XSS-Protection"] == "1; mode=block"

    def test_existing_headers_not_overridden(self):
        """Test that existing headers are not overridden."""
        request = self.factory.get("/")

        # Create response with existing headers
        def get_response_with_headers(req):
            response = HttpResponse()
            response["X-Frame-Options"] = "ALLOW-FROM https://example.com"
            return response

        middleware = SecurityHeadersMiddleware(get_response_with_headers)
        response = middleware(request)

        # Existing header should not be overridden
        assert response["X-Frame-Options"] == "ALLOW-FROM https://example.com"


@pytest.mark.django_db
class TestHSTSMiddleware(TestCase):
    """Test HSTSMiddleware functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse()

    @override_settings(
        HSTS_MAX_AGE=31536000, HSTS_INCLUDE_SUBDOMAINS=True, HSTS_PRELOAD=False
    )
    def test_hsts_header_on_https(self):
        """Test HSTS header is added on HTTPS connections."""
        middleware = HSTSMiddleware(self.get_response)
        request = self.factory.get("/", secure=True)
        response = middleware(request)

        assert "Strict-Transport-Security" in response
        assert "max-age=31536000" in response["Strict-Transport-Security"]
        assert "includeSubDomains" in response["Strict-Transport-Security"]
        assert "preload" not in response["Strict-Transport-Security"]

    def test_hsts_header_not_on_http(self):
        """Test HSTS header is NOT added on HTTP connections."""
        middleware = HSTSMiddleware(self.get_response)
        request = self.factory.get("/")  # HTTP by default
        response = middleware(request)

        assert "Strict-Transport-Security" not in response

    @override_settings(
        HSTS_MAX_AGE=63072000, HSTS_INCLUDE_SUBDOMAINS=True, HSTS_PRELOAD=True
    )
    def test_hsts_preload_enabled(self):
        """Test HSTS header with preload enabled."""
        middleware = HSTSMiddleware(self.get_response)
        request = self.factory.get("/", secure=True)
        response = middleware(request)

        assert "max-age=63072000" in response["Strict-Transport-Security"]
        assert "includeSubDomains" in response["Strict-Transport-Security"]
        assert "preload" in response["Strict-Transport-Security"]

    @override_settings(HSTS_INCLUDE_SUBDOMAINS=False)
    def test_hsts_without_subdomains(self):
        """Test HSTS header without includeSubDomains."""
        middleware = HSTSMiddleware(self.get_response)
        request = self.factory.get("/", secure=True)
        response = middleware(request)

        assert "includeSubDomains" not in response["Strict-Transport-Security"]


@pytest.mark.django_db
class TestContentSecurityPolicyMiddleware(TestCase):
    """Test ContentSecurityPolicyMiddleware functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.factory = RequestFactory()
        self.get_response = lambda request: HttpResponse()

    @override_settings(CSP_REPORT_ONLY=False)
    def test_csp_header_enforcing_mode(self):
        """Test CSP header in enforcing mode."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        assert "Content-Security-Policy" in response
        assert "Content-Security-Policy-Report-Only" not in response

    @override_settings(CSP_REPORT_ONLY=True)
    def test_csp_header_report_only_mode(self):
        """Test CSP header in report-only mode."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        assert "Content-Security-Policy-Report-Only" in response
        assert "Content-Security-Policy" not in response

    def test_csp_nonce_generation(self):
        """Test CSP nonce is generated for each request."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")

        # Process request to generate nonce
        middleware.process_request(request)

        assert hasattr(request, "csp_nonce")
        assert len(request.csp_nonce) > 0

        # Nonce should be different for each request
        request2 = self.factory.get("/")
        middleware.process_request(request2)

        assert request.csp_nonce != request2.csp_nonce

    def test_csp_nonce_in_header(self):
        """Test CSP nonce is included in header."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        csp_header = response["Content-Security-Policy"]

        # Header should contain nonce
        assert "'nonce-" in csp_header

    def test_csp_default_directives(self):
        """Test default CSP directives are present."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        csp_header = response["Content-Security-Policy"]

        # Check key directives
        assert "default-src 'self'" in csp_header
        assert "script-src" in csp_header
        assert "style-src" in csp_header
        assert "img-src 'self' data: https:" in csp_header
        assert "frame-ancestors 'none'" in csp_header
        assert "upgrade-insecure-requests" in csp_header

    @override_settings(
        CSP_DIRECTIVES={
            "default-src": ["'self'"],
            "script-src": ["'self'", "https://cdn.example.com"],
            "style-src": ["'self'", "https://fonts.googleapis.com"],
        }
    )
    def test_csp_custom_directives(self):
        """Test custom CSP directives."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        csp_header = response["Content-Security-Policy"]

        assert "https://cdn.example.com" in csp_header
        assert "https://fonts.googleapis.com" in csp_header

    @override_settings(CSP_REPORT_URI="/api/csp-report/")
    def test_csp_report_uri(self):
        """Test CSP report-uri directive."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        response = middleware(request)

        csp_header = response["Content-Security-Policy"]

        assert "report-uri /api/csp-report/" in csp_header

    def test_get_csp_nonce_helper(self):
        """Test get_csp_nonce helper function."""
        middleware = ContentSecurityPolicyMiddleware(self.get_response)
        request = self.factory.get("/")
        middleware.process_request(request)

        nonce = get_csp_nonce(request)

        assert nonce is not None
        assert nonce == request.csp_nonce


class TestSubresourceIntegrityHelper(TestCase):
    """Test SubresourceIntegrityHelper functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.sri_helper = SubresourceIntegrityHelper()

    def test_initialization_default_algorithm(self):
        """Test SRI helper initialization with default algorithm."""
        helper = SubresourceIntegrityHelper()
        assert helper.algorithm == "sha384"

    def test_initialization_custom_algorithm(self):
        """Test SRI helper initialization with custom algorithm."""
        helper = SubresourceIntegrityHelper(algorithm="sha512")
        assert helper.algorithm == "sha512"

    def test_initialization_invalid_algorithm(self):
        """Test SRI helper raises error for invalid algorithm."""
        with pytest.raises(ValueError):
            SubresourceIntegrityHelper(algorithm="md5")

    def test_generate_hash_format(self):
        """Test generated hash format."""
        # Create a temporary test file
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('console.log("test");')
            temp_path = f.name

        try:
            integrity = self.sri_helper.generate_hash(temp_path)

            # Hash should start with algorithm name
            assert integrity.startswith("sha384-")

            # Base64 part should be present
            assert len(integrity) > 10

        finally:
            os.unlink(temp_path)

    def test_generate_hash_caching(self):
        """Test hash caching for performance."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('console.log("test");')
            temp_path = f.name

        try:
            # Generate hash twice
            integrity1 = self.sri_helper.generate_hash(temp_path)
            integrity2 = self.sri_helper.generate_hash(temp_path)

            # Should return same hash (from cache)
            assert integrity1 == integrity2

        finally:
            os.unlink(temp_path)

    def test_generate_hash_file_not_found(self):
        """Test hash generation for non-existent file."""
        with pytest.raises(FileNotFoundError):
            self.sri_helper.generate_hash("/nonexistent/file.js")

    def test_generate_hashes_for_multiple_files(self):
        """Test generating hashes for multiple files."""
        import os
        import tempfile

        temp_files = []

        # Create test files
        for i in range(3):
            f = tempfile.NamedTemporaryFile(mode="w", delete=False)
            f.write(f'console.log("test {i}");')
            f.close()
            temp_files.append(f.name)

        try:
            hashes = self.sri_helper.generate_hashes_for_files(temp_files)

            # Should generate hashes for all files
            assert len(hashes) == 3

            # All hashes should be valid
            for path, integrity in hashes.items():
                assert integrity is not None
                assert integrity.startswith("sha384-")

        finally:
            for path in temp_files:
                os.unlink(path)

    def test_clear_cache(self):
        """Test cache clearing."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('console.log("test");')
            temp_path = f.name

        try:
            # Generate hash to populate cache
            self.sri_helper.generate_hash(temp_path)
            assert len(self.sri_helper._hash_cache) > 0

            # Clear cache
            self.sri_helper.clear_cache()
            assert len(self.sri_helper._hash_cache) == 0

        finally:
            os.unlink(temp_path)

    def test_different_algorithms_produce_different_hashes(self):
        """Test that different algorithms produce different hashes."""
        import os
        import tempfile

        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write('console.log("test");')
            temp_path = f.name

        try:
            helper_sha256 = SubresourceIntegrityHelper(algorithm="sha256")
            helper_sha384 = SubresourceIntegrityHelper(algorithm="sha384")
            helper_sha512 = SubresourceIntegrityHelper(algorithm="sha512")

            hash_256 = helper_sha256.generate_hash(temp_path)
            hash_384 = helper_sha384.generate_hash(temp_path)
            hash_512 = helper_sha512.generate_hash(temp_path)

            # All hashes should be different
            assert hash_256 != hash_384
            assert hash_384 != hash_512
            assert hash_256 != hash_512

            # But all should start with correct algorithm
            assert hash_256.startswith("sha256-")
            assert hash_384.startswith("sha384-")
            assert hash_512.startswith("sha512-")

        finally:
            os.unlink(temp_path)


class TestHelperFunctions(TestCase):
    """Test helper functions."""

    def test_set_frame_options_valid_values(self):
        """Test set_frame_options with valid values."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")

        # Test DENY
        set_frame_options(request, "DENY")
        assert request.x_frame_options == "DENY"

        # Test SAMEORIGIN
        set_frame_options(request, "SAMEORIGIN")
        assert request.x_frame_options == "SAMEORIGIN"

    def test_set_frame_options_invalid_value(self):
        """Test set_frame_options raises error for invalid value."""
        from django.test import RequestFactory

        factory = RequestFactory()
        request = factory.get("/")

        with pytest.raises(ValueError):
            set_frame_options(request, "INVALID")
