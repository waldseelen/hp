"""
Performance verification tests.
Checks page load times and ensures they meet the <3s requirement.
"""

import time

from django.test import Client
from django.urls import reverse
from django.utils import timezone

import pytest

from apps.blog.models import Post
from apps.main.models import Admin

pytestmark = pytest.mark.django_db


class TestPagePerformance:
    """Test page load performance"""

    @pytest.fixture
    def setup_test_data(self):
        """Setup test data for performance tests"""
        admin = Admin.objects.create(username="perfadmin", email="perf@test.com")

        # Create multiple blog posts for realistic testing
        posts = []
        for i in range(10):
            post = Post.objects.create(
                title=f"Performance Test Post {i + 1}",
                content=f"Content for performance test post {i + 1}. " * 50,
                excerpt=f"Excerpt {i + 1}",
                status="published",
                published_at=timezone.now(),
                author=admin,
                tags=["performance", "test"],
            )
            posts.append(post)

        return posts

    def test_homepage_load_time(self, client: Client):
        """Homepage should load in less than 3 seconds"""
        start_time = time.time()

        response = client.get("/")

        end_time = time.time()
        load_time = end_time - start_time

        assert response.status_code == 200
        assert load_time < 3.0, f"Homepage loaded in {load_time:.2f}s (>3s)"
        print(f"[PASS] Homepage load time: {load_time:.3f}s")

    def test_blog_list_load_time(self, client: Client, setup_test_data):
        """Blog list page should load in less than 3 seconds"""
        start_time = time.time()

        response = client.get(reverse("blog:list"))

        end_time = time.time()
        load_time = end_time - start_time

        assert response.status_code == 200
        assert load_time < 3.0, f"Blog list loaded in {load_time:.2f}s (>3s)"
        print(f"[PASS] Blog list load time: {load_time:.3f}s")

    def test_blog_detail_load_time(self, client: Client, setup_test_data):
        """Blog detail page should load in less than 3 seconds"""
        post = setup_test_data[0]

        start_time = time.time()

        response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))

        end_time = time.time()
        load_time = end_time - start_time

        assert response.status_code == 200
        assert load_time < 3.0, f"Blog detail loaded in {load_time:.2f}s (>3s)"
        print(f"[PASS] Blog detail load time: {load_time:.3f}s")

    def test_contact_page_load_time(self, client: Client):
        """Contact page should load in less than 3 seconds"""
        start_time = time.time()

        response = client.get(reverse("contact:form"))

        end_time = time.time()
        load_time = end_time - start_time

        assert response.status_code == 200
        assert load_time < 3.0, f"Contact page loaded in {load_time:.2f}s (>3s)"
        print(f"[PASS] Contact page load time: {load_time:.3f}s")

    def test_blog_search_performance(self, client: Client, setup_test_data):
        """Blog search should be performant"""
        start_time = time.time()

        response = client.get(reverse("blog:list") + "?search=performance")

        end_time = time.time()
        load_time = end_time - start_time

        assert response.status_code == 200
        assert load_time < 3.0, f"Blog search took {load_time:.2f}s (>3s)"
        print(f"[PASS] Blog search time: {load_time:.3f}s")

    def test_multiple_consecutive_requests(self, client: Client, setup_test_data):
        """Multiple consecutive requests should maintain performance"""
        post = setup_test_data[0]
        times = []

        for i in range(5):
            start_time = time.time()
            response = client.get(reverse("blog:detail", kwargs={"slug": post.slug}))
            end_time = time.time()

            load_time = end_time - start_time
            times.append(load_time)

            assert response.status_code == 200
            assert load_time < 3.0

        avg_time = sum(times) / len(times)
        print(f"[PASS] Average load time over 5 requests: {avg_time:.3f}s")
        print(f"  Min: {min(times):.3f}s, Max: {max(times):.3f}s")


class TestDatabaseQueryPerformance:
    """Test database query performance"""

    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing"""
        admin = Admin.objects.create(username="dbperf", email="dbperf@test.com")

        posts = []
        for i in range(50):
            post = Post.objects.create(
                title=f"Post {i + 1}",
                content=f"Content {i + 1}",
                status="published",
                published_at=timezone.now(),
                author=admin,
                tags=[f"tag{i % 5}", "common"],
            )
            posts.append(post)

        return posts

    def test_blog_list_query_count(
        self, client: Client, django_assert_num_queries, large_dataset
    ):
        """Blog list should use efficient queries"""
        # Optimized queries: 1) Count query, 2) Posts with select_related(author), 3) Social links
        with django_assert_num_queries(3):  # Actual optimized query count
            response = client.get(reverse("blog:list"))
            assert response.status_code == 200

    def test_related_posts_query_efficiency(self, large_dataset):
        """Related posts should be fetched efficiently"""
        post = large_dataset[0]

        start_time = time.time()
        related = post.get_related_posts(limit=3)
        end_time = time.time()

        query_time = end_time - start_time
        assert query_time < 0.5, f"Related posts query took {query_time:.3f}s"
        print(f"[PASS] Related posts query time: {query_time:.3f}s")


class TestResponseTimes:
    """Test various response time metrics"""

    def test_static_page_response_time(self, client: Client):
        """Static-like pages should respond very quickly"""
        start_time = time.time()
        response = client.get("/")
        end_time = time.time()

        response_time = end_time - start_time

        # Static pages should be very fast
        assert response_time < 1.0, f"Response time: {response_time:.3f}s"
        print(f"[PASS] Homepage response time: {response_time:.3f}s")

    def test_api_endpoint_response_time(self, client: Client):
        """API endpoints should have fast response times"""
        # Test a simple API endpoint if available
        # This is a placeholder - adjust based on actual API endpoints
        pass


class TestPerformanceSummary:
    """Generate performance summary report"""

    def test_performance_summary(self, client: Client):
        """Generate a summary of all performance metrics"""
        metrics = {}

        # Homepage
        start = time.time()
        client.get("/")
        metrics["homepage"] = time.time() - start

        # Blog list
        start = time.time()
        client.get(reverse("blog:list"))
        metrics["blog_list"] = time.time() - start

        # Contact
        start = time.time()
        client.get(reverse("contact:form"))
        metrics["contact"] = time.time() - start

        # Check all pages meet requirement
        failures = {k: v for k, v in metrics.items() if v >= 3.0}

        print("\n" + "=" * 60)
        print("PERFORMANCE SUMMARY")
        print("=" * 60)
        for page, time_val in metrics.items():
            status = "[PASS]" if time_val < 3.0 else "[FAIL]"
            print(f"{page:20s}: {time_val:.3f}s {status}")
        print("=" * 60)

        assert len(failures) == 0, f"Pages exceeding 3s: {failures}"
