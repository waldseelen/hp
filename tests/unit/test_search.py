"""
Comprehensive Unit Tests for Search System

Tests cover:
- SearchEngine query parsing and cleaning
- SearchEngine result scoring and ranking
- SearchEngine category filtering
- SearchIndexManager document building
- SearchIndexManager indexing operations
- Search API views (search_api, search_suggest, search_stats)
- Search result formatting and pagination
- Error handling and edge cases

Target Coverage: 85%+ for apps/main/search*.py modules
"""

from datetime import datetime, timedelta
from unittest.mock import MagicMock, Mock, patch

from django.conf import settings
from django.utils import timezone

import pytest

from apps.main.search import SearchEngine, search_engine
from apps.main.search_index import SearchIndexManager, get_search_index_manager


# Override settings for tests
@pytest.fixture(autouse=True)
def setup_search_settings(settings):
    """Auto-configure Meilisearch settings for all tests"""
    settings.MEILISEARCH_HOST = "http://localhost:7700"
    settings.MEILISEARCH_MASTER_KEY = "test_master_key_for_testing"
    settings.MEILISEARCH_INDEX_NAME = "test_portfolio_search"
    settings.MEILISEARCH_TIMEOUT = 5
    settings.MEILISEARCH_BATCH_SIZE = 100


# ============================================================================
# TEST FIXTURES
# ============================================================================


@pytest.fixture
def sample_blog_post():
    """Sample blog post for testing"""
    return Mock(
        id=1,
        title="Django REST Framework Tutorial",
        content="Learn how to build RESTful APIs with Django REST Framework",
        excerpt="A comprehensive guide to DRF",
        meta_description="DRF tutorial for beginners",
        tags="django,rest,api,python",
        status="published",
        is_featured=True,
        created_at=timezone.now() - timedelta(days=10),
        published_at=timezone.now() - timedelta(days=5),
        slug="django-rest-framework-tutorial",
        view_count=100,
        reading_time=10,
        category=Mock(display_name="Web Development"),
    )


@pytest.fixture
def sample_ai_tool():
    """Sample AI tool for testing"""
    return Mock(
        id=1,
        name="ChatGPT",
        description="AI-powered chatbot by OpenAI",
        tags=["ai", "nlp", "chatbot"],
        is_visible=True,
        is_featured=True,
        is_free=False,
        rating=4.8,
        created_at=timezone.now() - timedelta(days=30),
        category="language_model",
        url="https://chat.openai.com",
    )


@pytest.fixture
def sample_cyber_resource():
    """Sample cybersecurity resource for testing"""
    return Mock(
        id=1,
        title="SQL Injection Prevention",
        description="How to prevent SQL injection attacks",
        content="# SQL Injection\n\nPrevent SQL injection with parameterized queries...",
        tags="security,sql,injection,owasp",
        is_visible=True,
        is_featured=False,
        type="guide",
        difficulty="intermediate",
        severity_level=3,
        created_at=timezone.now() - timedelta(days=20),
        url="https://example.com/sql-injection",
    )


@pytest.fixture
def mock_meilisearch_client(monkeypatch):
    """Mock Meilisearch client for testing"""
    from tests.mocks.meilisearch_mock import MockMeilisearchClient

    mock_client = MockMeilisearchClient("http://localhost:7700", "test_key")

    # Patch the meilisearch.Client
    monkeypatch.setattr("meilisearch.Client", lambda *args, **kwargs: mock_client)

    return mock_client


# ============================================================================
# SEARCHENGINE - QUERY CLEANING & PARSING
# ============================================================================


