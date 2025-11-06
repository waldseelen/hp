"""
Unit tests for Blog Views

Tests the PostListView and PostDetailView including search, pagination,
and related posts functionality.

Coverage target: 85%+
"""

from datetime import timedelta

from django.urls import reverse
from django.utils import timezone

import pytest

from apps.blog.models import Post
from apps.main.models import Admin

# ============================================================================
# Fixtures
# ============================================================================


@pytest.fixture
def author(db):
    """Create a test author (Admin)"""
    return Admin.objects.create(
        username="testauthor",
        email="author@test.com",
        first_name="Test",
        last_name="Author",
    )


@pytest.fixture
def published_posts(author):
    """Create multiple published posts"""
    posts = []
    for i in range(5):
        post = Post.objects.create(
            title=f"Published Post {i + 1}",
            content=f"Content for post {i + 1}. " * 50,
            status="published",
            author=author,
            published_at=timezone.now() - timedelta(days=i),
            tags=["django", "python"],
        )
        posts.append(post)
    return posts


@pytest.fixture
def draft_post(author):
    """Create a draft post"""
    return Post.objects.create(
        title="Draft Post",
        content="Draft content.",
        status="draft",
        author=author,
    )


# ============================================================================
# PostListView Tests
# ============================================================================


@pytest.mark.django_db
class TestPostListView:
    """Test blog post list view"""

    def test_post_list_view_url(self, client, published_posts):
        """Should access post list view"""
        response = client.get(reverse("blog:list"))

        assert response.status_code == 200

    def test_post_list_view_uses_correct_template(self, client, published_posts):
        """Should use correct template"""
        response = client.get(reverse("blog:list"))

        assert "pages/blog/list.html" in [t.name for t in response.templates]

    def test_post_list_view_shows_published_posts(
        self, client, published_posts, draft_post
    ):
        """Should show only published posts"""
        response = client.get(reverse("blog:list"))

        # Check published posts are in context
        posts = response.context["posts"]
        assert len(posts) == 5
        for published_post in published_posts:
            assert published_post in posts

        # Draft post should not be shown
        assert draft_post not in posts

    def test_post_list_view_pagination(self, client, author):
        """Should paginate posts"""
        # Create 15 posts (more than paginate_by=10)
        for i in range(15):
            Post.objects.create(
                title=f"Post {i + 1}",
                content=f"Content {i + 1}",
                status="published",
                author=author,
                published_at=timezone.now() - timedelta(days=i),
            )

        # First page should have 10 posts
        response = client.get(reverse("blog:list"))
        assert len(response.context["posts"]) == 10
        assert response.context["is_paginated"] is True

        # Second page should have 5 posts
        response = client.get(reverse("blog:list") + "?page=2")
        assert len(response.context["posts"]) == 5

    def test_post_list_view_search_by_title(self, client, author):
        """Should filter posts by title search"""
        Post.objects.create(
            title="Django Tutorial",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )
        Post.objects.create(
            title="React Guide",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )

        response = client.get(reverse("blog:list") + "?search=Django")

        posts = response.context["posts"]
        assert len(posts) == 1
        assert posts[0].title == "Django Tutorial"

    def test_post_list_view_search_by_content(self, client, author):
        """Should filter posts by content search"""
        Post.objects.create(
            title="Post 1",
            content="This is about Django framework",
            status="published",
            author=author,
            published_at=timezone.now(),
        )
        Post.objects.create(
            title="Post 2",
            content="This is about React",
            status="published",
            author=author,
            published_at=timezone.now(),
        )

        response = client.get(reverse("blog:list") + "?search=Django")

        posts = response.context["posts"]
        assert len(posts) == 1
        assert "Django" in posts[0].content

    def test_post_list_view_search_by_excerpt(self, client, author):
        """Should filter posts by excerpt search"""
        Post.objects.create(
            title="Post 1",
            excerpt="Learn Django framework",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )
        Post.objects.create(
            title="Post 2",
            excerpt="Learn React",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )

        response = client.get(reverse("blog:list") + "?search=Django")

        posts = response.context["posts"]
        assert len(posts) == 1
        assert "Django" in posts[0].excerpt

    def test_post_list_view_search_case_insensitive(self, client, author):
        """Should perform case-insensitive search"""
        Post.objects.create(
            title="Django Tutorial",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )

        # Search with lowercase
        response = client.get(reverse("blog:list") + "?search=django")

        posts = response.context["posts"]
        assert len(posts) == 1
        assert posts[0].title == "Django Tutorial"

    def test_post_list_view_search_query_in_context(self, client, published_posts):
        """Should include search query in context"""
        response = client.get(reverse("blog:list") + "?search=Django")

        assert response.context["search_query"] == "Django"

    def test_post_list_view_no_search_query(self, client, published_posts):
        """Should show all posts when no search query"""
        response = client.get(reverse("blog:list"))

        assert response.context["search_query"] == ""
        assert len(response.context["posts"]) == 5

    def test_post_list_view_empty_search_results(self, client, published_posts):
        """Should show no results for non-matching search"""
        response = client.get(reverse("blog:list") + "?search=NonExistentTerm")

        posts = response.context["posts"]
        assert len(posts) == 0


