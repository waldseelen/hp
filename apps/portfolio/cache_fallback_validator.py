"""
Cache fallback validation utilities
"""

import logging

from django.core.cache import cache
from django.test import RequestFactory

from apps.main.views import home
from apps.portfolio.utils.cache_test_helpers import CacheFallbackTester
from apps.portfolio.views import personal_page

logger = logging.getLogger(__name__)


def test_cache_fallbacks():
    """
    Test that fallback data is properly returned when cache is empty.

    This function simulates cache misses and verifies that:
    1. Views return fallback data when cache is empty
    2. Fallback data structure matches expected format
    3. No exceptions are raised during fallback

    REFACTORED: Complexity reduced from C:15 to A:2
    """
    tester = CacheFallbackTester(home, personal_page)
    return tester.run_tests()


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