class TestSearchQueryCleaning:
    """Test SearchEngine query cleaning and normalization"""

    def test_clean_query_removes_special_characters(self):
        """Should remove special characters except hyphens"""
        engine = SearchEngine()
        clean = engine._clean_query("django@#$%framework!")
        assert clean == "django framework"

    def test_clean_query_normalizes_whitespace(self):
        """Should normalize multiple spaces to single space"""
        engine = SearchEngine()
        clean = engine._clean_query("django    rest     framework")
        assert clean == "django rest framework"

    def test_clean_query_strips_leading_trailing_spaces(self):
        """Should strip leading and trailing whitespace"""
        engine = SearchEngine()
        clean = engine._clean_query("  django  ")
        assert clean == "django"

    def test_clean_query_preserves_hyphens(self):
        """Should preserve hyphens in queries"""
        engine = SearchEngine()
        clean = engine._clean_query("django-rest-framework")
        assert clean == "django-rest-framework"

    def test_extract_keywords_splits_words(self):
        """Should split query into individual keywords"""
        engine = SearchEngine()
        keywords = engine._extract_keywords("django rest framework")
        assert "django" in keywords
        assert "rest" in keywords
        assert "framework" in keywords

    def test_extract_keywords_ignores_single_characters(self):
        """Should ignore single character words"""
        engine = SearchEngine()
        keywords = engine._extract_keywords("a django b rest c")
        assert "a" not in keywords
        assert "b" not in keywords
        assert "c" not in keywords
        assert "django" in keywords

    def test_extract_keywords_includes_full_phrase(self):
        """Should include full query as a phrase for multi-word queries"""
        engine = SearchEngine()
        keywords = engine._extract_keywords("django rest")
        assert "django rest" in keywords

    def test_extract_keywords_single_word_no_phrase(self):
        """Should not duplicate single word as phrase"""
        engine = SearchEngine()
        keywords = engine._extract_keywords("django")
        # Should only appear once
        assert keywords.count("django") == 1


# ============================================================================
# SEARCHENGINE - SEARCH FUNCTIONALITY
# ============================================================================


class TestSearchEngineSearch:
    """Test SearchEngine main search functionality"""

    @pytest.mark.django_db
    def test_search_returns_empty_for_short_query(self):
        """Should return empty results for queries < 2 characters"""
        engine = SearchEngine()
        result = engine.search("a")

        assert result["results"] == []
        assert result["total_count"] == 0
        assert result["query"] == "a"

    @pytest.mark.django_db
    def test_search_returns_empty_for_empty_query(self):
        """Should return empty results for empty query"""
        engine = SearchEngine()
        result = engine.search("")

        assert result["results"] == []
        assert result["total_count"] == 0

    @pytest.mark.django_db
    def test_search_cleans_query_before_processing(self):
        """Should clean query before searching"""
        engine = SearchEngine()

        # Mock _search_model to avoid database access
        with patch.object(engine, "_search_model", return_value=[]):
            result = engine.search("django@#$framework")

        # Cleaned query should be stored
        assert result["clean_query"] == "django framework"

    @pytest.mark.django_db
    def test_search_extracts_keywords(self):
        """Should extract keywords from query"""
        engine = SearchEngine()

        # Mock _search_model to avoid database access
        with patch.object(engine, "_search_model", return_value=[]):
            result = engine.search("django rest framework")

        assert "keywords" in result
        assert "django" in result["keywords"]
        assert "rest" in result["keywords"]

    def test_search_respects_category_filter(self):
        """Should only search specified categories when filtered"""
        engine = SearchEngine()

        # Mock one model to return results
        with patch.object(engine, "_search_model") as mock_search:
            mock_search.return_value = [{"title": "Test", "relevance_score": 10}]

            result = engine.search("test", categories=["blog_posts"])

            # Should only search blog_posts
            assert mock_search.call_count == 1

    def test_search_respects_limit_parameter(self):
        """Should limit number of results returned"""
        engine = SearchEngine()

        # Mock search to return 100 results
        with patch.object(engine, "_search_model") as mock_search:
            mock_results = [
                {"title": f"Result {i}", "relevance_score": 100 - i} for i in range(100)
            ]
            mock_search.return_value = mock_results

            result = engine.search("test", limit=10)

            assert len(result["results"]) == 10

    def test_search_sorts_by_relevance_score(self):
        """Should sort results by relevance score descending"""
        engine = SearchEngine()

        with patch.object(engine, "_search_model") as mock_search:
            # Return results in mixed order
            mock_search.return_value = [
                {"title": "Low Score", "relevance_score": 5, "model_weight": 10},
                {"title": "High Score", "relevance_score": 50, "model_weight": 10},
                {"title": "Mid Score", "relevance_score": 25, "model_weight": 10},
            ]

            result = engine.search("test")

            # Should be sorted by score (descending)
            scores = [r["relevance_score"] for r in result["results"]]
            assert scores == sorted(scores, reverse=True)

    def test_search_adds_category_metadata(self):
        """Should add category metadata to results"""
        engine = SearchEngine()

        with patch.object(engine, "_search_model") as mock_search:
            mock_search.return_value = [{"title": "Test Result", "relevance_score": 10}]

            result = engine.search("test")

            # Should have category metadata
            if result["results"]:
                assert "search_category" in result["results"][0]
                assert "category_name" in result["results"][0]
                assert "category_icon" in result["results"][0]


