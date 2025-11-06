"""
Locust Load Testing Configuration

This file defines realistic user behavior scenarios for load testing.
Run with: locust -f locustfile.py --host=http://localhost:8000

Scenarios:
- Browse homepage and navigate
- Search functionality
- Read blog posts
- View tools and resources
- Contact form submission
"""

import json
import random

from locust import HttpUser, SequentialTaskSet, between, task


class BrowseHomepageTask(SequentialTaskSet):
    """User browses homepage and navigates to different sections."""

    @task
    def view_homepage(self):
        """View homepage."""
        self.client.get("/", name="Homepage")

    @task
    def view_about(self):
        """View about section."""
        self.client.get("/#about", name="About Section")

    @task
    def view_skills(self):
        """View skills section."""
        self.client.get("/#skills", name="Skills Section")

    @task
    def view_portfolio(self):
        """View portfolio section."""
        self.client.get("/portfolio/", name="Portfolio")


class SearchTaskSet(SequentialTaskSet):
    """User performs search operations."""

    search_terms = [
        "django",
        "python",
        "security",
        "web development",
        "api",
        "database",
        "caching",
        "performance",
    ]

    @task
    def search(self):
        """Perform a search."""
        term = random.choice(self.search_terms)
        self.client.get(f"/search/?q={term}", name="Search")

    @task
    def search_autocomplete(self):
        """Test search autocomplete."""
        term = random.choice(["dja", "pyt", "sec"])
        self.client.get(
            f"/ajax/search-autocomplete/?q={term}", name="Search Autocomplete"
        )


class BlogReaderTaskSet(SequentialTaskSet):
    """User reads blog posts."""

    def on_start(self):
        """Fetch blog post list on start."""
        response = self.client.get("/blog/", name="Blog List")
        # In real scenario, parse HTML to get actual post URLs
        self.blog_posts = [
            "/blog/post-1/",
            "/blog/post-2/",
            "/blog/post-3/",
        ]

    @task(3)
    def view_blog_list(self):
        """View blog list page."""
        self.client.get("/blog/", name="Blog List")

    @task(5)
    def read_blog_post(self):
        """Read a random blog post."""
        if hasattr(self, "blog_posts"):
            post = random.choice(self.blog_posts)
            self.client.get(post, name="Read Blog Post")

    @task(1)
    def view_blog_category(self):
        """View blog by category."""
        categories = ["django", "python", "security"]
        category = random.choice(categories)
        self.client.get(f"/blog/category/{category}/", name="Blog Category")


class ToolsViewerTaskSet(SequentialTaskSet):
    """User views tools and resources."""

    @task(3)
    def view_tools_list(self):
        """View tools list."""
        self.client.get("/tools/", name="Tools List")

    @task(2)
    def view_ai_tools(self):
        """View AI tools section."""
        self.client.get("/useful/#ai-tools", name="AI Tools")

    @task(2)
    def view_security_resources(self):
        """View cybersecurity resources."""
        self.client.get("/useful/#security", name="Security Resources")

    @task(1)
    def view_tool_detail(self):
        """View specific tool detail."""
        # Mock tool IDs
        tool_id = random.randint(1, 10)
        self.client.get(f"/tools/{tool_id}/", name="Tool Detail")


class ContactFormTaskSet(SequentialTaskSet):
    """User submits contact form."""

    @task
    def view_contact_page(self):
        """View contact page and get CSRF token."""
        response = self.client.get("/contact/", name="Contact Page")
        # In production, parse CSRF token from HTML

    @task
    def submit_contact_form(self):
        """Submit contact form."""
        self.client.post(
            "/contact/",
            data={
                "name": "Load Test User",
                "email": "test@example.com",
                "subject": "Load Test",
                "message": "This is a load test message.",
            },
            name="Submit Contact Form",
        )


class APIUserTaskSet(SequentialTaskSet):
    """User interacts with API endpoints."""

    @task(3)
    def get_posts_api(self):
        """Get blog posts via API."""
        self.client.get("/api/posts/", name="API: Get Posts")

    @task(2)
    def get_tools_api(self):
        """Get tools via API."""
        self.client.get("/api/tools/", name="API: Get Tools")

    @task(2)
    def get_categories_api(self):
        """Get categories via API."""
        self.client.get("/api/categories/", name="API: Get Categories")

    @task(1)
    def search_api(self):
        """Search via API."""
        term = random.choice(["django", "python", "security"])
        self.client.get(
            f"/api/search/?q={term}",
            name="API: Search",
            headers={"Accept": "application/json"},
        )


class WebsiteUser(HttpUser):
    """
    Simulates a typical website user.

    Users will randomly choose between different task sets,
    simulating various user behaviors.
    """

    # Wait between 1-5 seconds between tasks (realistic user behavior)
    wait_time = between(1, 5)

    # Weight distribution of different user types
    tasks = {
        BrowseHomepageTask: 3,
        SearchTaskSet: 2,
        BlogReaderTaskSet: 5,
        ToolsViewerTaskSet: 3,
        ContactFormTaskSet: 1,
    }

    def on_start(self):
        """Called when a simulated user starts."""
        # Visit homepage first (realistic behavior)
        self.client.get("/")


class APIUser(HttpUser):
    """
    Simulates API client behavior.

    Focused on API endpoint testing.
    """

    # API clients typically faster
    wait_time = between(0.5, 2)

    tasks = [APIUserTaskSet]

    def on_start(self):
        """Set headers for API requests."""
        self.client.headers.update(
            {"Accept": "application/json", "Content-Type": "application/json"}
        )


class HeavyUser(HttpUser):
    """
    Simulates a heavy/power user.

    More aggressive usage patterns, less wait time.
    """

    # Heavy users wait less between actions
    wait_time = between(0.5, 2)

    tasks = {
        SearchTaskSet: 4,
        BlogReaderTaskSet: 3,
        ToolsViewerTaskSet: 2,
        APIUserTaskSet: 1,
    }


# Run configurations (use via command line)
"""
Example runs:

1. Basic test (10 users):
   locust -f locustfile.py --host=http://localhost:8000 --users 10 --spawn-rate 2

2. Medium load (100 users):
   locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10

3. Heavy load (1000 users):
   locust -f locustfile.py --host=http://localhost:8000 --users 1000 --spawn-rate 50

4. Headless mode with report:
   locust -f locustfile.py --host=http://localhost:8000 --users 100 --spawn-rate 10 --run-time 5m --headless --html report.html

5. Target specific user type:
   locust -f locustfile.py --host=http://localhost:8000 WebsiteUser --users 100

6. Stress test:
   locust -f locustfile.py --host=http://localhost:8000 --users 2000 --spawn-rate 100 --run-time 10m
"""
