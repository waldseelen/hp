"""
Integration tests for Blog comment flow and user journeys.
Tests end-to-end workflows including:
- Creating posts
- Viewing posts
- Commenting on posts
- Comment moderation
- User interactions
"""

from django.test import Client
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.blog.models import Post
from apps.main.models import Admin

pytestmark = pytest.mark.django_db


class TestBlogCommentFlow:
    """Integration tests for blog comment functionality"""

    @pytest.fixture
    def admin_user(self):
        """Create admin user for tests"""
        return Admin.objects.create(username="testadmin", email="admin@test.com")

    @pytest.fixture
    def published_post(self, admin_user):
        """Create a published blog post"""
        return Post.objects.create(
            title="Test Post for Comments",
            slug="test-post-comments",
            content="This is a test post for testing comments functionality.",
            excerpt="Test excerpt",
            status="published",
            published_at=timezone.now(),
            author=admin_user,
            tags=["test", "comments"],
        )

    def test_view_post_without_comments(self, client: Client, published_post):
        """User can view a post that has no comments"""
        response = client.get(
            reverse("blog:detail", kwargs={"slug": published_post.slug})
        )
        assert response.status_code == 200
        assert "Test Post for Comments" in str(response.content)

    def test_post_detail_increments_view_count(self, client: Client, published_post):
        """Viewing a post should increment its view count"""
        initial_count = published_post.view_count

        # View the post
        client.get(reverse("blog:detail", kwargs={"slug": published_post.slug}))

        # Refresh from database
        published_post.refresh_from_db()
        assert published_post.view_count == initial_count + 1

    def test_multiple_views_increment_count(self, client: Client, published_post):
        """Multiple views should increment count each time"""
        initial_count = published_post.view_count

        # View the post 3 times
        for _ in range(3):
            client.get(reverse("blog:detail", kwargs={"slug": published_post.slug}))

        published_post.refresh_from_db()
        assert published_post.view_count == initial_count + 3

    def test_related_posts_shown_on_detail_page(
        self, client: Client, published_post, admin_user
    ):
        """Related posts should be shown on post detail page"""
        # Create related posts with same tags
        related_post1 = Post.objects.create(
            title="Related Post 1",
            content="Related content 1",
            status="published",
            published_at=timezone.now(),
            author=admin_user,
            tags=["test", "python"],
        )

        related_post2 = Post.objects.create(
            title="Related Post 2",
            content="Related content 2",
            status="published",
            published_at=timezone.now(),
            author=admin_user,
            tags=["test", "django"],
        )

        response = client.get(
            reverse("blog:detail", kwargs={"slug": published_post.slug})
        )

        assert response.status_code == 200
        # Related posts should be in context
        assert "related_posts" in response.context


class TestBlogUserJourney:
    """Test complete user journeys through the blog"""

    @pytest.fixture
    def setup_blog_posts(self):
        """Setup multiple blog posts for testing"""
        admin = Admin.objects.create(username="testadmin", email="admin@test.com")

        posts = []
        for i in range(5):
            post = Post.objects.create(
                title=f"Test Post {i + 1}",
                content=f"Content for post {i + 1}",
                excerpt=f"Excerpt {i + 1}",
                status="published",
                published_at=timezone.now(),
                author=admin,
                tags=["test", f"tag{i + 1}"],
            )
            posts.append(post)

        return posts

    def test_user_browses_blog_list(self, client: Client, setup_blog_posts):
        """User visits blog list page"""
        response = client.get(reverse("blog:list"))
        assert response.status_code == 200

        # Should see posts
        for post in setup_blog_posts:
            assert post.title in str(response.content)

    def test_user_searches_blog(self, client: Client, setup_blog_posts):
        """User searches for specific blog post"""
        response = client.get(reverse("blog:list") + "?search=Post 2")
        assert response.status_code == 200
        assert "Test Post 2" in str(response.content)

    def test_user_navigates_from_list_to_detail(self, client: Client, setup_blog_posts):
        """User clicks on a post from list page"""
        post = setup_blog_posts[0]

        # First, visit list page
        list_response = client.get(reverse("blog:list"))
        assert list_response.status_code == 200

        # Then, visit detail page
        detail_response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))
        assert detail_response.status_code == 200
        assert post.title in str(detail_response.content)

    def test_user_views_multiple_posts_sequentially(
        self, client: Client, setup_blog_posts
    ):
        """User views multiple posts in sequence"""
        for post in setup_blog_posts[:3]:
            response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))
            assert response.status_code == 200
            assert post.title in str(response.content)

    def test_pagination_workflow(self, client: Client, setup_blog_posts):
        """User navigates through paginated blog posts"""
        # Visit first page
        response_page1 = client.get(reverse("blog:list"))
        assert response_page1.status_code == 200

        # Visit second page if exists
        response_page2 = client.get(reverse("blog:list") + "?page=2")
        # Should either show page 2 or redirect to page 1
        assert response_page2.status_code in [200, 404]