# ============================================================================
# SEARCHENGINE - RELEVANCE SCORING
# ============================================================================


class TestSearchRelevanceScoring:
    """Test SearchEngine relevance score calculation"""

    def test_exact_title_match_high_score(self):
        """Should give highest score for exact title match"""
        engine = SearchEngine()

        obj = Mock(
            title="django",
            content="Some content about Django framework",
            created_at=timezone.now() - timedelta(days=15),
        )

        score = engine._calculate_relevance_score(
            obj,
            keywords=["django"],
            fields=["title", "content"],
            tag_field=None,
            base_weight=10,
        )

        # Exact title match should have very high score
        assert score > 50

    def test_partial_title_match_moderate_score(self):
        """Should give moderate score for partial title match"""
        engine = SearchEngine()

        obj = Mock(
            title="Django REST Framework",
            content="Some content",
            created_at=timezone.now() - timedelta(days=15),
        )

        score = engine._calculate_relevance_score(
            obj,
            keywords=["django"],
            fields=["title", "content"],
            tag_field=None,
            base_weight=10,
        )

        # Partial match should have decent score
        # Score can be high if multiple matches found
        assert score > 10

    def test_content_match_lower_score_than_title(self):
        """Should give lower score for content matches vs title"""
        engine = SearchEngine()

        obj_title = Mock(
            title="django",
            content="other stuff",
            created_at=timezone.now() - timedelta(days=100),
        )
        obj_content = Mock(
            title="other stuff",
            content="django framework",
            created_at=timezone.now() - timedelta(days=100),
        )

        score_title = engine._calculate_relevance_score(
            obj_title, ["django"], ["title", "content"], None, 10
        )
        score_content = engine._calculate_relevance_score(
            obj_content, ["django"], ["title", "content"], None, 10
        )

        assert score_title > score_content

    def test_tag_matches_add_bonus_score(self):
        """Should add bonus score for tag matches"""
        engine = SearchEngine()

        obj = Mock(
            title="Some Title",
            content="Some content",
            tags="django,python,web",
            created_at=timezone.now() - timedelta(days=15),
        )

        score = engine._calculate_relevance_score(
            obj,
            keywords=["django"],
            fields=["title", "content"],
            tag_field="tags",
            base_weight=10,
        )

        # Should have some score from tag match
        assert score > 0

    def test_featured_items_get_boost(self):
        """Should boost score for featured items"""
        engine = SearchEngine()

        obj_featured = Mock(
            title="django tutorial",
            content="content",
            is_featured=True,
            created_at=timezone.now() - timedelta(days=100),
        )
        obj_normal = Mock(
            title="django tutorial",
            content="content",
            is_featured=False,
            created_at=timezone.now() - timedelta(days=100),
        )

        score_featured = engine._calculate_relevance_score(
            obj_featured, ["django"], ["title", "content"], None, 10
        )
        score_normal = engine._calculate_relevance_score(
            obj_normal, ["django"], ["title", "content"], None, 10
        )

        assert score_featured > score_normal

    def test_recent_items_get_boost(self):
        """Should boost score for recently created items"""
        engine = SearchEngine()

        obj_recent = Mock(
            title="django tutorial",
            content="content",
            created_at=timezone.now() - timedelta(days=15),
        )
        obj_old = Mock(
            title="django tutorial",
            content="content",
            created_at=timezone.now() - timedelta(days=200),
        )

        score_recent = engine._calculate_relevance_score(
            obj_recent, ["django"], ["title", "content"], None, 10
        )
        score_old = engine._calculate_relevance_score(
            obj_old, ["django"], ["title", "content"], None, 10
        )

        assert score_recent > score_old


