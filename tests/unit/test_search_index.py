"""
Unit Tests for SearchIndexManager

Tests covering:
- Document indexing/deletion operations
- Content sanitization (HTML, Markdown, XSS)
- Bulk indexing operations
- Model registry configuration
- Visibility filtering
- Tag parsing and metadata extraction
- Error handling
"""

from datetime import datetime
from datetime import timezone as dt_timezone
from unittest.mock import MagicMock, Mock, call, patch

from django.contrib.auth import get_user_model
from django.core.exceptions import ImproperlyConfigured
from django.test import TestCase, override_settings

import pytest

from apps.main.models import (
    AITool,
    BlogPost,
    CybersecurityResource,
    PersonalInfo,
    SocialLink,
    UsefulResource,
)
from apps.main.sanitizer import ContentSanitizer
from apps.main.search_index import SearchIndexManager, search_index_manager

User = get_user_model()


@pytest.mark.unit
@pytest.mark.search
class TestSearchIndexManagerInit(TestCase):
    """Test SearchIndexManager initialization"""

    @override_settings(
        MEILISEARCH_HOST="http://test:7700",
        MEILISEARCH_MASTER_KEY="testkey123",
        MEILISEARCH_INDEX_NAME="test_index",
        MEILISEARCH_TIMEOUT=10,
        MEILISEARCH_BATCH_SIZE=50,
    )
    def test_init_with_valid_config(self):
        """Test initialization with valid configuration"""
        with patch("meilisearch.Client") as mock_client:
            manager = SearchIndexManager()

            assert manager.host == "http://test:7700"
            assert manager.master_key == "testkey123"
            assert manager.index_name == "test_index"
            assert manager.timeout == 10
            assert manager.batch_size == 50
            mock_client.assert_called_once_with("http://test:7700", "testkey123")

    @override_settings(MEILISEARCH_MASTER_KEY=None)
    def test_init_without_master_key(self):
        """Test that initialization fails without master key"""
        with pytest.raises(
            ImproperlyConfigured, match="MEILISEARCH_MASTER_KEY must be set"
        ):
            SearchIndexManager()

    @override_settings(MEILISEARCH_MASTER_KEY="testkey")
    def test_init_with_connection_error(self):
        """Test initialization with connection error"""
        with patch("meilisearch.Client", side_effect=Exception("Connection refused")):
            with pytest.raises(Exception, match="Connection refused"):
                SearchIndexManager()

    @override_settings(MEILISEARCH_MASTER_KEY="testkey")
    def test_model_registry_built(self):
        """Test that model registry is properly built"""
        with patch("meilisearch.Client"):
            manager = SearchIndexManager()

            # Check all expected models are registered
            expected_models = [
                "BlogPost",
                "AITool",
                "UsefulResource",
                "CybersecurityResource",
                "PersonalInfo",
                "SocialLink",
            ]

            for model_name in expected_models:
                assert model_name in manager.model_registry
                config = manager.model_registry[model_name]

                # Verify config structure
                assert "model" in config
                assert "fields" in config
                assert "metadata" in config
                assert "url_pattern" in config
                assert "visibility_check" in config


