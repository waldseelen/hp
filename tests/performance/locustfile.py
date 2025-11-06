"""
Load testing script for Portfolio Site using Locust.

This script defines load testing scenarios for critical endpoints
as documented in docs/monitoring/performance-monitoring.md

Usage:
    # Normal load (10 users)
    locust -f tests/performance/locustfile.py --headless -u 10 -r 2 --run-time 1m --host http://localhost:8000

    # Peak traffic (100 users)
    locust -f tests/performance/locustfile.py --headless -u 100 -r 10 --run-time 5m --host http://localhost:8000

    # Stress test (500 users)
    locust -f tests/performance/locustfile.py --headless -u 500 -r 50 --run-time 10m --host http://localhost:8000
"""

from locust import HttpUser, between, task


class PortfolioUser(HttpUser):
    """
    Simulates a typical user browsing the portfolio site.

    Wait time: 1-5 seconds between requests (realistic user behavior)
    """

    wait_time = between(1, 5)

    def on_start(self):
        """Called when a user starts - simulates user landing on site"""
        self.client.get("/")

    @task(5)
    def view_home_page(self):
        """
        Most common task - viewing the homepage.
        Weight: 5 (50% of traffic)
        """
        with self.client.get("/", catch_response=True) as response:
            if response.status_code == 200:
                response.success()
            else:
                response.failure(f"Homepage failed with status {response.status_code}")

    @task(3)
    def view_personal_page(self):
        """
        View personal/about page.
        Weight: 3 (30% of traffic)
        """
        self.client.get("/personal/")

    @task(2)
    def perform_search(self):
        """
        Search functionality test.
        Weight: 2 (20% of traffic)
        """
        search_queries = [
            "python",
            "django",
            "security",
            "performance",
            "devops",
        ]
        import random

        query = random.choice(search_queries)

        with self.client.get(
            "/api/search/",
            params={"q": query},
            headers={"X-Requested-With": "XMLHttpRequest"},
            catch_response=True,
            name="/api/search/",
        ) as response:
            if response.status_code == 200:
                try:
                    data = response.json()
                    if "results" in data:
                        response.success()
                    else:
                        response.failure("Invalid search response format")
                except Exception as e:
                    response.failure(f"Search parsing error: {e}")
            else:
                response.failure(f"Search failed with status {response.status_code}")

    @task(1)
    def view_tools_page(self):
        """
        View tools/resources pages.
        Weight: 1 (10% of traffic)
        """
        pages = ["/ai/", "/cybersecurity/", "/useful/"]
        import random

        page = random.choice(pages)
        self.client.get(page)

    @task(1)
    def view_health_check(self):
        """
        Health check endpoint (for monitoring).
        Weight: 1 (10% of traffic)
        """
        self.client.get("/health/")


class AdminUser(HttpUser):
    """
    Simulates admin users accessing monitoring endpoints.

    Wait time: 5-15 seconds between requests (less frequent than regular users)
    """

    wait_time = between(5, 15)

    @task(1)
    def view_health_readiness(self):
        """Check readiness probe"""
        self.client.get("/health/readiness/")

    @task(1)
    def view_health_liveness(self):
        """Check liveness probe"""
        self.client.get("/health/liveness/")


class StressTestUser(HttpUser):
    """
    Aggressive user for stress testing.

    No wait time - hammers the server as fast as possible.
    """

    wait_time = between(0, 0.5)

    @task
    def stress_home(self):
        """Stress test homepage"""
        self.client.get("/")

    @task
    def stress_search(self):
        """Stress test search API"""
        self.client.get(
            "/api/search/",
            params={"q": "test"},
            headers={"X-Requested-With": "XMLHttpRequest"},
        )