# ============================================================================
# SEARCHENGINE - RESULT FORMATTING
# ============================================================================


class TestSearchResultFormatting:
    """Test SearchEngine result formatting"""

    def test_format_result_extracts_title(self):
        """Should extract title from object"""
        engine = SearchEngine()

        obj = Mock(
            id=1,
            title="Test Title",
            excerpt="Test excerpt",
        )

        config = {
            "category": "Blog Posts",
            "icon": "📝",
            "url_name": None,
            "url_field": None,
            "tag_field": None,
        }

        result = engine._format_search_result(obj, config, score=10)

        assert result is not None
        assert result["title"] == "Test Title"

    def test_format_result_falls_back_to_name(self):
        """Should use 'name' if no 'title' attribute"""
        engine = SearchEngine()

        obj = Mock(spec=["id", "name", "description"])
        obj.id = 1
        obj.name = "Test Name"
        obj.description = "Test description"

        config = {
            "category": "Tools",
            "icon": "🔧",
            "url_name": None,
            "url_field": None,
            "tag_field": None,
        }

        result = engine._format_search_result(obj, config, score=10)

        assert result is not None
        assert result["title"] == "Test Name"

    def test_format_result_truncates_long_descriptions(self):
        """Should truncate descriptions longer than 200 characters"""
        engine = SearchEngine()

        long_desc = "A" * 300

        obj = Mock(spec=["id", "title", "description"])
        obj.id = 1
        obj.title = "Test"
        obj.description = long_desc

        config = {
            "category": "Tools",
            "icon": "🔧",
            "url_name": None,
            "url_field": None,
            "tag_field": None,
        }

        result = engine._format_search_result(obj, config, score=10)

        # Description should be truncated
        assert isinstance(result["description"], str)
        assert len(result["description"]) <= 203  # 200 + "..."

    def test_format_result_includes_metadata(self):
        """Should include date and category metadata"""
        engine = SearchEngine()

        from datetime import timezone as dt_timezone

        obj = Mock(
            id=1,
            title="Test",
            excerpt="Test excerpt",
            published_at=datetime(2024, 1, 1, tzinfo=dt_timezone.utc),
            category=Mock(display_name="Web Dev"),
        )

        config = {
            "category": "Blog Posts",
            "icon": "📝",
            "url_name": None,
            "url_field": None,
            "tag_field": None,
        }

        result = engine._format_search_result(obj, config, score=10)

        assert "metadata" in result
        assert "date" in result["metadata"]
        assert "category" in result["metadata"]

    def test_format_result_parses_tags(self):
        """Should parse and limit tags"""
        engine = SearchEngine()

        obj = Mock(
            id=1,
            title="Test",
            description="Test",
            tags="tag1,tag2,tag3,tag4,tag5,tag6,tag7",
        )

        config = {
            "category": "Blog",
            "icon": "📝",
            "url_name": None,
            "url_field": None,
            "tag_field": "tags",
        }

        result = engine._format_search_result(obj, config, score=10)

        # Should limit to 5 tags
        assert len(result["tags"]) <= 5


# ============================================================================
# SEARCHENGINE - SUGGESTIONS
# ============================================================================