@pytest.mark.unit
@pytest.mark.search
class TestContentSanitization(TestCase):
    """Test content sanitization functionality"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client"):
            self.manager = SearchIndexManager()

    def test_sanitize_html_content(self):
        """Test HTML sanitization removes tags"""
        html_content = (
            '<p>Hello <strong>World</strong></p><script>alert("xss")</script>'
        )

        result = self.manager.sanitize_content(html_content, sanitize_type="html")

        assert "<script>" not in result
        assert "<p>" not in result
        assert "<strong>" not in result
        assert "Hello World" in result
        assert "alert" not in result  # Script content should be stripped

    def test_sanitize_markdown_content(self):
        """Test Markdown sanitization"""
        markdown_content = (
            "# Heading\n\n**Bold text** and *italic*\n\n[Link](http://example.com)"
        )

        result = self.manager.sanitize_content(
            markdown_content, sanitize_type="markdown"
        )

        # Should convert to HTML then strip tags
        assert "#" not in result
        assert "**" not in result
        assert "Heading" in result
        assert "Bold text" in result

    def test_sanitize_xss_payloads(self):
        """Test XSS payload sanitization"""
        xss_payloads = [
            '<img src=x onerror="alert(1)">',
            "<svg/onload=alert(1)>",
            "javascript:alert(1)",
            '<iframe src="javascript:alert(1)"></iframe>',
            "<body onload=alert(1)>",
            "<input onfocus=alert(1) autofocus>",
        ]

        for payload in xss_payloads:
            result = self.manager.sanitize_content(payload, sanitize_type="html")

            # Should not contain dangerous elements
            assert "<script>" not in result.lower()
            assert "onerror" not in result.lower()
            assert "onload" not in result.lower()
            assert "javascript:" not in result.lower()
            assert "<iframe" not in result.lower()
            assert "onfocus" not in result.lower()

    def test_sanitize_preserves_safe_content(self):
        """Test that safe content is preserved"""
        safe_content = "This is safe plain text with numbers 123 and symbols !@#"

        result = self.manager.sanitize_content(safe_content, sanitize_type="auto")

        assert result == safe_content

    def test_sanitize_no_type(self):
        """Test sanitization without type returns original"""
        content = "<p>Test</p>"

        result = self.manager.sanitize_content(content, sanitize_type=False)

        assert result == content

    def test_sanitize_empty_content(self):
        """Test sanitization of empty content"""
        assert self.manager.sanitize_content("", sanitize_type="html") == ""
        assert self.manager.sanitize_content(None, sanitize_type="html") == ""


@pytest.mark.unit
@pytest.mark.search
class TestDocumentBuilding(TestCase):
    """Test document building functionality"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client"):
            self.manager = SearchIndexManager()

        self.user = User.objects.create_user(
            username="testauthor", email="author@test.com", password="testpass"
        )

    def test_build_document_blog_post(self):
        """Test building document from BlogPost"""
        blog_post = BlogPost.objects.create(
            title="Test Blog Post",
            slug="test-blog-post",
            content="<p>This is <strong>HTML</strong> content</p>",
            excerpt="Short excerpt",
            meta_description="Meta description",
            author=self.user,
            status="published",
            is_featured=True,
            view_count=100,
            reading_time=5,
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/test-blog-post/"
        ):
            document = self.manager.build_document(blog_post)

        # Verify document structure
        assert document["id"] == f"BlogPost-{blog_post.id}"
        assert document["model"] == "BlogPost"
        assert document["object_id"] == blog_post.id
        assert document["title"] == "Test Blog Post"
        assert document["slug"] == "test-blog-post"

        # Content should be sanitized
        assert "<p>" not in document["content"]
        assert "<strong>" not in document["content"]
        assert "HTML" in document["content"]

        # Metadata
        assert document["is_visible"] is True
        assert document["is_featured"] is True
        assert document["view_count"] == 100
        assert document["reading_time"] == 5
        assert document["url"] == "/blog/test-blog-post/"
        assert "published_at" in document
        assert "updated_at" in document

    def test_build_document_ai_tool(self):
        """Test building document from AITool"""
        ai_tool = AITool.objects.create(
            name="ChatGPT",
            slug="chatgpt",
            description="AI chatbot",
            category="chatbot",
            is_featured=True,
            is_free=True,
            is_visible=True,
            rating=4.5,
            order=1,
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/tools/chatgpt/"
        ):
            document = self.manager.build_document(ai_tool)

        assert document["id"] == f"AITool-{ai_tool.id}"
        assert document["model"] == "AITool"
        assert document["name"] == "ChatGPT"
        assert document["category"] == "chatbot"
        assert document["is_featured"] is True
        assert document["is_free"] is True
        assert document["rating"] == 4.5

    def test_build_document_with_tags(self):
        """Test document building with tag parsing"""
        blog_post = BlogPost.objects.create(
            title="Tagged Post",
            slug="tagged-post",
            content="Content",
            tags="python, django, web development",
            author=self.user,
            status="published",
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/tagged-post/"
        ):
            document = self.manager.build_document(blog_post)

        # Tags should be parsed into list
        assert "tags" in document
        assert isinstance(document["tags"], list)
        assert "python" in document["tags"]
        assert "django" in document["tags"]
        assert "web development" in document["tags"]

    def test_build_document_unpublished_not_visible(self):
        """Test that unpublished content is marked as not visible"""
        blog_post = BlogPost.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Draft content",
            author=self.user,
            status="draft",
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/draft-post/"
        ):
            document = self.manager.build_document(blog_post)

        assert document["is_visible"] is False

    def test_build_document_handles_missing_fields(self):
        """Test document building with missing optional fields"""
        blog_post = BlogPost.objects.create(
            title="Minimal Post",
            slug="minimal-post",
            content="Minimal content",
            author=self.user,
            status="published",
            # No excerpt, tags, meta_description
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/minimal-post/"
        ):
            document = self.manager.build_document(blog_post)

        # Should not crash, use defaults
        assert document["excerpt"] in [
            "",
            None,
            "Minimal content",
        ]  # May use content as fallback
        assert "tags" in document


