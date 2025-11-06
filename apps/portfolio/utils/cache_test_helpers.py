"""
Cache Fallback Test Helpers
===========================

Helper classes for cache fallback testing using Extract Class pattern.

Complexity reduced: C:15 → A:3 (main function)
"""

import logging
from typing import Any, Dict, List

from django.core.cache import cache
from django.test import RequestFactory

logger = logging.getLogger(__name__)


class TestRequestBuilder:
    """
    Build test requests

    Complexity: A:1
    """

    @staticmethod
    def create_anonymous_request(path: str = "/"):
        """
        Create anonymous user request

        Complexity: A:1
        """
        factory = RequestFactory()
        request = factory.get(path)
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()
        return request


class ViewTester:
    """
    Test individual views for cache fallback

    Complexity: A:4
    """

    def __init__(self, request_builder: TestRequestBuilder):
        self.request_builder = request_builder

    def test_home_view(self, home_view_func) -> tuple[bool, str]:
        """
        Test home view fallback behavior

        Returns:
            (success, error_message)

        Complexity: A:4
        """
        try:
            print("Testing home view fallback...")
            cache.clear()

            request = self.request_builder.create_anonymous_request("/")
            response = home_view_func(request)

            # Check response content for fallback data
            content = response.content.decode("utf-8")
            success = all(
                [
                    "Building secure, human-centered products" in content,
                    "GitHub profile" in content,
                    "Designing secure platforms" in content,
                ]
            )

            result_msg = "PASS" if success else "FAIL"
            print(f"Home view fallback test: {result_msg}")

            return success, ""

        except Exception as e:
            error_msg = f"Home view test failed: {e}"
            logger.error(f"Home view fallback test error: {e}")
            return False, error_msg

    def test_personal_view(self, personal_view_func) -> tuple[bool, str]:
        """
        Test personal page view fallback behavior

        Returns:
            (success, error_message)

        Complexity: A:5
        """
        try:
            print("Testing personal page view fallback...")
            cache.clear()

            request = self.request_builder.create_anonymous_request("/personal/")
            response = personal_view_func(request)

            # Check response content for fallback data
            if hasattr(response, "content"):
                content = response.content.decode("utf-8")
                success = all(
                    [
                        "personal info" in content.lower()
                        or "about" in content.lower(),
                        "social links" in content.lower()
                        or "contact" in content.lower(),
                    ]
                )
            else:
                success = False

            result_msg = "PASS" if success else "FAIL"
            print(f"Personal view fallback test: {result_msg}")

            return success, ""

        except Exception as e:
            error_msg = f"Personal view test failed: {e}"
            logger.error(f"Personal view fallback test error: {e}")
            return False, error_msg


class TestResultsReporter:
    """
    Report test results

    Complexity: A:3
    """

    @staticmethod
    def print_summary(results: Dict[str, Any]) -> None:
        """
        Print test results summary

        Complexity: A:3
        """
        all_passed = (
            results["home_view"] and results["personal_view"] and not results["errors"]
        )

        print("\nCache Fallback Test Results:")
        print(f"Home View: {'✅ PASS' if results['home_view'] else '❌ FAIL'}")
        print(f"Personal View: {'✅ PASS' if results['personal_view'] else '❌ FAIL'}")
        print(
            f"Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}"
        )

        if results["errors"]:
            print(f"Errors: {len(results['errors'])}")
            for error in results["errors"]:
                print(f"  - {error}")


class CacheFallbackTester:
    """
    Orchestrate cache fallback tests

    Complexity: A:3
    """

    def __init__(self, home_view_func, personal_view_func):
        self.home_view = home_view_func
        self.personal_view = personal_view_func
        self.request_builder = TestRequestBuilder()
        self.view_tester = ViewTester(self.request_builder)
        self.reporter = TestResultsReporter()

    def run_tests(self) -> Dict[str, Any]:
        """
        Run all cache fallback tests

        Complexity: A:3
        """
        results = {"home_view": False, "personal_view": False, "errors": []}

        # Test home view
        success, error = self.view_tester.test_home_view(self.home_view)
        results["home_view"] = success
        if error:
            results["errors"].append(error)

        # Test personal view
        success, error = self.view_tester.test_personal_view(self.personal_view)
        results["personal_view"] = success
        if error:
            results["errors"].append(error)

        # Print summary
        self.reporter.print_summary(results)

        return results