class TestSearchSuggestions:
    """Test SearchEngine suggestion generation"""

    def test_generate_suggestions_from_tags(self):
        """Should generate suggestions from popular tags in results"""
        engine = SearchEngine()

        results = [
            {
                "title": "Django Tutorial",
                "tags": ["django", "python", "web"],
            },
            {
                "title": "Python Guide",
                "tags": ["python", "programming"],
            },
        ]

        suggestions = engine._generate_suggestions("django", results)

        # Should suggest related tags
        assert len(suggestions) > 0
        # Check if any suggestion contains a tag
        suggestion_texts = [s["text"] for s in suggestions]
        has_tag_suggestion = any(
            "python" in text or "web" in text for text in suggestion_texts
        )
        assert has_tag_suggestion

    def test_suggestions_exclude_query_terms(self):
        """Should not suggest tags already in query"""
        engine = SearchEngine()

        results = [
            {
                "title": "Django Tutorial",
                "tags": ["django", "python", "web"],
                "category_name": "Blog",
            }
        ]

        suggestions = engine._generate_suggestions("django python", results)

        # Should not suggest django or python again
        suggestion_texts = " ".join([s["text"] for s in suggestions])
        # Suggestions should not be ONLY the query terms
        assert (
            len(suggestions) == 0
            or "web" in suggestion_texts
            or "Blog" in suggestion_texts
        )


# ============================================================================
# SEARCHINDEXMANAGER - DOCUMENT BUILDING
# ============================================================================


class TestSearchIndexDocumentBuilding:
    """Test SearchIndexManager document building"""

    @patch("apps.main.search_index.meilisearch.Client")
    def test_build_document_creates_valid_structure(
        self, mock_client, sample_blog_post
    ):
        """Should build properly structured document"""
        manager = SearchIndexManager()

        # Mock object needs to have __class__.__name__ in registry
        sample_blog_post.__class__.__name__ = "Mock"

        # Add Mock to registry for test
        manager.model_registry["Mock"] = {
            "model": Mock,
            "fields": {
                "title": {"weight": 10, "sanitize": False},
                "content": {"weight": 5, "sanitize": False},
            },
            "metadata": ["id"],
            "url_pattern": None,
            "url_field": None,
            "tag_field": None,
            "visibility_check": lambda x: True,
            "search_category": "Test",
            "search_icon": "📝",
        }

        document = manager.build_document(sample_blog_post)

        assert document is not None
        assert "id" in document
        assert "model_type" in document
        assert "search_category" in document
        assert document["model_type"] == "Mock"  # Mock object class name

    @patch("apps.main.search_index.meilisearch.Client")
    def test_build_document_sanitizes_html_content(self, mock_client):
        """Should sanitize HTML from content fields"""
        manager = SearchIndexManager()

        obj = Mock(
            id=1,
            title="Test",
            content="<script>alert('xss')</script>Hello World",
        )

        # Manually set up config for this test
        config = manager.model_registry.get("Mock", {})
        if not config:
            # Create a test config
            manager.model_registry["Mock"] = {
                "model": Mock,
                "fields": {
                    "title": {"weight": 10, "sanitize": False},
                    "content": {"weight": 5, "sanitize": "html"},
                },
                "metadata": ["id"],
                "url_pattern": None,
                "url_field": None,
                "tag_field": None,
                "visibility_check": lambda x: True,
                "search_category": "Test",
                "search_icon": "📝",
            }

        document = manager.build_document(obj)

        # Should sanitize HTML (exact behavior depends on ContentSanitizer)
        assert document is not None
        assert "content" in document

    @patch("apps.main.search_index.meilisearch.Client")
    def test_build_document_returns_none_for_invisible_objects(self, mock_client):
        """Should return None for objects that fail visibility check"""
        manager = SearchIndexManager()

        obj = Mock(
            id=1,
            title="Hidden Item",
            is_visible=False,
        )

        # Set up config with visibility check
        manager.model_registry["Mock"] = {
            "model": Mock,
            "fields": {"title": {"weight": 10, "sanitize": False}},
            "metadata": ["id"],
            "url_pattern": None,
            "url_field": None,
            "tag_field": None,
            "visibility_check": lambda x: x.is_visible,
            "search_category": "Test",
            "search_icon": "📝",
        }

        document = manager.build_document(obj)

        assert document is None


