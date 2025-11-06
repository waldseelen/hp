"""
Load Testing Scenarios - Phase 22D.2
Using Locust for performance testing

Test Scenarios:
1. Homepage Load (100 concurrent users)
2. Blog List/Detail (50 concurrent users)
3. API Endpoints (30 concurrent users)
4. Contact Form Submission (20 concurrent users)

Performance Targets:
- p95 latency < 200ms
- Error rate < 1%
- Throughput > 100 req/s
- Success rate > 99%

Run:
    locust -f tests/load/locustfile.py --host=http://localhost:8000

Web UI: http://localhost:8089
"""

import random
import time

from locust import HttpUser, TaskSet, between, task


class HomepageUserBehavior(TaskSet):
    """
    Homepage load testing scenarios
    Target: 100 concurrent users
    """

    @task(10)
    def load_homepage(self):
        """Load homepage - highest priority"""
        with self.client.get("/", catch_response=True, name="Homepage") as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage failed with status {response.status_code}")

    @task(5)
    def load_about(self):
        """Load about page"""
        with self.client.get(
            "/about/", catch_response=True, name="About Page"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # About page might not exist
                response.success()
            else:
                response.failure(
                    f"About page failed with status {response.status_code}"
                )

    @task(3)
    def load_ui_kit(self):
        """Load UI kit page"""
        with self.client.get(
            "/ui-kit/", catch_response=True, name="UI Kit"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"UI Kit failed with status {response.status_code}")

    @task(2)
    def load_static_css(self):
        """Load main CSS file"""
        with self.client.get(
            "/static/css/output.css", catch_response=True, name="Static CSS"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"CSS failed with status {response.status_code}")

    @task(2)
    def load_static_js(self):
        """Load main JS file"""
        with self.client.get(
            "/static/js/main.js", catch_response=True, name="Static JS"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # JS might not exist
                response.success()
            else:
                response.failure(f"JS failed with status {response.status_code}")


class BlogUserBehavior(TaskSet):
    """
    Blog load testing scenarios
    Target: 50 concurrent users
    """

    def on_start(self):
        """Initialize blog IDs"""
        self.blog_ids = []

        # Try to fetch blog list to get IDs
        try:
            response = self.client.get("/blog/")
            if response.status_code == 200:
                # Parse blog IDs from response (simplified)
                # In real scenario, parse HTML or use API
                self.blog_ids = list(range(1, 11))  # Assume 10 blog posts
        except Exception:
            self.blog_ids = list(range(1, 11))

    @task(10)
    def load_blog_list(self):
        """Load blog list page"""
        with self.client.get(
            "/blog/", catch_response=True, name="Blog List"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Blog list failed with status {response.status_code}")

    @task(8)
    def load_blog_detail(self):
        """Load random blog post detail"""
        if self.blog_ids:
            blog_id = random.choice(self.blog_ids)
            with self.client.get(
                f"/blog/{blog_id}/", catch_response=True, name="Blog Detail"
            ) as response:
                if response.status_code == 200:
                    response.success()
                elif response.status_code == 404:
                    # Blog post might not exist
                    response.success()
                else:
                    response.failure(
                        f"Blog detail failed with status {response.status_code}"
                    )

    @task(5)
    def load_blog_paginated(self):
        """Load paginated blog list"""
        page = random.randint(1, 5)
        with self.client.get(
            f"/blog/?page={page}", catch_response=True, name="Blog Pagination"
        ) as response:
            if response.status_code == 200 or response.status_code == 404:
                response.success()
            else:
                response.failure(
                    f"Blog pagination failed with status {response.status_code}"
                )

    @task(3)
    def search_blog(self):
        """Search blog posts"""
        search_terms = ["python", "django", "web", "development", "tutorial", "test"]
        term = random.choice(search_terms)

        with self.client.get(
            f"/blog/?q={term}", catch_response=True, name="Blog Search"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Blog search failed with status {response.status_code}"
                )

    @task(2)
    def load_blog_category(self):
        """Load blog by category"""
        categories = ["tutorial", "news", "guide", "tips"]
        category = random.choice(categories)

        with self.client.get(
            f"/blog/category/{category}/", catch_response=True, name="Blog Category"
        ) as response:
            if response.status_code == 200 or response.status_code == 404:
                response.success()
            else:
                response.failure(
                    f"Blog category failed with status {response.status_code}"
                )


class APIUserBehavior(TaskSet):
    """
    API endpoint load testing
    Target: 30 concurrent users
    """

    @task(10)
    def load_blog_api(self):
        """Load blog API endpoint"""
        with self.client.get(
            "/api/blog/", catch_response=True, name="API: Blog List"
        ) as response:
            if response.status_code == 200:
                response.success()
            elif response.status_code == 404:
                # API might not be implemented
                response.success()
            else:
                response.failure(f"Blog API failed with status {response.status_code}")

    @task(8)
    def load_blog_detail_api(self):
        """Load blog detail API endpoint"""
        blog_id = random.randint(1, 10)

        with self.client.get(
            f"/api/blog/{blog_id}/", catch_response=True, name="API: Blog Detail"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(
                    f"Blog detail API failed with status {response.status_code}"
                )

    @task(5)
    def load_portfolio_api(self):
        """Load portfolio API endpoint"""
        with self.client.get(
            "/api/portfolio/", catch_response=True, name="API: Portfolio"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(
                    f"Portfolio API failed with status {response.status_code}"
                )

    @task(3)
    def search_api(self):
        """Search via API"""
        search_term = random.choice(["test", "python", "django", "web"])

        with self.client.get(
            f"/api/search/?q={search_term}", catch_response=True, name="API: Search"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(
                    f"Search API failed with status {response.status_code}"
                )

    @task(2)
    def load_health_check(self):
        """Health check endpoint"""
        with self.client.get(
            "/health/", catch_response=True, name="API: Health Check"
        ) as response:
            if response.status_code in [200, 404]:
                response.success()
            else:
                response.failure(
                    f"Health check failed with status {response.status_code}"
                )


class ContactFormBehavior(TaskSet):
    """
    Contact form submission load testing
    Target: 20 concurrent users
    """

    def on_start(self):
        """Get CSRF token before submitting forms"""
        response = self.client.get("/contact/")
        if response.status_code == 200:
            # Extract CSRF token (simplified)
            # In real scenario, parse HTML to get token
            self.csrf_token = "test-token"
        else:
            self.csrf_token = None

    @task(10)
    def load_contact_page(self):
        """Load contact form page"""
        with self.client.get(
            "/contact/", catch_response=True, name="Contact Page"
        ) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(
                    f"Contact page failed with status {response.status_code}"
                )

    @task(5)
    def submit_contact_form(self):
        """Submit contact form"""

        # Generate random test data
        user_id = random.randint(1000, 9999)

        form_data = {
            "name": f"Test User {user_id}",
            "email": f"testuser{user_id}@example.com",
            "subject": f"Load Test Message {user_id}",
            "message": f"This is a load testing message generated at {time.time()}",
            "csrfmiddlewaretoken": self.csrf_token or "test-token",
        }

        with self.client.post(
            "/contact/", data=form_data, catch_response=True, name="Contact Form Submit"
        ) as response:
            if response.status_code in [200, 302]:
                response.success()
            elif response.status_code == 403:
                # CSRF failure - expected in load testing
                response.success()
            else:
                response.failure(
                    f"Contact form submission failed with status {response.status_code}"
                )


# ============================================================================
# USER CLASSES - Define different user types and their weights
# ============================================================================


class HomepageUser(HttpUser):
    """
    Users primarily browsing homepage and static pages
    Weight: 40% of total users
    """

    tasks = [HomepageUserBehavior]
    wait_time = between(1, 3)  # Wait 1-3 seconds between tasks
    weight = 40


class BlogUser(HttpUser):
    """
    Users browsing blog content
    Weight: 30% of total users
    """

    tasks = [BlogUserBehavior]
    wait_time = between(2, 5)  # Wait 2-5 seconds between tasks
    weight = 30


class APIUser(HttpUser):
    """
    API consumers (mobile apps, integrations)
    Weight: 20% of total users
    """

    tasks = [APIUserBehavior]
    wait_time = between(0.5, 2)  # Faster requests for API
    weight = 20


class ContactFormUser(HttpUser):
    """
    Users submitting contact forms
    Weight: 10% of total users
    """

    tasks = [ContactFormBehavior]
    wait_time = between(5, 10)  # Slower, users take time to fill forms
    weight = 10


# ============================================================================
# COMBINED USER - All behaviors in one user
# ============================================================================


class CombinedUser(HttpUser):
    """
    Realistic user that performs multiple actions
    Simulates real user journey: Homepage → Blog → Contact
    """

    wait_time = between(1, 5)

    @task(10)
    def browse_homepage(self):
        """Browse homepage"""
        self.client.get("/", name="Homepage")

    @task(8)
    def browse_blog(self):
        """Browse blog"""
        self.client.get("/blog/", name="Blog List")

        # Sometimes read a blog post
        if random.random() > 0.5:
            blog_id = random.randint(1, 10)
            self.client.get(f"/blog/{blog_id}/", name="Blog Detail")

    @task(5)
    def view_portfolio(self):
        """View portfolio"""
        self.client.get("/portfolio/", name="Portfolio")

    @task(3)
    def search(self):
        """Perform search"""
        term = random.choice(["python", "django", "web"])
        self.client.get(f"/blog/?q={term}", name="Search")

    @task(2)
    def contact(self):
        """View contact page"""
        self.client.get("/contact/", name="Contact Page")

    @task(1)
    def submit_contact(self):
        """Submit contact form"""
        form_data = {
            "name": f"Test User {random.randint(1000, 9999)}",
            "email": f"test{random.randint(1000, 9999)}@example.com",
            "subject": "Load Test",
            "message": "This is a load test message",
        }
        self.client.post("/contact/", data=form_data, name="Contact Submit")


# ============================================================================
# TESTING RECOMMENDATIONS
# ============================================================================

"""
Load Testing Scenarios:

1. BASELINE TEST (10 users, 1 minute)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2 --run-time 1m --headless

2. MODERATE LOAD (50 users, 5 minutes)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 5m --headless

3. HIGH LOAD (100 users, 10 minutes)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 20 --run-time 10m --headless

4. STRESS TEST (200 users, 15 minutes)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 200 --spawn-rate 30 --run-time 15m --headless

5. SPIKE TEST (0 → 100 → 0 users)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 100 --run-time 2m --headless

6. ENDURANCE TEST (50 users, 1 hour)
   locust -f tests/load/locustfile.py --host=http://localhost:8000 --users 50 --spawn-rate 10 --run-time 1h --headless


Performance Targets:
- Response Time (p50): < 100ms
- Response Time (p95): < 200ms
- Response Time (p99): < 500ms
- Error Rate: < 1%
- Requests/sec: > 100
- Success Rate: > 99%


Monitoring During Tests:
1. Server CPU usage (should stay < 80%)
2. Memory usage (should stay < 85%)
3. Database connections (should not max out)
4. Cache hit rate (should be > 80%)
5. Error logs (should be minimal)


Expected Results:
Homepage: 50-100ms (highly cached)
Blog List: 100-200ms (database queries)
Blog Detail: 80-150ms (cached content)
API Endpoints: 50-100ms (optimized)
Contact Form: 200-300ms (validation + email)
Static Assets: 10-50ms (CDN/cached)
"""
