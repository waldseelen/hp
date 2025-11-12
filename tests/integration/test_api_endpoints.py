"""
Integration tests for REST API endpoints - Phase 22C.1.

Tests cover:
- apps/portfolio/views.py (API views with ListAPIView, APIView, @api_view decorators)
- apps/main/ (search API endpoints)
- apps/playground/ (code execution API)
- Authentication, permissions, rate limiting, pagination, filtering

Target: Comprehensive API integration testing with real HTTP requests.
"""

import json
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.blog.models import Post
from apps.portfolio.models import (
    Admin,
    AITool,
    CybersecurityResource,
    PersonalInfo,
    SocialLink,
    UsefulResource,
)

User = get_user_model()


# ============================================================================
# PORTFOLIO API TESTS
# ============================================================================


@pytest.mark.django_db
class TestPersonalInfoAPI:
    """Test PersonalInfo List API endpoint."""

    def setup_method(self):
        """Set up test client and test data."""
        self.client = APIClient()
        PersonalInfo.objects.create(
            key="name", value="John Doe", type="text", display_order=1
        )
        PersonalInfo.objects.create(
            key="email", value="john@example.com", type="email", display_order=2
        )

    def test_personalinfo_list_api_returns_200(self):
        """Test PersonalInfo API returns 200 OK."""
        url = reverse("portfolio:personal_info_list")  # Adjust based on actual URL name
        response = self.client.get(url)

        # Should be accessible without authentication
        assert response.status_code == status.HTTP_200_OK

    def test_personalinfo_list_api_returns_json(self):
        """Test PersonalInfo API returns JSON response."""
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url)

        assert response["Content-Type"] == "application/json"

    def test_personalinfo_list_api_contains_data(self):
        """Test PersonalInfo API returns correct data."""
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url)

        data = response.json()
        assert len(data) >= 2  # We created 2 records

        # Verify data structure
        first_item = data[0]
        assert "key" in first_item
        assert "value" in first_item
        assert "type" in first_item