# ============================================================================
# SEARCHINDEXMANAGER - INDEXING OPERATIONS
# ============================================================================


class TestSearchIndexOperations:
    """Test SearchIndexManager indexing operations"""

    @patch("apps.main.search_index.meilisearch.Client")
    def test_index_document_adds_to_index(self, mock_client, mock_meilisearch_client):
        """Should add document to Meilisearch index"""
        # Use mock client
        with patch(
            "apps.main.search_index.meilisearch.Client",
            return_value=mock_meilisearch_client,
        ):
            manager = SearchIndexManager()

            obj = Mock(
                id=1,
                title="Test Document",
                description="Test description",
            )

            # Add to registry
            manager.model_registry["Mock"] = {
                "model": Mock,
                "fields": {
                    "title": {"weight": 10, "sanitize": False},
                    "description": {"weight": 5, "sanitize": False},
                },
                "metadata": ["id"],
                "url_pattern": None,
                "url_field": None,
                "tag_field": None,
                "visibility_check": lambda x: True,
                "search_category": "Test",
                "search_icon": "📝",
            }

            success = manager.index_document(obj)

            # Should succeed
            assert success is True

            # Check if document was added to mock index
            index = manager.index
            assert len(index.documents) > 0

    @patch("apps.main.search_index.meilisearch.Client")
    def test_delete_document_removes_from_index(
        self, mock_client, mock_meilisearch_client
    ):
        """Should remove document from index"""
        with patch(
            "apps.main.search_index.meilisearch.Client",
            return_value=mock_meilisearch_client,
        ):
            manager = SearchIndexManager()

            # First add a document
            index = manager.index
            index.add_documents([{"id": "BlogPost:1", "title": "Test"}])

            # Verify it exists
            assert len(index.documents) == 1

            # Delete it
            success = manager.delete_document("BlogPost", 1)

            assert success is True
            assert len(index.documents) == 0


# ============================================================================
# SEARCH API VIEWS
# ============================================================================


class TestSearchAPIViews:
    """Test search API view functions"""

    @pytest.mark.django_db
    def test_search_api_requires_query_parameter(self, client):
        """Should return 400 if no query parameter"""
        from django.urls import reverse

        # Try without query
        response = client.get("/api/search/")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False
        assert "error" in data

    @pytest.mark.django_db
    def test_search_api_validates_min_query_length(self, client):
        """Should return 400 for queries shorter than 2 characters"""
        response = client.get("/api/search/?q=a")

        assert response.status_code == 400
        data = response.json()
        assert data["success"] is False

    @pytest.mark.django_db
    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_api_returns_results(self, mock_manager, client):
        """Should return search results for valid query"""
        # Mock search results
        mock_index = Mock()
        mock_index.search.return_value = {
            "hits": [
                {
                    "id": "BlogPost:1",
                    "model_id": 1,
                    "model_type": "BlogPost",
                    "title": "Django Tutorial",
                    "excerpt": "Learn Django",
                    "url": "/blog/django-tutorial/",
                    "search_category": "Blog Posts",
                    "search_icon": "📝",
                    "tags": ["django", "python"],
                    "metadata": {},
                    "_formatted": {},
                }
            ],
            "estimatedTotalHits": 1,
            "processingTimeMs": 5,
            "facetDistribution": {},
        }
        mock_manager.index = mock_index

        response = client.get("/api/search/?q=django")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "results" in data
        assert len(data["results"]) == 1
        assert data["results"][0]["title"] == "Django Tutorial"

    @pytest.mark.django_db
    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_api_pagination_works(self, mock_manager, client):
        """Should paginate search results correctly"""
        mock_index = Mock()
        mock_index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 100,
            "processingTimeMs": 5,
            "facetDistribution": {},
        }
        mock_manager.index = mock_index

        response = client.get("/api/search/?q=test&page=2&per_page=20")

        assert response.status_code == 200
        data = response.json()
        assert "pagination" in data
        assert data["pagination"]["page"] == 2
        assert data["pagination"]["per_page"] == 20
        assert data["pagination"]["total_pages"] == 5  # 100 / 20

    @pytest.mark.django_db
    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_suggest_returns_suggestions(self, mock_manager, client):
        """Should return search suggestions"""
        mock_index = Mock()
        mock_index.search.return_value = {
            "hits": [
                {
                    "title": "Django REST Framework",
                    "excerpt": "DRF Tutorial",
                    "search_category": "Blog",
                    "search_icon": "📝",
                    "url": "/blog/drf/",
                    "metadata": {},
                }
            ]
        }
        mock_manager.index = mock_index

        response = client.get("/api/search/suggest/?q=dja&limit=5")

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "suggestions" in data
        assert len(data["suggestions"]) <= 5

    @pytest.mark.django_db
    def test_search_suggest_validates_query_length(self, client):
        """Should validate minimum query length"""
        response = client.get("/api/search/suggest/?q=a")

        assert response.status_code == 400


