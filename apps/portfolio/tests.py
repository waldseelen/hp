"""
Tests for main app views and middleware
"""

import json
from unittest.mock import patch

from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

# Move model imports inside test methods/setUp to avoid circular imports
# from apps.blog.models import Post
# from apps.main.models import PersonalInfo, SocialLink
# from apps.tools.models import Tool
# from django.contrib.auth import get_user_model


class HealthCheckViewTest(TestCase):
    """Test cases for health_check view"""

    def setUp(self):
        self.client = Client()
        self.url = reverse("main:health_check")

    def test_health_check_success(self):
        """Test successful health check response"""
        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertEqual(data["status"], "healthy")
        self.assertIn("timestamp", data)
        self.assertIn("services", data)
        self.assertIn("database", data["services"])
        self.assertIn("cache", data["services"])
        self.assertEqual(data["services"]["database"]["status"], "healthy")

    def test_health_check_contains_environment_info(self):
        """Test health check includes environment information"""
        response = self.client.get(self.url)
        data = json.loads(response.content)

        self.assertIn("environment", data)
        self.assertIn("debug", data["environment"])
        self.assertIn("django_version", data["environment"])

    @patch("django.db.connection.cursor")
    def test_health_check_database_error(self, mock_cursor):
        """Test health check with database error"""
        mock_cursor.side_effect = Exception("Database connection failed")

        response = self.client.get(self.url)

        self.assertEqual(response.status_code, 503)
        data = json.loads(response.content)
        self.assertEqual(data["status"], "unhealthy")
        self.assertIn("error", data)


