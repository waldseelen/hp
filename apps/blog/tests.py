"""
Comprehensive test suite for blog app.
Tests for models, views, and user journeys.
"""

from datetime import timedelta

from django.test import Client, TestCase
from django.urls import reverse
from django.utils import timezone

from apps.blog.models import Post
from apps.main.models import Admin


class PostModelTests(TestCase):
    """Test Post model functionality."""

    def setUp(self):
        """Create test author and posts."""
        self.author = Admin.objects.create(
            username="testauthor", email="author@test.com", name="Test Author"
        )

    def test_post_creation(self):
        """Test basic post creation."""
        post = Post.objects.create(
            title="Test Post",
            content="Test content here",
            excerpt="Test excerpt",
            author=self.author,
            status="published",
            published_at=timezone.now(),
        )
        self.assertEqual(post.title, "Test Post")
        self.assertEqual(post.author, self.author)
        self.assertEqual(post.status, "published")

    def test_post_slug_generation(self):
        """Test that slug is auto-generated from title."""
        post = Post.objects.create(
            title="Test Post Title", content="Content", author=self.author
        )
        self.assertIsNotNone(post.slug)
        self.assertIn("test-post", post.slug.lower())

    def test_published_manager(self):
        """Test that published() manager filters correctly."""
        # Published post
        published = Post.objects.create(
            title="Published Post",
            content="Content",
            author=self.author,
            status="published",
            published_at=timezone.now() - timedelta(hours=1),
        )

        # Draft post
        draft = Post.objects.create(
            title="Draft Post", content="Content", author=self.author, status="draft"
        )

        # Future published post
        future = Post.objects.create(
            title="Future Post",
            content="Content",
            author=self.author,
            status="published",
            published_at=timezone.now() + timedelta(hours=1),
        )

        published_posts = Post.objects.published()
        self.assertIn(published, published_posts)
        self.assertNotIn(draft, published_posts)
        self.assertNotIn(future, published_posts)

    def test_get_absolute_url(self):
        """Test post URL generation."""
        post = Post.objects.create(
            title="Test Post",
            slug="test-post",
            content="Content",
            author=self.author,
            status="published",
            published_at=timezone.now(),
        )
        url = post.get_absolute_url()
        self.assertIn("/blog/", url)
        self.assertIn("test-post", url)


class PostListViewTests(TestCase):
    """Test PostListView functionality."""

    def setUp(self):
        """Create test client, author, and posts."""
        self.client = Client()
        self.author = Admin.objects.create(
            username="testauthor", email="author@test.com", name="Test Author"
        )

        # Create multiple published posts
        for i in range(15):
            Post.objects.create(
                title=f"Test Post {i}",
                content=f"Content for post {i}",
                excerpt=f"Excerpt {i}",
                author=self.author,
                status="published",
                published_at=timezone.now() - timedelta(hours=i),
            )

    def test_blog_list_view_status_code(self):
        """Test that blog list page loads successfully."""
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(response.status_code, 200)

    def test_blog_list_view_template(self):
        """Test correct template is used."""
        response = self.client.get(reverse("blog:list"))
        self.assertTemplateUsed(response, "pages/blog/list.html")

    def test_blog_list_pagination(self):
        """Test that pagination works correctly."""
        response = self.client.get(reverse("blog:list"))
        self.assertEqual(response.status_code, 200)

        # Should have 10 posts on first page (paginate_by = 10)
        self.assertEqual(len(response.context["posts"]), 10)

        # Check pagination context
        self.assertTrue(response.context["is_paginated"])
        self.assertEqual(response.context["total_posts"], 15)
        self.assertEqual(response.context["total_pages"], 2)

    def test_blog_list_second_page(self):
        """Test second page of pagination."""
        response = self.client.get(reverse("blog:list") + "?page=2")
        self.assertEqual(response.status_code, 200)

        # Should have 5 posts on second page (15 total, 10 on first page)
        self.assertEqual(len(response.context["posts"]), 5)

    def test_blog_list_search(self):
        """Test search functionality."""
        # Create a post with distinctive content
        Post.objects.create(
            title="Unique Python Post",
            content="This post is about Python programming",
            excerpt="Python excerpt",
            author=self.author,
            status="published",
            published_at=timezone.now(),
        )

        response = self.client.get(reverse("blog:list") + "?search=Python")
        self.assertEqual(response.status_code, 200)

        # Should find the unique post
        posts = response.context["posts"]
        self.assertTrue(any("Python" in post.title for post in posts))

    def test_blog_list_only_published(self):
        """Test that only published posts are shown."""
        # Create a draft post
        Post.objects.create(
            title="Draft Post",
            content="Draft content",
            author=self.author,
            status="draft",
        )

        response = self.client.get(reverse("blog:list"))
        posts = list(response.context["posts"])

        # Draft should not appear
        self.assertFalse(any(post.status == "draft" for post in posts))