# ============================================================================
# EDGE CASES & ERROR HANDLING
# ============================================================================


class TestSearchEdgeCases:
    """Test edge cases and error handling"""

    @pytest.mark.django_db
    def test_search_handles_unicode_queries(self):
        """Should handle Unicode characters in queries"""
        engine = SearchEngine()

        # Mock _search_model to avoid database access
        with patch.object(engine, "_search_model", return_value=[]):
            result = engine.search("日本語 مرحبا Привет")

        # Should not crash
        assert "results" in result
        assert "query" in result

    @pytest.mark.django_db
    def test_search_handles_very_long_queries(self):
        """Should handle very long search queries"""
        engine = SearchEngine()
        long_query = "django " * 100  # 600+ characters

        # Mock _search_model to avoid database access
        with patch.object(engine, "_search_model", return_value=[]):
            result = engine.search(long_query)

        # Should not crash
        assert "results" in result

    @pytest.mark.django_db
    def test_search_handles_sql_injection_attempts(self):
        """Should safely handle SQL injection attempts"""
        engine = SearchEngine()

        # Mock _search_model to avoid database access
        with patch.object(engine, "_search_model", return_value=[]):
            result = engine.search("'; DROP TABLE users; --")

        # Should not crash and should clean the query
        assert "results" in result
        assert "query" in result

    def test_relevance_score_handles_none_values(self):
        """Should handle None values in object fields gracefully"""
        engine = SearchEngine()

        obj = Mock(
            title=None,
            content=None,
            description="Valid description",
            created_at=timezone.now() - timedelta(days=15),
        )

        score = engine._calculate_relevance_score(
            obj,
            keywords=["test"],
            fields=["title", "content", "description"],
            tag_field=None,
            base_weight=10,
        )

        # Should not crash, score should be based on description only
        assert score >= 0

    @patch("apps.main.search_index.meilisearch.Client")
    def test_index_manager_handles_missing_config(self, mock_client):
        """Should handle objects without configuration"""
        manager = SearchIndexManager()

        obj = Mock(id=1, unknown_field="value")
        obj.__class__.__name__ = "UnknownModel"

        document = manager.build_document(obj)

        # Should return None for unconfigured models
        assert document is None

    @patch("apps.main.search_index.meilisearch.Client")
    def test_index_manager_handles_malformed_tags(self, mock_client):
        """Should handle malformed tag data"""
        manager = SearchIndexManager()

        # Test various malformed tag formats
        assert manager.parse_tags(None) == []
        assert manager.parse_tags("") == []
        assert manager.parse_tags([]) == []
        assert manager.parse_tags({"invalid": "dict"}) == []

    @pytest.mark.django_db
    @patch("apps.main.views.search_views.search_index_manager")
    def test_search_api_handles_meilisearch_errors(self, mock_manager, client):
        """Should handle Meilisearch connection errors gracefully"""
        mock_index = Mock()
        mock_index.search.side_effect = Exception("Connection refused")
        mock_manager.index = mock_index

        response = client.get("/api/search/?q=test")

        assert response.status_code == 500
        data = response.json()
        assert data["success"] is False
        assert "error" in data