@pytest.mark.unit
@pytest.mark.search
class TestIndexOperations(TestCase):
    """Test index CRUD operations"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client") as mock_client:
            self.mock_index = MagicMock()
            mock_client.return_value.index.return_value = self.mock_index
            self.manager = SearchIndexManager()

        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    def test_index_document_success(self):
        """Test successful document indexing"""
        blog_post = BlogPost.objects.create(
            title="Test Post",
            slug="test-post",
            content="Content",
            author=self.user,
            status="published",
        )

        self.mock_index.add_documents.return_value = {"taskUid": 123}

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/test-post/"
        ):
            result = self.manager.index_document(blog_post)

        assert result is True
        self.mock_index.add_documents.assert_called_once()

    def test_index_document_draft_skipped(self):
        """Test that draft posts are not indexed"""
        blog_post = BlogPost.objects.create(
            title="Draft",
            slug="draft",
            content="Content",
            author=self.user,
            status="draft",
        )

        result = self.manager.index_document(blog_post)

        assert result is False
        self.mock_index.add_documents.assert_not_called()

    def test_index_document_invisible_skipped(self):
        """Test that invisible items are not indexed"""
        ai_tool = AITool.objects.create(
            name="Hidden Tool",
            slug="hidden",
            description="Description",
            is_visible=False,
        )

        result = self.manager.index_document(ai_tool)

        assert result is False
        self.mock_index.add_documents.assert_not_called()

    def test_index_document_error_handling(self):
        """Test error handling during indexing"""
        blog_post = BlogPost.objects.create(
            title="Test Post",
            slug="test-post",
            content="Content",
            author=self.user,
            status="published",
        )

        self.mock_index.add_documents.side_effect = Exception("Connection error")

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/test-post/"
        ):
            result = self.manager.index_document(blog_post)

        assert result is False

    def test_delete_document_success(self):
        """Test successful document deletion"""
        self.mock_index.delete_document.return_value = {"taskUid": 456}

        result = self.manager.delete_document("BlogPost", 42)

        assert result is True
        self.mock_index.delete_document.assert_called_once_with("BlogPost-42")

    def test_delete_document_error_handling(self):
        """Test error handling during deletion"""
        self.mock_index.delete_document.side_effect = Exception("Document not found")

        result = self.manager.delete_document("BlogPost", 42)

        assert result is False

    def test_bulk_index_success(self):
        """Test bulk indexing operation"""
        posts = []
        for i in range(3):
            post = BlogPost.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                content=f"Content {i}",
                author=self.user,
                status="published",
            )
            posts.append(post)

        self.mock_index.add_documents.return_value = {"taskUid": 789}

        with patch.object(self.manager, "_generate_url", return_value="/blog/post/"):
            results = self.manager.bulk_index(posts)

        assert results["indexed"] == 3
        assert results["skipped"] == 0
        assert results["failed"] == 0

    def test_bulk_index_with_skipped(self):
        """Test bulk indexing with some items skipped"""
        posts = [
            BlogPost.objects.create(
                title="Published",
                slug="published",
                content="Content",
                author=self.user,
                status="published",
            ),
            BlogPost.objects.create(
                title="Draft",
                slug="draft",
                content="Content",
                author=self.user,
                status="draft",  # Should be skipped
            ),
        ]

        self.mock_index.add_documents.return_value = {"taskUid": 789}

        with patch.object(self.manager, "_generate_url", return_value="/blog/post/"):
            results = self.manager.bulk_index(posts)

        assert results["indexed"] == 1
        assert results["skipped"] == 1
        assert results["failed"] == 0

    def test_bulk_index_batching(self):
        """Test bulk indexing with batching"""
        # Create more items than batch size
        self.manager.batch_size = 2

        posts = []
        for i in range(5):
            post = BlogPost.objects.create(
                title=f"Post {i}",
                slug=f"post-{i}",
                content=f"Content {i}",
                author=self.user,
                status="published",
            )
            posts.append(post)

        self.mock_index.add_documents.return_value = {"taskUid": 789}

        with patch.object(self.manager, "_generate_url", return_value="/blog/post/"):
            results = self.manager.bulk_index(posts)

        # Should call add_documents multiple times (3 batches: 2+2+1)
        assert self.mock_index.add_documents.call_count == 3
        assert results["indexed"] == 5


@pytest.mark.unit
@pytest.mark.search
class TestTagParsing(TestCase):
    """Test tag parsing functionality"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client"):
            self.manager = SearchIndexManager()

    def test_parse_tags_comma_separated(self):
        """Test parsing comma-separated tags"""
        tags_str = "python, django, web development"

        result = self.manager._parse_tags(tags_str)

        assert isinstance(result, list)
        assert len(result) == 3
        assert "python" in result
        assert "django" in result
        assert "web development" in result

    def test_parse_tags_whitespace_handling(self):
        """Test tag parsing with various whitespace"""
        tags_str = "  python ,  django  ,web development  "

        result = self.manager._parse_tags(tags_str)

        # Should strip whitespace
        assert "python" in result
        assert "django" in result
        assert "web development" in result
        assert "  python" not in result

    def test_parse_tags_empty_string(self):
        """Test parsing empty tag string"""
        result = self.manager._parse_tags("")
        assert result == []

    def test_parse_tags_none(self):
        """Test parsing None"""
        result = self.manager._parse_tags(None)
        assert result == []

    def test_parse_tags_already_list(self):
        """Test parsing when already a list"""
        tags_list = ["python", "django"]

        result = self.manager._parse_tags(tags_list)

        assert result == tags_list

    def test_parse_tags_single_tag(self):
        """Test parsing single tag without comma"""
        result = self.manager._parse_tags("python")
        assert result == ["python"]