# ============================================================================
# PostDetailView Tests
# ============================================================================


@pytest.mark.django_db
class TestPostDetailView:
    """Test blog post detail view"""

    def test_post_detail_view_url(self, client, published_posts):
        """Should access post detail view"""
        post = published_posts[0]
        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        assert response.status_code == 200

    def test_post_detail_view_uses_correct_template(self, client, published_posts):
        """Should use correct template"""
        post = published_posts[0]
        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        assert "pages/blog/detail.html" in [t.name for t in response.templates]

    def test_post_detail_view_shows_correct_post(self, client, published_posts):
        """Should show correct post"""
        post = published_posts[0]
        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        assert response.context["post"] == post
        assert post.title in response.content.decode()

    def test_post_detail_view_draft_post_404(self, client, draft_post):
        """Should return 404 for draft posts"""
        response = client.get(reverse("blog:detail", kwargs={"slug": draft_post.slug}))

        assert response.status_code == 404

    def test_post_detail_view_future_post_404(self, client, author):
        """Should return 404 for future scheduled posts"""
        future_post = Post.objects.create(
            title="Future Post",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now() + timedelta(days=1),
        )

        response = client.get(reverse("blog:detail", kwargs={"slug": future_post.slug}))

        assert response.status_code == 404

    def test_post_detail_view_shows_related_posts(self, client, author):
        """Should show related posts in context"""
        main_post = Post.objects.create(
            title="Main Post",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
            tags=["django", "python"],
        )

        # Create related posts
        for i in range(5):
            Post.objects.create(
                title=f"Related {i}",
                content="Content",
                status="published",
                author=author,
                published_at=timezone.now(),
                tags=["django"],
            )

        response = client.get(reverse("blog:detail", kwargs={"slug": main_post.slug}))

        # Should have related_posts in context
        assert "related_posts" in response.context
        related_posts = response.context["related_posts"]

        # Should limit to 3 posts
        assert len(related_posts) <= 3

        # Should not include main post
        assert main_post not in related_posts

    def test_post_detail_view_no_related_posts(self, client, author):
        """Should handle case with no related posts"""
        post = Post.objects.create(
            title="Single Post",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
            tags=["unique-tag"],
        )

        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        related_posts = response.context["related_posts"]
        assert len(related_posts) == 0

    def test_post_detail_view_invalid_slug_404(self, client):
        """Should return 404 for invalid slug"""
        response = client.get(
            reverse("blog:detail", kwargs={"slug": "non-existent-slug"})
        )

        assert response.status_code == 404

    def test_post_detail_view_context_object_name(self, client, published_posts):
        """Should use correct context object name"""
        post = published_posts[0]
        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        # Context should use 'post' as object name
        assert "post" in response.context
        assert response.context["post"] == post


# ============================================================================
# Integration Tests
# ============================================================================


@pytest.mark.django_db
class TestBlogViewsIntegration:
    """Test blog views integration"""

    def test_list_to_detail_navigation(self, client, published_posts):
        """Should navigate from list to detail view"""
        # Get list view
        list_response = client.get(reverse("blog:list"))
        assert list_response.status_code == 200

        # Get first post
        post = published_posts[0]

        # Navigate to detail
        detail_response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))
        assert detail_response.status_code == 200
        assert detail_response.context["post"] == post

    def test_search_and_view_result(self, client, author):
        """Should search and view result"""
        post = Post.objects.create(
            title="Unique Django Post",
            content="Content",
            status="published",
            author=author,
            published_at=timezone.now(),
        )

        # Search
        search_response = client.get(reverse("blog:list") + "?search=Unique")
        assert search_response.status_code == 200
        assert len(search_response.context["posts"]) == 1

        # View detail
        detail_response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))
        assert detail_response.status_code == 200
        assert detail_response.context["post"] == post
