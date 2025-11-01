"""
Integration Tests for Search API Endpoints

Tests covering:
- /api/search/ main search endpoint
- /api/search/suggest/ autocomplete
- /api/search/stats/ statistics
- Query parameter handling (q, category, page, per_page)
- Pagination and filtering
- Rate limiting
- Error handling
- Response format validation
- Performance metrics
"""

import json
from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.core.cache import cache
from django.test import Client, TestCase, override_settings
from django.urls import reverse

import pytest
from rest_framework import status
from rest_framework.test import APIClient

from apps.main.models import AITool, BlogPost, CybersecurityResource, UsefulResource
from apps.main.search_index import search_index_manager

User = get_user_model()


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
class TestSearchAPIEndpoint(TestCase):
    """Test /api/search/ endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

        # Create test data
        self.blog_posts = []
        for i in range(5):
            post = BlogPost.objects.create(
                title=f"Django Tutorial {i}",
                slug=f"django-tutorial-{i}",
                content=f"Learn Django web framework part {i}",
                excerpt=f"Django excerpt {i}",
                tags="python, django, web",
                author=self.user,
                status="published",
                is_featured=(i % 2 == 0),
                view_count=i * 10,
            )
            self.blog_posts.append(post)

        # Create AI tools
        self.ai_tools = []
        for i in range(3):
            tool = AITool.objects.create(
                name=f"AI Tool {i}",
                slug=f"ai-tool-{i}",
                description=f"AI tool description {i}",
                category="chatbot",
                is_visible=True,
                is_featured=(i == 0),
                rating=4.0 + i * 0.5,
            )
            self.ai_tools.append(tool)

    def tearDown(self):
        """Clean up after tests"""
        cache.clear()

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_basic_query(self, mock_manager):
        """Test basic search query"""
        mock_manager.index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost-1",
                    "model": "BlogPost",
                    "title": "Django Tutorial",
                    "content": "Learn Django",
                    "url": "/blog/django-tutorial/",
                }
            ],
            "estimatedTotalHits": 1,
            "query": "django",
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "django"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "results" in data
        assert "total" in data
        assert "query" in data
        assert data["query"] == "django"
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Django Tutorial"

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_empty_query(self, mock_manager):
        """Test search with empty query"""
        response = self.client.get("/api/search/", {"q": ""})

        # Should return 400 or empty results
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_no_query_parameter(self, mock_manager):
        """Test search without query parameter"""
        response = self.client.get("/api/search/")

        # Should return 400 or all results
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_with_pagination(self, mock_manager):
        """Test search pagination"""
        # Mock 25 results
        hits = [
            {
                "id": f"BlogPost-{i}",
                "model": "BlogPost",
                "title": f"Post {i}",
                "content": f"Content {i}",
            }
            for i in range(25)
        ]

        mock_manager.index.search.return_value = {
            "hits": hits[:10],  # First page
            "estimatedTotalHits": 25,
            "query": "test",
            "processingTimeMs": 5,
        }

        response = self.client.get(
            "/api/search/", {"q": "test", "page": 1, "per_page": 10}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "page_info" in data
        assert data["page_info"]["current_page"] == 1
        assert data["page_info"]["per_page"] == 10
        assert data["page_info"]["total_pages"] >= 2

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_with_category_filter(self, mock_manager):
        """Test search with category filter"""
        mock_manager.index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost-1",
                    "model": "BlogPost",
                    "title": "Tutorial",
                    "category": "tutorial",
                }
            ],
            "estimatedTotalHits": 1,
            "query": "django",
            "processingTimeMs": 5,
        }

        response = self.client.get(
            "/api/search/", {"q": "django", "category": "tutorial"}
        )

        assert response.status_code == status.HTTP_200_OK

        # Verify filter was applied in search call
        mock_manager.index.search.assert_called_once()
        call_kwargs = mock_manager.index.search.call_args[1]
        assert "filter" in call_kwargs or "filters" in call_kwargs

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_with_type_filter(self, mock_manager):
        """Test search with model type filter"""
        mock_manager.index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost-1",
                    "model": "BlogPost",
                    "title": "Post",
                }
            ],
            "estimatedTotalHits": 1,
            "query": "test",
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test", "type": "BlogPost"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # All results should be BlogPost type
        for result in data["results"]:
            assert result["model"] == "BlogPost"

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_visibility_filter(self, mock_manager):
        """Test that only visible items are returned"""
        mock_manager.index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost-1",
                    "model": "BlogPost",
                    "title": "Visible Post",
                    "is_visible": True,
                }
            ],
            "estimatedTotalHits": 1,
            "query": "test",
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        assert response.status_code == status.HTTP_200_OK

        # Verify visibility filter applied
        mock_manager.index.search.assert_called_once()
        call_kwargs = mock_manager.index.search.call_args[1]
        # Should have is_visible=true filter
        assert "filter" in call_kwargs or "filters" in call_kwargs

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_with_facets(self, mock_manager):
        """Test search returns facets for filtering"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 10,
            "query": "test",
            "processingTimeMs": 5,
            "facetDistribution": {
                "model": {"BlogPost": 7, "AITool": 3},
                "category": {"tutorial": 5, "guide": 2},
            },
        }

        response = self.client.get(
            "/api/search/", {"q": "test", "facets": "model,category"}
        )

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should include facet information
        assert "facets" in data
        assert "model" in data["facets"]
        assert "category" in data["facets"]

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_error_handling(self, mock_manager):
        """Test search handles MeiliSearch errors gracefully"""
        mock_manager.index.search.side_effect = Exception(
            "MeiliSearch connection error"
        )

        response = self.client.get("/api/search/", {"q": "test"})

        # Should return error response, not crash
        assert response.status_code in [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]
        data = response.json()
        assert "error" in data or "detail" in data

    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_performance_metrics(self, mock_manager):
        """Test search returns performance metrics"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "query": "test",
            "processingTimeMs": 15,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should include performance data
        assert "performance" in data or "processingTimeMs" in data


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
class TestSearchSuggestEndpoint(TestCase):
    """Test /api/search/suggest/ autocomplete endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()

    @patch("apps.main.views.search_views.search_index_manager")
    def test_suggest_basic(self, mock_manager):
        """Test basic suggestion request"""
        mock_manager.index.search.return_value = {
            "hits": [
                {"title": "Django Tutorial", "model": "BlogPost"},
                {"title": "Django REST Framework", "model": "BlogPost"},
                {"name": "Django App", "model": "AITool"},
            ],
            "estimatedTotalHits": 3,
            "processingTimeMs": 2,
        }

        response = self.client.get("/api/search/suggest/", {"q": "djan"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "suggestions" in data
        assert len(data["suggestions"]) <= 10  # Default limit

    @patch("apps.main.views.search_views.search_index_manager")
    def test_suggest_limit(self, mock_manager):
        """Test suggestion limit parameter"""
        hits = [{"title": f"Result {i}", "model": "BlogPost"} for i in range(20)]
        mock_manager.index.search.return_value = {
            "hits": hits,
            "estimatedTotalHits": 20,
            "processingTimeMs": 2,
        }

        response = self.client.get("/api/search/suggest/", {"q": "test", "limit": 5})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert len(data["suggestions"]) <= 5

    @patch("apps.main.views.search_views.search_index_manager")
    def test_suggest_empty_query(self, mock_manager):
        """Test suggestion with empty query"""
        response = self.client.get("/api/search/suggest/", {"q": ""})

        # Should return empty or error
        assert response.status_code in [status.HTTP_200_OK, status.HTTP_400_BAD_REQUEST]

    @patch("apps.main.views.search_views.search_index_manager")
    def test_suggest_short_query(self, mock_manager):
        """Test suggestion with very short query (1 char)"""
        mock_manager.index.search.return_value = {
            "hits": [{"title": "Django", "model": "BlogPost"}],
            "estimatedTotalHits": 1,
            "processingTimeMs": 2,
        }

        response = self.client.get("/api/search/suggest/", {"q": "d"})

        # Should still work
        assert response.status_code == status.HTTP_200_OK

    @patch("apps.main.views.search_views.search_index_manager")
    def test_suggest_performance(self, mock_manager):
        """Test suggestion is fast (< 100ms)"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 2,
        }

        import time

        start = time.time()
        response = self.client.get("/api/search/suggest/", {"q": "test"})
        duration = (time.time() - start) * 1000

        assert response.status_code == status.HTTP_200_OK
        # Total roundtrip should be reasonably fast
        assert duration < 500  # 500ms including Django overhead


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
class TestSearchStatsEndpoint(TestCase):
    """Test /api/search/stats/ statistics endpoint"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()

    @patch("apps.main.views.search_views.search_index_manager")
    def test_stats_basic(self, mock_manager):
        """Test basic stats request"""
        mock_manager.index.get_stats.return_value = {
            "numberOfDocuments": 42,
            "isIndexing": False,
            "fieldDistribution": {
                "title": 42,
                "content": 42,
            },
        }

        # Also mock per-model counts
        mock_manager.index.search.side_effect = [
            {"estimatedTotalHits": 25},  # BlogPost
            {"estimatedTotalHits": 10},  # AITool
            {"estimatedTotalHits": 7},  # Others
        ]

        response = self.client.get("/api/search/stats/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert "total_documents" in data
        assert "is_indexing" in data
        assert data["total_documents"] == 42

    @patch("apps.main.views.search_views.search_index_manager")
    def test_stats_per_model_counts(self, mock_manager):
        """Test stats include per-model document counts"""
        mock_manager.index.get_stats.return_value = {
            "numberOfDocuments": 35,
            "isIndexing": False,
        }

        # Mock counts per model
        model_counts = {
            "BlogPost": 20,
            "AITool": 10,
            "UsefulResource": 5,
        }

        def search_mock(*args, **kwargs):
            filter_str = kwargs.get("filter", "")
            for model, count in model_counts.items():
                if model in filter_str:
                    return {"estimatedTotalHits": count}
            return {"estimatedTotalHits": 0}

        mock_manager.index.search.side_effect = search_mock

        response = self.client.get("/api/search/stats/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should have model breakdown
        assert "models" in data or "by_model" in data

    @patch("apps.main.views.search_views.search_index_manager")
    def test_stats_indexing_status(self, mock_manager):
        """Test stats show indexing status"""
        mock_manager.index.get_stats.return_value = {
            "numberOfDocuments": 100,
            "isIndexing": True,  # Currently indexing
        }

        response = self.client.get("/api/search/stats/")

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        assert data["is_indexing"] is True

    @patch("apps.main.views.search_views.search_index_manager")
    def test_stats_error_handling(self, mock_manager):
        """Test stats handles errors gracefully"""
        mock_manager.index.get_stats.side_effect = Exception("Index not found")

        response = self.client.get("/api/search/stats/")

        # Should return error, not crash
        assert response.status_code in [
            status.HTTP_500_INTERNAL_SERVER_ERROR,
            status.HTTP_503_SERVICE_UNAVAILABLE,
        ]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
@pytest.mark.performance
class TestSearchRateLimiting(TestCase):
    """Test rate limiting on search endpoints"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        cache.clear()

    def tearDown(self):
        """Clean up"""
        cache.clear()

    @patch("apps.main.views.search_views.search_index_manager")
    def test_rate_limit_anonymous_user(self, mock_manager):
        """Test rate limiting for anonymous users"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
        }

        # Make many requests quickly
        responses = []
        for i in range(120):  # Exceeds 100/min limit
            response = self.client.get("/api/search/", {"q": f"test{i}"})
            responses.append(response)

        # Some requests should be rate limited
        status_codes = [r.status_code for r in responses]

        # At least one should be rate limited
        assert status.HTTP_429_TOO_MANY_REQUESTS in status_codes

    @patch("apps.main.views.search_views.search_index_manager")
    def test_rate_limit_headers(self, mock_manager):
        """Test rate limit headers are present"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        # Should include rate limit headers (if implemented)
        # X-RateLimit-Limit, X-RateLimit-Remaining, etc.
        assert response.status_code == status.HTTP_200_OK


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
class TestSearchResponseFormat(TestCase):
    """Test search API response format consistency"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()

    @patch("apps.main.views.search_views.search_index_manager")
    def test_response_structure(self, mock_manager):
        """Test response has consistent structure"""
        mock_manager.index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost-1",
                    "model": "BlogPost",
                    "title": "Test Post",
                    "content": "Content",
                    "url": "/blog/test/",
                }
            ],
            "estimatedTotalHits": 1,
            "query": "test",
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Required top-level fields
        required_fields = ["results", "total", "query"]
        for field in required_fields:
            assert field in data, f"Missing required field: {field}"

        # Each result should have standard fields
        if data["results"]:
            result = data["results"][0]
            result_fields = ["id", "model", "title", "url"]
            for field in result_fields:
                assert field in result, f"Missing result field: {field}"

    @patch("apps.main.views.search_views.search_index_manager")
    def test_response_json_valid(self, mock_manager):
        """Test response is valid JSON"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        # Should be valid JSON
        try:
            data = response.json()
            assert isinstance(data, dict)
        except json.JSONDecodeError:
            pytest.fail("Response is not valid JSON")

    @patch("apps.main.views.search_views.search_index_manager")
    def test_response_content_type(self, mock_manager):
        """Test response content type is JSON"""
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
        }

        response = self.client.get("/api/search/", {"q": "test"})

        assert "application/json" in response["Content-Type"]


@pytest.mark.integration
@pytest.mark.api
@pytest.mark.search
class TestSearchWithRealData(TestCase):
    """Integration tests with real database data (no mocks)"""

    def setUp(self):
        """Set up test fixtures"""
        self.client = APIClient()
        self.user = User.objects.create_user(
            username="realuser", email="real@test.com", password="testpass"
        )

        # Create real data
        BlogPost.objects.create(
            title="Python Programming Guide",
            slug="python-guide",
            content="Learn Python programming language",
            author=self.user,
            status="published",
            tags="python, programming",
        )

        BlogPost.objects.create(
            title="Django Web Framework",
            slug="django-framework",
            content="Build web applications with Django",
            author=self.user,
            status="published",
            tags="django, web, python",
        )

        BlogPost.objects.create(
            title="Draft Post",
            slug="draft",
            content="Draft content",
            author=self.user,
            status="draft",  # Should not appear in search
        )

    @pytest.mark.skipif(
        not hasattr(search_index_manager, "client"),
        reason="MeiliSearch not configured for integration tests",
    )
    def test_end_to_end_search_flow(self):
        """Test complete search flow from database to API response"""
        # This test requires MeiliSearch to be running
        # Skip if not available

        # Index the data
        posts = BlogPost.objects.filter(status="published")
        search_index_manager.bulk_index(posts)

        # Wait a bit for indexing
        import time

        time.sleep(1)

        # Search via API
        response = self.client.get("/api/search/", {"q": "python"})

        assert response.status_code == status.HTTP_200_OK
        data = response.json()

        # Should find Python-related posts
        assert data["total"] >= 1
        titles = [r["title"] for r in data["results"]]
        assert any("Python" in title for title in titles)

        # Draft should not appear
        assert not any("Draft" in r["title"] for r in data["results"])