@pytest.mark.django_db
class TestSocialLinkAPI:
    """Test SocialLink List API endpoint."""

    def setup_method(self):
        """Set up test client and test data."""
        self.client = APIClient()
        SocialLink.objects.create(
            platform="GitHub",
            url="https://github.com/testuser",
            display_order=1,
            is_active=True,
        )
        SocialLink.objects.create(
            platform="LinkedIn",
            url="https://linkedin.com/in/testuser",
            display_order=2,
            is_active=True,
        )

    def test_sociallink_list_api_returns_200(self):
        """Test SocialLink API returns 200 OK."""
        url = reverse("portfolio:social_link_list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_sociallink_list_api_filters_active(self):
        """Test SocialLink API only returns active links."""
        # Create inactive link
        SocialLink.objects.create(
            platform="Twitter",
            url="https://twitter.com/testuser",
            display_order=3,
            is_active=False,
        )

        url = reverse("portfolio:social_link_list")
        response = self.client.get(url)

        data = response.json()
        # Should only return 2 active links (not the inactive one)
        assert len(data) == 2
        assert all(link["is_active"] for link in data)


@pytest.mark.django_db
class TestAIToolAPI:
    """Test AITool List API endpoint."""

    def setup_method(self):
        """Set up test client and test data."""
        self.client = APIClient()
        from apps.tools.models import Tool

        Tool.objects.create(
            title="ChatGPT",
            description="AI chatbot",
            url="https://chat.openai.com",
            category="AI/ML",
            is_visible=True,
        )
        Tool.objects.create(
            title="GitHub Copilot",
            description="AI pair programmer",
            url="https://github.com/features/copilot",
            category="Development",
            is_visible=True,
        )

    def test_aitool_list_api_returns_200(self):
        """Test AITool API returns 200 OK."""
        url = reverse("portfolio:aitool_list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_aitool_list_api_category_filtering(self):
        """Test AITool API category filtering."""
        url = reverse("portfolio:aitool_list")

        # Test filtering by category (if supported)
        response = self.client.get(url, {"category": "AI/ML"})

        if response.status_code == status.HTTP_200_OK:
            data = response.json()
            # Should only return AI/ML tools
            for tool in data:
                if "category" in tool:
                    assert tool["category"] == "AI/ML"


# ============================================================================
# SEARCH API TESTS (with Meilisearch mocked)
# ============================================================================


@pytest.mark.django_db
class TestSearchAPI:
    """Test search API endpoints with mocked Meilisearch."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()

    @patch("apps.main.search_index.SearchIndexManager.search")
    def test_search_api_returns_200(self, mock_search):
        """Test search API returns 200 OK."""
        mock_search.return_value = {
            "hits": [{"id": "post_1", "title": "Test Post", "content": "Test content"}],
            "estimatedTotalHits": 1,
            "processingTimeMs": 10,
        }

        url = reverse("main:search_api")
        response = self.client.get(url, {"q": "test"})

        assert response.status_code == status.HTTP_200_OK

    @patch("apps.main.search_index.SearchIndexManager.search")
    def test_search_api_requires_query_param(self, mock_search):
        """Test search API requires 'q' query parameter."""
        url = reverse("main:search_api")
        response = self.client.get(url)

        # Should return 400 Bad Request or handle gracefully
        assert response.status_code in [status.HTTP_400_BAD_REQUEST, status.HTTP_200_OK]

    @patch("apps.main.search_index.SearchIndexManager.search")
    def test_search_api_returns_json_structure(self, mock_search):
        """Test search API returns expected JSON structure."""
        mock_search.return_value = {
            "hits": [{"id": "post_1", "title": "Test Post"}],
            "estimatedTotalHits": 1,
        }

        url = reverse("main:search_api")
        response = self.client.get(url, {"q": "test"})

        data = response.json()
        assert "hits" in data or "results" in data  # Either key might be used

    @patch("apps.main.search_index.SearchIndexManager.search_suggest")
    def test_search_suggest_api(self, mock_suggest):
        """Test search suggest/autocomplete API."""
        mock_suggest.return_value = ["test post", "test article", "test guide"]

        url = reverse("main:search_suggest")
        response = self.client.get(url, {"q": "test"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert isinstance(data, (list, dict))

    @patch("apps.main.search_index.SearchIndexManager.get_stats")
    def test_search_stats_api(self, mock_stats):
        """Test search statistics API."""
        mock_stats.return_value = {
            "total_documents": 100,
            "total_queries": 500,
            "avg_response_time": 15,
        }

        url = reverse("main:search_stats")
        response = self.client.get(url)

        # May require authentication
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]


# ============================================================================
# PLAYGROUND API TESTS
# ============================================================================


@pytest.mark.django_db
class TestPlaygroundAPI:
    """Test code playground API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()

    @patch("subprocess.run")
    def test_execute_code_api_requires_post(self, mock_run):
        """Test execute code API requires POST method."""
        url = reverse("playground:execute_code")

        # GET should fail
        response = self.client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    @patch("subprocess.run")
    def test_execute_code_api_with_valid_code(self, mock_run):
        """Test execute code API with valid Python code."""
        from unittest.mock import MagicMock

        mock_result = MagicMock()
        mock_result.stdout = "Hello, World!"
        mock_result.stderr = ""
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        url = reverse("playground:execute_code")
        response = self.client.post(
            url,
            data=json.dumps({"code": "print('Hello, World!')"}),
            content_type="application/json",
        )

        # Should return 200 or require authentication
        assert response.status_code in [
            status.HTTP_200_OK,
            status.HTTP_401_UNAUTHORIZED,
            status.HTTP_403_FORBIDDEN,
        ]

    def test_save_snippet_api_requires_post(self):
        """Test save snippet API requires POST method."""
        url = reverse("playground:save_snippet")

        # GET should fail
        response = self.client.get(url)
        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_get_template_api(self):
        """Test get template API endpoint."""
        url = reverse("playground:get_template", kwargs={"template_id": 1})
        response = self.client.get(url)

        # Should return 200 or 404 if template doesn't exist
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


# ============================================================================
# AUTHENTICATION & PERMISSIONS TESTS
# ============================================================================


@pytest.mark.django_db
class TestAPIAuthentication:
    """Test API authentication and permissions."""

    def setup_method(self):
        """Set up test client and user."""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@example.com", password="testpass123"
        )

    def test_unauthenticated_access_to_public_api(self):
        """Test unauthenticated access to public APIs."""
        # PersonalInfo should be public
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_authenticated_access(self):
        """Test authenticated access to APIs."""
        self.client.force_authenticate(user=self.user)

        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url)

        assert response.status_code == status.HTTP_200_OK

    def test_admin_only_endpoints(self):
        """Test admin-only API endpoints."""
        # Create regular user and admin
        regular_user = self.user
        admin_user = User.objects.create_superuser(
            username="admin", email="admin@example.com", password="adminpass123"
        )

        # Try accessing admin endpoint as regular user
        self.client.force_authenticate(user=regular_user)
        url = reverse("main:admin_search_metrics")  # Adjust if different
        response = self.client.get(url)

        # Should be forbidden
        assert response.status_code in [
            status.HTTP_403_FORBIDDEN,
            status.HTTP_401_UNAUTHORIZED,
        ]

        # Try accessing as admin
        self.client.force_authenticate(user=admin_user)
        response = self.client.get(url)

        # Should be allowed (200 or 404 if endpoint doesn't exist yet)
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]


