"""
Pytest fixtures for search tests

Provides common fixtures for:
- Mock MeiliSearch client
- Test data (BlogPost, AITool, etc.)
- Mock search results
- Admin users
- Search index manager mocks
"""

from unittest.mock import MagicMock, Mock, patch

from django.contrib.auth import get_user_model
from django.test import Client

import pytest

from apps.main.models import AITool, BlogPost, CybersecurityResource, UsefulResource
from apps.main.search_index import SearchIndexManager

User = get_user_model()


# ============================================================================
# User Fixtures
# ============================================================================


@pytest.fixture
def regular_user(db):
    """Create a regular test user"""
    return User.objects.create_user(
        username="testuser", email="test@example.com", password="testpass123"
    )


@pytest.fixture
def admin_user(db):
    """Create an admin/superuser"""
    return User.objects.create_superuser(
        username="admin", email="admin@example.com", password="adminpass123"
    )


@pytest.fixture
def authenticated_client(regular_user):
    """Django test client with authenticated user"""
    client = Client()
    client.force_login(regular_user)
    return client


@pytest.fixture
def admin_client(admin_user):
    """Django test client with admin user"""
    client = Client()
    client.force_login(admin_user)
    return client


# ============================================================================
# Model Fixtures
# ============================================================================


@pytest.fixture
def blog_post(db, regular_user):
    """Create a published blog post"""
    return BlogPost.objects.create(
        title="Test Blog Post",
        slug="test-blog-post",
        content="<p>This is test content with <strong>HTML</strong></p>",
        excerpt="Test excerpt",
        meta_description="Meta description",
        tags="python, django, testing",
        author=regular_user,
        status="published",
        is_featured=True,
        view_count=100,
        reading_time=5,
    )


@pytest.fixture
def draft_blog_post(db, regular_user):
    """Create a draft blog post"""
    return BlogPost.objects.create(
        title="Draft Post",
        slug="draft-post",
        content="Draft content",
        author=regular_user,
        status="draft",
        is_featured=False,
    )


@pytest.fixture
def multiple_blog_posts(db, regular_user):
    """Create multiple blog posts for testing"""
    posts = []
    for i in range(5):
        post = BlogPost.objects.create(
            title=f"Post {i}",
            slug=f"post-{i}",
            content=f"Content for post {i}",
            excerpt=f"Excerpt {i}",
            tags=f"tag{i}, python",
            author=regular_user,
            status="published",
            is_featured=(i % 2 == 0),
            view_count=i * 10,
        )
        posts.append(post)
    return posts


@pytest.fixture
def ai_tool(db):
    """Create an AI tool"""
    return AITool.objects.create(
        name="Test AI Tool",
        slug="test-ai-tool",
        description="AI tool description",
        category="chatbot",
        is_visible=True,
        is_featured=True,
        is_free=True,
        rating=4.5,
        order=1,
    )


@pytest.fixture
def multiple_ai_tools(db):
    """Create multiple AI tools"""
    tools = []
    categories = ["chatbot", "image", "code"]
    for i in range(3):
        tool = AITool.objects.create(
            name=f"AI Tool {i}",
            slug=f"ai-tool-{i}",
            description=f"Description {i}",
            category=categories[i],
            is_visible=True,
            is_featured=(i == 0),
            rating=4.0 + i * 0.5,
            order=i,
        )
        tools.append(tool)
    return tools


@pytest.fixture
def useful_resource(db):
    """Create a useful resource"""
    return UsefulResource.objects.create(
        title="Test Resource",
        slug="test-resource",
        description="Resource description",
        url="https://example.com",
        category="tutorial",
        is_visible=True,
    )


# ============================================================================
# MeiliSearch Mock Fixtures
# ============================================================================


@pytest.fixture
def mock_meilisearch_client():
    """Mock MeiliSearch client"""
    with patch("meilisearch.Client") as mock_client:
        mock_index = MagicMock()
        mock_client.return_value.index.return_value = mock_index

        # Default mock responses
        mock_index.add_documents.return_value = {"taskUid": 123}
        mock_index.delete_document.return_value = {"taskUid": 456}
        mock_index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
            "query": "",
        }
        mock_index.get_stats.return_value = {
            "numberOfDocuments": 0,
            "isIndexing": False,
        }

        yield mock_client


@pytest.fixture
def mock_search_index_manager(mock_meilisearch_client):
    """Mock SearchIndexManager instance"""
    with patch("apps.main.search_index.search_index_manager") as mock_manager:
        # Configure mock manager
        mock_manager.index_document.return_value = True
        mock_manager.delete_document.return_value = True
        mock_manager.bulk_index.return_value = {"indexed": 0, "skipped": 0, "failed": 0}
        mock_manager.reindex_all.return_value = {
            "total_indexed": 0,
            "total_skipped": 0,
            "total_failed": 0,
        }
        mock_manager.reindex_model.return_value = {
            "indexed": 0,
            "skipped": 0,
            "failed": 0,
        }

        # Mock index
        mock_manager.index = MagicMock()
        mock_manager.index.search.return_value = {
            "hits": [],
            "estimatedTotalHits": 0,
            "processingTimeMs": 5,
            "query": "",
        }

        yield mock_manager