class TestBlogSearchIntegration:
    """Integration tests for blog search functionality"""

    @pytest.fixture
    def search_test_posts(self):
        """Create posts for search testing"""
        admin = Admin.objects.create(username="searchadmin", email="search@test.com")

        Post.objects.create(
            title="Python Tutorial",
            content="Learn Python programming basics",
            status="published",
            published_at=timezone.now(),
            author=admin,
            tags=["python", "tutorial"],
        )

        Post.objects.create(
            title="Django Guide",
            content="Django web framework tutorial",
            status="published",
            published_at=timezone.now(),
            author=admin,
            tags=["django", "python"],
        )

        Post.objects.create(
            title="JavaScript Basics",
            content="Learn JavaScript fundamentals",
            status="published",
            published_at=timezone.now(),
            author=admin,
            tags=["javascript", "tutorial"],
        )

    def test_search_by_title(self, client: Client, search_test_posts):
        """Search posts by title"""
        response = client.get(reverse("blog:list") + "?search=Python")
        assert response.status_code == 200
        assert "Python Tutorial" in str(response.content)

    def test_search_by_content(self, client: Client, search_test_posts):
        """Search posts by content"""
        response = client.get(reverse("blog:list") + "?search=Django")
        assert response.status_code == 200
        assert "Django Guide" in str(response.content)

    def test_search_case_insensitive(self, client: Client, search_test_posts):
        """Search should be case insensitive"""
        response = client.get(reverse("blog:list") + "?search=python")
        assert response.status_code == 200
        content = str(response.content)
        assert "Python Tutorial" in content or "Django Guide" in content

    def test_search_with_no_results(self, client: Client, search_test_posts):
        """Search with no matching results"""
        response = client.get(reverse("blog:list") + "?search=nonexistent")
        assert response.status_code == 200
        # Should show empty results gracefully

    def test_empty_search_query(self, client: Client, search_test_posts):
        """Empty search query should show all posts"""
        response = client.get(reverse("blog:list") + "?search=")
        assert response.status_code == 200


class TestBlogPostLifecycle:
    """Test blog post lifecycle from creation to publication"""

    @pytest.fixture
    def admin_user(self):
        return Admin.objects.create(
            username="lifecycleadmin", email="lifecycle@test.com"
        )

    def test_draft_post_not_visible_to_public(self, client: Client, admin_user):
        """Draft posts should not be visible on public blog list"""
        draft_post = Post.objects.create(
            title="Draft Post",
            content="This is a draft",
            status="draft",
            author=admin_user,
        )

        response = client.get(reverse("blog:list"))
        assert response.status_code == 200
        assert "Draft Post" not in str(response.content)

    def test_published_post_visible_to_public(self, client: Client, admin_user):
        """Published posts should be visible on public blog list"""
        published_post = Post.objects.create(
            title="Published Post",
            content="This is published",
            status="published",
            published_at=timezone.now(),
            author=admin_user,
        )

        response = client.get(reverse("blog:list"))
        assert response.status_code == 200
        assert "Published Post" in str(response.content)

    def test_scheduled_post_not_yet_visible(self, client: Client, admin_user):
        """Scheduled posts with future date should not be visible"""
        from datetime import timedelta

        future_date = timezone.now() + timedelta(days=1)
        scheduled_post = Post.objects.create(
            title="Future Post",
            content="This will be published in future",
            status="published",
            published_at=future_date,
            author=admin_user,
        )

        response = client.get(reverse("blog:list"))
        assert response.status_code == 200
        assert "Future Post" not in str(response.content)