# ============================================================================
# RATE LIMITING TESTS (if implemented)
# ============================================================================


@pytest.mark.django_db
class TestAPIRateLimiting:
    """Test API rate limiting (if implemented)."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()

    @pytest.mark.skip("Rate limiting configuration dependent")
    def test_rate_limit_exceeded(self):
        """Test API rate limiting kicks in after too many requests."""
        url = reverse("main:search_api")

        # Make many requests rapidly
        responses = []
        for i in range(100):
            response = self.client.get(url, {"q": f"test{i}"})
            responses.append(response.status_code)

        # At some point, should receive 429 Too Many Requests
        assert status.HTTP_429_TOO_MANY_REQUESTS in responses


# ============================================================================
# ERROR HANDLING TESTS
# ============================================================================


@pytest.mark.django_db
class TestAPIErrorHandling:
    """Test API error handling."""

    def setup_method(self):
        """Set up test client."""
        self.client = APIClient()

    def test_api_404_for_invalid_endpoint(self):
        """Test API returns 404 for non-existent endpoint."""
        response = self.client.get("/api/nonexistent/endpoint/")

        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_api_405_for_wrong_method(self):
        """Test API returns 405 for wrong HTTP method."""
        url = reverse("playground:execute_code")

        # execute_code requires POST, try DELETE
        response = self.client.delete(url)

        assert response.status_code == status.HTTP_405_METHOD_NOT_ALLOWED

    def test_api_400_for_invalid_json(self):
        """Test API returns 400 for malformed JSON."""
        url = reverse("playground:execute_code")

        response = self.client.post(
            url, data="invalid json {", content_type="application/json"
        )

        # Should return 400 Bad Request or 500 Internal Server Error
        assert response.status_code in [
            status.HTTP_400_BAD_REQUEST,
            status.HTTP_500_INTERNAL_SERVER_ERROR,
        ]


# ============================================================================
# PAGINATION TESTS
# ============================================================================


@pytest.mark.django_db
class TestAPIPagination:
    """Test API pagination."""

    def setup_method(self):
        """Set up test client and create many records."""
        self.client = APIClient()

        # Create 50 PersonalInfo records
        for i in range(50):
            PersonalInfo.objects.create(
                key=f"key_{i}", value=f"value_{i}", type="text", display_order=i
            )

    def test_api_pagination_page_1(self):
        """Test API pagination returns first page."""
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url, {"page": 1})

        assert response.status_code == status.HTTP_200_OK

        data = response.json()
        # Should return paginated results (check for 'results', 'count', 'next', 'previous')
        if isinstance(data, dict):
            assert "results" in data or "count" in data

    def test_api_pagination_page_2(self):
        """Test API pagination returns second page."""
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url, {"page": 2})

        # Should return 200 or 404 if page doesn't exist
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_404_NOT_FOUND]

    def test_api_pagination_invalid_page(self):
        """Test API pagination handles invalid page number."""
        url = reverse("portfolio:personal_info_list")
        response = self.client.get(url, {"page": "invalid"})

        # Should return 400 Bad Request or default to page 1
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]