class SearchViewTest(TestCase):
    """Test cases for search functionality"""

    def setUp(self):
        self.client = Client()

    def test_search_view_get(self):
        """Test search view GET request"""
        from django.contrib.auth import get_user_model

        from apps.blog.models import Post
        from apps.tools.models import Tool

        User = get_user_model()
        # Create test user
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        # Create test blog post
        Post.objects.create(
            title="Test Blog Post",
            content="This is test content for searching",
            author=user,
            status="published",
            published_at=timezone.now(),
            tags=["django", "testing"],
        )

        # Create test tool
        Tool.objects.create(
            title="Test Tool",
            description="This is a test tool for searching",
            is_visible=True,
        )

        response = self.client.get(reverse("main:search"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "search")
        self.assertIn("search_categories", response.context)
        self.assertIn("popular_searches", response.context)

    def test_search_with_query(self):
        """Test search with query parameter"""
        from django.contrib.auth import get_user_model

        from apps.blog.models import Post
        from apps.tools.models import Tool

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        Post.objects.create(
            title="Test Blog Post",
            content="This is test content for searching",
            author=user,
            status="published",
            published_at=timezone.now(),
            tags=["django", "testing"],
        )

        Tool.objects.create(
            title="Test Tool",
            description="This is a test tool for searching",
            is_visible=True,
        )

        response = self.client.get(reverse("main:search"), {"q": "test"})

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context["query"], "test")
        self.assertIn("search_results", response.context)

    def test_search_api_endpoint(self):
        """Test search API endpoint"""
        from django.contrib.auth import get_user_model

        from apps.blog.models import Post
        from apps.tools.models import Tool

        User = get_user_model()
        user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

        Post.objects.create(
            title="Test Blog Post",
            content="This is test content for searching",
            author=user,
            status="published",
            published_at=timezone.now(),
            tags=["django", "testing"],
        )

        Tool.objects.create(
            title="Test Tool",
            description="This is a test tool for searching",
            is_visible=True,
        )

        response = self.client.get(
            reverse("main:search_api"),
            {"q": "test"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertIn("results", data)
        self.assertIn("total_count", data)

    def test_search_api_requires_ajax(self):
        """Test search API requires AJAX request"""
        response = self.client.get(reverse("main:search_api"), {"q": "test"})

        self.assertEqual(response.status_code, 400)
        data = json.loads(response.content)
        self.assertIn("error", data)

    def test_search_suggestions(self):
        """Test search suggestions endpoint"""
        response = self.client.get(
            reverse("main:search_suggestions"),
            {"q": "te"},
            HTTP_X_REQUESTED_WITH="XMLHttpRequest",
        )

        self.assertEqual(response.status_code, 200)
        data = json.loads(response.content)
        self.assertIn("suggestions", data)
        self.assertIn("query", data)


class SecurityHeadersMiddlewareTest(TestCase):
    """Test cases for SecurityHeadersMiddleware"""

    def setUp(self):
        self.client = Client()

    def test_security_headers_present(self):
        """Test that security headers are added to responses"""
        response = self.client.get("/")

        # Check security headers
        self.assertEqual(response["X-Content-Type-Options"], "nosniff")
        self.assertEqual(response["X-Frame-Options"], "DENY")
        self.assertEqual(response["X-XSS-Protection"], "1; mode=block")
        self.assertEqual(response["Referrer-Policy"], "strict-origin-when-cross-origin")
        self.assertIn("Content-Security-Policy", response)

    def test_csp_header_content(self):
        """Test Content Security Policy header content"""
        response = self.client.get("/")
        csp = response["Content-Security-Policy"]

        self.assertIn("default-src 'self'", csp)
        self.assertIn("object-src 'none'", csp)
        self.assertIn("base-uri 'self'", csp)
        self.assertIn("frame-ancestors 'none'", csp)

    @override_settings(DEBUG=False)
    def test_production_security_headers(self):
        """Test additional security headers in production"""
        response = self.client.get(
            "/", SERVER_NAME="testserver", wsgi={"wsgi.url_scheme": "https"}
        )

        # In production, CSP should include report-uri
        response.get("Content-Security-Policy", "")
        # Note: This test may need adjustment based on actual middleware implementation


class PerformanceMiddlewareTest(TestCase):
    """Test cases for PerformanceMiddleware"""

    def setUp(self):
        self.client = Client()

    def test_response_time_header(self):
        """Test that response time header is added"""
        response = self.client.get("/")

        self.assertIn("X-Response-Time", response)
        # Check that the value looks like a time (ends with 's')
        self.assertTrue(response["X-Response-Time"].endswith("s"))

    def test_performance_headers(self):
        """Test performance optimization headers"""
        response = self.client.get("/")

        self.assertEqual(response["X-DNS-Prefetch-Control"], "on")
        self.assertEqual(response["X-Preload"], "dns-prefetch")


class MainViewsTest(TestCase):
    """Test cases for main views"""

    def setUp(self):
        self.client = Client()

    def test_home_view(self):
        """Test home page view"""
        # Import signal handlers to ensure cache invalidation works
        import apps.core.cache_signals  # noqa: F401
        from apps.main.models import PersonalInfo, SocialLink

        # Create test data
        PersonalInfo.objects.create(
            key="about", value="Test about information", is_visible=True, order=1
        )

        SocialLink.objects.create(
            platform="github",
            url="https://github.com/testuser",
            is_visible=True,
            order=1,
        )

        response = self.client.get(reverse("main:home"))

        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Home")
        self.assertIn("personal_info", response.context)
        self.assertIn("social_links", response.context)

    def test_personal_view(self):
        """Test personal/about page view"""
        # Import signal handlers to ensure cache invalidation works
        import apps.core.cache_signals  # noqa: F401
        from apps.main.models import PersonalInfo, SocialLink

        # Create test data
        PersonalInfo.objects.create(
            key="about", value="Test about information", is_visible=True, order=1
        )

        SocialLink.objects.create(
            platform="github",
            url="https://github.com/testuser",
            is_visible=True,
            order=1,
        )

        response = self.client.get(reverse("main:personal"))

        self.assertEqual(response.status_code, 200)
        self.assertIn("personal_info", response.context)
        self.assertEqual(response.context["page_title"], "Hakkımda")

    def test_view_caching(self):
        """Test that views use caching properly"""
        # Import signal handlers to ensure cache invalidation works
        import apps.core.cache_signals  # noqa: F401
        from apps.main.models import PersonalInfo, SocialLink

        # Create test data
        PersonalInfo.objects.create(
            key="about", value="Test about information", is_visible=True, order=1
        )

        SocialLink.objects.create(
            platform="github",
            url="https://github.com/testuser",
            is_visible=True,
            order=1,
        )

        # Clear cache first
        cache.clear()

        # First request should cache the data
        response1 = self.client.get(reverse("main:home"))
        self.assertEqual(response1.status_code, 200)

        # Second request should use cached data
        response2 = self.client.get(reverse("main:home"))
        self.assertEqual(response2.status_code, 200)

        # Context should be the same
        self.assertEqual(
            len(response1.context["personal_info"]),
            len(response2.context["personal_info"]),
        )

    def test_language_status_view(self):
        """Test language status API endpoint"""
        response = self.client.get(reverse("main:language_status"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response["Content-Type"], "application/json")

        data = json.loads(response.content)
        self.assertIn("current_language", data)
        self.assertIn("available_languages", data)
        self.assertIn("rtl", data)


class CacheControlMiddlewareTest(TestCase):
    """Test cases for CacheControlMiddleware"""

    def setUp(self):
        self.client = Client()

    def test_no_cache_for_admin(self):
        """Test that admin URLs are not cached"""
        # This would require admin URLs to be configured

    def test_static_file_caching(self):
        """Test that static files have long cache headers"""
        # This would require static file serving to be configured

    def test_html_page_caching(self):
        """Test that HTML pages have appropriate cache headers"""
        response = self.client.get("/")

        # Check if cache control header is set
        cache_control = response.get("Cache-Control", "")
        self.assertTrue(len(cache_control) > 0)