class PostDetailViewTests(TestCase):
    """Test PostDetailView functionality."""

    def setUp(self):
        """Create test client, author, and post."""
        self.client = Client()
        self.author = Admin.objects.create(
            username="testauthor", email="author@test.com", name="Test Author"
        )

        self.post = Post.objects.create(
            title="Test Detail Post",
            slug="test-detail-post",
            content="Detailed content here",
            excerpt="Test excerpt",
            author=self.author,
            status="published",
            published_at=timezone.now(),
        )

    def test_post_detail_view_status_code(self):
        """Test that post detail page loads successfully."""
        response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(response.status_code, 200)

    def test_post_detail_view_template(self):
        """Test correct template is used."""
        response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )
        self.assertTemplateUsed(response, "pages/blog/detail.html")

    def test_post_detail_view_context(self):
        """Test that correct post is in context."""
        response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(response.context["post"], self.post)

    def test_post_detail_404_for_draft(self):
        """Test that draft posts return 404."""
        draft = Post.objects.create(
            title="Draft Post",
            slug="draft-post",
            content="Draft content",
            author=self.author,
            status="draft",
        )

        response = self.client.get(reverse("blog:detail", kwargs={"slug": draft.slug}))
        self.assertEqual(response.status_code, 404)

    def test_post_detail_404_for_nonexistent(self):
        """Test that non-existent slug returns 404."""
        response = self.client.get(
            reverse("blog:detail", kwargs={"slug": "nonexistent-post"})
        )
        self.assertEqual(response.status_code, 404)

    def test_post_detail_view_count_increment(self):
        """Test that view count increments on visit."""
        # Refresh post from database first to get current count
        self.post.refresh_from_db()
        initial_views = self.post.view_count

        # Visit the post
        self.client.get(reverse("blog:detail", kwargs={"slug": self.post.slug}))

        # Refresh from database and check increment
        self.post.refresh_from_db()
        self.assertEqual(self.post.view_count, initial_views + 1)

    def test_related_posts_in_context(self):
        """Test that related posts are provided."""
        # Create additional posts
        for i in range(3):
            Post.objects.create(
                title=f"Related Post {i}",
                content=f"Content {i}",
                author=self.author,
                status="published",
                published_at=timezone.now(),
            )

        response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )

        # Should have related_posts in context
        self.assertIn("related_posts", response.context)


class BlogIntegrationTests(TestCase):
    """Integration tests for blog user journeys."""

    def setUp(self):
        """Create test environment."""
        self.client = Client()
        self.author = Admin.objects.create(
            username="testauthor", email="author@test.com", name="Test Author"
        )

        self.post = Post.objects.create(
            title="Integration Test Post",
            slug="integration-test-post",
            content="Full integration test content",
            excerpt="Integration excerpt",
            author=self.author,
            status="published",
            published_at=timezone.now(),
        )

    def test_user_journey_list_to_detail(self):
        """Test complete journey from list to detail page."""
        # User visits blog list
        list_response = self.client.get(reverse("blog:list"))
        self.assertEqual(list_response.status_code, 200)

        # User clicks on a post
        detail_response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(detail_response.status_code, 200)

        # Verify post content is displayed
        self.assertContains(detail_response, self.post.title)
        self.assertContains(detail_response, self.post.content)

    def test_search_and_view_post(self):
        """Test searching and viewing a post."""
        # User searches for specific content
        search_response = self.client.get(reverse("blog:list") + "?search=Integration")
        self.assertEqual(search_response.status_code, 200)

        # Result should contain the post
        self.assertContains(search_response, self.post.title)

        # User clicks on search result
        detail_response = self.client.get(
            reverse("blog:detail", kwargs={"slug": self.post.slug})
        )
        self.assertEqual(detail_response.status_code, 200)
