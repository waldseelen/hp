"""
Cache fallback validation utilities
"""

import logging

from django.core.cache import cache
from django.test import RequestFactory

from apps.main.views import home
from apps.portfolio.views import personal_page

logger = logging.getLogger(__name__)


def test_cache_fallbacks():
    """
    Test that fallback data is properly returned when cache is empty.

    This function simulates cache misses and verifies that:
    1. Views return fallback data when cache is empty
    2. Fallback data structure matches expected format
    3. No exceptions are raised during fallback
    """
    results = {"home_view": False, "personal_view": False, "errors": []}

    # Create test request
    factory = RequestFactory()

    try:
        # Test 1: Home view fallback
        print("Testing home view fallback...")

        # Clear all cache first
        cache.clear()

        # Make request to home view
        request = factory.get("/")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()

        response = home(request)

        # Check if response contains expected fallback data
        # For direct render responses, we can't easily check context
        # Check response content instead
        content = response.content.decode("utf-8")
        results["home_view"] = all(
            [
                "Building secure, human-centered products" in content,
                "GitHub profile" in content,
                "Designing secure platforms" in content,
            ]
        )

        print(f"Home view fallback test: {'PASS' if results['home_view'] else 'FAIL'}")

    except Exception as e:
        results["errors"].append(f"Home view test failed: {e}")
        logger.error(f"Home view fallback test error: {e}")

    try:
        # Test 2: Personal page view fallback
        print("Testing personal page view fallback...")

        # Clear cache again
        cache.clear()

        # Make request to personal page
        request = factory.get("/personal/")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()

        response = personal_page(request)

        # Check response content for fallback data
        if hasattr(response, "content"):
            content = response.content.decode("utf-8")
            results["personal_view"] = all(
                [
                    "personal info" in content.lower() or "about" in content.lower(),
                    "social links" in content.lower() or "contact" in content.lower(),
                ]
            )

        print(
            f"Personal view fallback test: {'PASS' if results['personal_view'] else 'FAIL'}"
        )

    except Exception as e:
        results["errors"].append(f"Personal view test failed: {e}")
        logger.error(f"Personal view fallback test error: {e}")

    # Summary
    all_passed = (
        results["home_view"] and results["personal_view"] and not results["errors"]
    )

    print("\nCache Fallback Test Results:")
    print(f"Home View: {'✅ PASS' if results['home_view'] else '❌ FAIL'}")
    print(f"Personal View: {'✅ PASS' if results['personal_view'] else '❌ FAIL'}")
    print(f"Overall: {'✅ ALL TESTS PASSED' if all_passed else '❌ SOME TESTS FAILED'}")

    if results["errors"]:
        print(f"Errors: {len(results['errors'])}")
        for error in results["errors"]:
            print(f"  - {error}")

    return results


def validate_cache_fallback_behavior():
    """
    Comprehensive validation of cache fallback behavior.

    Returns:
        dict: Validation results with detailed information
    """
    print("🔍 Validating Cache Fallback Behavior...")

    # Run the tests
    test_results = test_cache_fallbacks()

    # Additional validation
    validation_results = {
        "cache_cleared": False,
        "fallback_data_present": False,
        "no_exceptions": False,
        "performance_acceptable": False,
    }

    try:
        # Test cache clearing
        cache.set("test_key", "test_value", 30)
        cache.clear()
        validation_results["cache_cleared"] = cache.get("test_key") is None

        # Test fallback data presence
        validation_results["fallback_data_present"] = (
            test_results["home_view"] and test_results["personal_view"]
        )

        # Test no exceptions during fallback
        validation_results["no_exceptions"] = len(test_results["errors"]) == 0

        # Performance check (basic)
        import time

        start_time = time.time()
        cache.clear()  # Simulate cache miss
        factory = RequestFactory()
        request = factory.get("/")
        request.user = type("AnonymousUser", (), {"is_authenticated": False})()
        home(request)
        end_time = time.time()
        validation_results["performance_acceptable"] = (
            end_time - start_time
        ) < 2.0  # < 2 seconds

    except Exception as e:
        logger.error(f"Cache validation error: {e}")
        validation_results["errors"] = str(e)

    # Final report
    print("\n📊 Cache Fallback Validation Report:")
    print(f"Cache Clearing: {'✅' if validation_results['cache_cleared'] else '❌'}")
    print(
        f"Fallback Data: {'✅' if validation_results['fallback_data_present'] else '❌'}"
    )
    print(f"No Exceptions: {'✅' if validation_results['no_exceptions'] else '❌'}")
    print(
        f"Performance: {'✅' if validation_results['performance_acceptable'] else '❌'}"
    )

    all_valid = all(
        [
            validation_results["cache_cleared"],
            validation_results["fallback_data_present"],
            validation_results["no_exceptions"],
            validation_results["performance_acceptable"],
        ]
    )

    print(f"Overall Validation: {'✅ PASSED' if all_valid else '❌ FAILED'}")

    return {
        "test_results": test_results,
        "validation_results": validation_results,
        "overall_success": all_valid,
    }


if __name__ == "__main__":
    # Run validation when script is executed directly
    validate_cache_fallback_behavior()