@pytest.fixture
def mock_search_results():
    """Mock search API results"""
    return {
        "hits": [
            {
                "id": "BlogPost-1",
                "model": "BlogPost",
                "title": "Django Tutorial",
                "content": "Learn Django web framework",
                "excerpt": "Django tutorial excerpt",
                "url": "/blog/django-tutorial/",
                "tags": ["python", "django", "web"],
                "is_featured": True,
                "published_at": "2024-01-01T00:00:00Z",
                "view_count": 100,
                "reading_time": 5,
            },
            {
                "id": "AITool-1",
                "model": "AITool",
                "name": "ChatGPT",
                "description": "AI chatbot",
                "url": "/tools/chatgpt/",
                "category": "chatbot",
                "rating": 4.5,
                "is_free": True,
            },
        ],
        "estimatedTotalHits": 2,
        "query": "test",
        "processingTimeMs": 15,
        "facetDistribution": {
            "model": {"BlogPost": 1, "AITool": 1},
            "category": {"tutorial": 1, "chatbot": 1},
        },
    }


# ============================================================================
# Search Index Manager Fixtures
# ============================================================================


@pytest.fixture
def real_search_index_manager(mock_meilisearch_client):
    """Real SearchIndexManager instance with mocked client"""
    with patch("apps.main.search_index.meilisearch.Client", mock_meilisearch_client):
        manager = SearchIndexManager()
        yield manager


# ============================================================================
# Request/Response Fixtures
# ============================================================================


@pytest.fixture
def mock_request(regular_user):
    """Mock Django request object"""
    request = Mock()
    request.user = regular_user
    request.method = "GET"
    request.GET = {}
    request.POST = {}
    return request


@pytest.fixture
def mock_admin_request(admin_user):
    """Mock Django admin request"""
    request = Mock()
    request.user = admin_user
    request.method = "POST"
    request.GET = {}
    request.POST = {}
    return request


# ============================================================================
# Content Fixtures
# ============================================================================


@pytest.fixture
def xss_payloads():
    """Common XSS payloads for testing sanitization"""
    return [
        '<script>alert("xss")</script>',
        '<img src=x onerror="alert(1)">',
        "<svg/onload=alert(1)>",
        "javascript:alert(1)",
        '<iframe src="javascript:alert(1)"></iframe>',
        "<body onload=alert(1)>",
        "<input onfocus=alert(1) autofocus>",
        '<a href="javascript:alert(1)">Click</a>',
        '<object data="javascript:alert(1)">',
        '<embed src="javascript:alert(1)">',
    ]


@pytest.fixture
def safe_html_content():
    """Safe HTML content for testing"""
    return """
    <h1>Heading</h1>
    <p>This is a <strong>safe</strong> paragraph with <em>emphasis</em>.</p>
    <ul>
        <li>Item 1</li>
        <li>Item 2</li>
    </ul>
    <a href="https://example.com">Safe link</a>
    """


@pytest.fixture
def markdown_content():
    """Markdown content for testing"""
    return """
# Heading 1

This is a paragraph with **bold** and *italic* text.

## Heading 2

- List item 1
- List item 2
- List item 3

[Link](https://example.com)

```python
def hello():
    print("Hello, World!")
```
    """


# ============================================================================
# Cache Fixtures
# ============================================================================


@pytest.fixture(autouse=True)
def clear_cache():
    """Automatically clear cache between tests"""
    from django.core.cache import cache

    cache.clear()
    yield
    cache.clear()


# ============================================================================
# Settings Fixtures
# ============================================================================


@pytest.fixture
def search_settings(settings):
    """Configure search-related settings for tests"""
    settings.MEILISEARCH_HOST = "http://localhost:7700"
    settings.MEILISEARCH_MASTER_KEY = "testkey123"
    settings.MEILISEARCH_INDEX_NAME = "test_index"
    settings.MEILISEARCH_TIMEOUT = 5
    settings.MEILISEARCH_BATCH_SIZE = 100
    return settings


# ============================================================================
# Pytest Configuration
# ============================================================================


def pytest_configure(config):
    """Configure pytest markers"""
    config.addinivalue_line("markers", "unit: Unit tests for search functionality")
    config.addinivalue_line("markers", "integration: Integration tests for search")
    config.addinivalue_line("markers", "search: All search-related tests")
    config.addinivalue_line("markers", "api: API endpoint tests")
    config.addinivalue_line("markers", "admin: Admin interface tests")
    config.addinivalue_line("markers", "performance: Performance tests")
    config.addinivalue_line("markers", "security: Security tests (XSS, sanitization)")