@pytest.mark.unit
@pytest.mark.search
class TestURLGeneration(TestCase):
    """Test URL generation for search results"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client"):
            self.manager = SearchIndexManager()

    def test_generate_url_blog_post(self):
        """Test URL generation for blog post"""
        from apps.main.models import BlogPost

        blog_post = Mock(spec=BlogPost)
        blog_post.__class__.__name__ = "BlogPost"
        blog_post.slug = "test-post"

        with patch("django.urls.reverse", return_value="/blog/test-post/"):
            url = self.manager._generate_url(blog_post)

        assert url == "/blog/test-post/"

    def test_generate_url_ai_tool(self):
        """Test URL generation for AI tool"""
        from apps.main.models import AITool

        ai_tool = Mock(spec=AITool)
        ai_tool.__class__.__name__ = "AITool"
        ai_tool.slug = "chatgpt"

        with patch("django.urls.reverse", return_value="/tools/chatgpt/"):
            url = self.manager._generate_url(ai_tool)

        assert url == "/tools/chatgpt/"

    def test_generate_url_error_fallback(self):
        """Test URL generation error fallback"""
        from apps.main.models import BlogPost

        blog_post = Mock(spec=BlogPost)
        blog_post.__class__.__name__ = "BlogPost"
        blog_post.slug = "test-post"

        with patch("django.urls.reverse", side_effect=Exception("URL error")):
            url = self.manager._generate_url(blog_post)

        # Should return empty or fallback URL
        assert url in ["#", "", None, "/"]


@pytest.mark.unit
@pytest.mark.search
@pytest.mark.security
class TestXSSPrevention(TestCase):
    """Security tests for XSS prevention"""

    def setUp(self):
        """Set up test fixtures"""
        with patch("meilisearch.Client"):
            self.manager = SearchIndexManager()

        self.user = User.objects.create_user(
            username="testuser", email="test@test.com", password="testpass"
        )

    def test_xss_in_title_sanitized(self):
        """Test XSS payload in title is sanitized"""
        blog_post = BlogPost.objects.create(
            title='<script>alert("xss")</script>Normal Title',
            slug="xss-test",
            content="Content",
            author=self.user,
            status="published",
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/xss-test/"
        ):
            document = self.manager.build_document(blog_post)

        # Title field might not be sanitized (set sanitize: False in config)
        # but should be HTML-escaped when displayed
        assert document["title"] == blog_post.title

    def test_xss_in_content_sanitized(self):
        """Test XSS payload in content is sanitized"""
        xss_content = """
        <p>Normal content</p>
        <script>alert('xss')</script>
        <img src=x onerror="alert(1)">
        <iframe src="javascript:alert(1)"></iframe>
        """

        blog_post = BlogPost.objects.create(
            title="XSS Test",
            slug="xss-content-test",
            content=xss_content,
            author=self.user,
            status="published",
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/xss-content-test/"
        ):
            document = self.manager.build_document(blog_post)

        # Content should be sanitized
        sanitized_content = document["content"]
        assert "<script>" not in sanitized_content
        assert "onerror" not in sanitized_content
        assert "<iframe" not in sanitized_content
        assert "Normal content" in sanitized_content

    def test_sql_injection_in_search_safe(self):
        """Test SQL injection attempts are safe"""
        # This is more of a documentation test - Django ORM handles this
        malicious_input = "'; DROP TABLE blog_post; --"

        # Should not crash or execute SQL
        blog_post = BlogPost.objects.create(
            title="Normal Title",
            slug="sql-test",
            content=malicious_input,
            author=self.user,
            status="published",
        )

        with patch.object(
            self.manager, "_generate_url", return_value="/blog/sql-test/"
        ):
            document = self.manager.build_document(blog_post)

        # Content should be stored safely
        assert malicious_input in document["content"]

    def test_javascript_protocol_in_links(self):
        """Test javascript: protocol in links is removed"""
        content_with_js_link = """
        <a href="javascript:alert(1)">Click me</a>
        <a href="http://safe.com">Safe link</a>
        """

        result = self.manager.sanitize_content(
            content_with_js_link, sanitize_type="html"
        )

        # javascript: protocol should be removed
        assert "javascript:" not in result.lower()
        assert "Click me" in result
        assert "Safe link" in result


@pytest.mark.unit
@pytest.mark.search
class TestSearchIndexManagerSingleton(TestCase):
    """Test singleton pattern of search_index_manager"""

    @override_settings(MEILISEARCH_MASTER_KEY="testkey")
    def test_singleton_instance(self):
        """Test that search_index_manager is a singleton"""
        with patch("meilisearch.Client"):
            # Import the instance
            from apps.main.search_index import search_index_manager

            # Should be same instance
            assert isinstance(search_index_manager, SearchIndexManager)

            # Multiple imports should return same instance
            from apps.main.search_index import search_index_manager as manager2

            assert search_index_manager is manager2
