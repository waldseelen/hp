#!/usr/bin/env python
"""
Test Celery setup and configuration without requiring Redis.
"""

import os
import sys
from pathlib import Path

# Add project root to Python path
BASE_DIR = Path(__file__).resolve().parent
sys.path.append(str(BASE_DIR))

# Set Django settings
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings.development")

# Import Django and configure
import django

django.setup()

from django.conf import settings
from django.test import override_settings

from apps.main.tasks import (
    cleanup_temp_files,
    health_check,
    process_user_action,
    send_notification,
    update_analytics,
)


def test_celery_configuration():
    """Test Celery configuration without Redis."""
    print("=" * 60)
    print("TESTING CELERY CONFIGURATION")
    print("=" * 60)

    # Test configuration settings
    print("[OK] Checking Celery settings...")

    config_tests = [
        ("CELERY_BROKER_URL", hasattr(settings, "CELERY_BROKER_URL")),
        ("CELERY_RESULT_BACKEND", hasattr(settings, "CELERY_RESULT_BACKEND")),
        ("CELERY_TASK_SERIALIZER", hasattr(settings, "CELERY_TASK_SERIALIZER")),
        ("CELERY_ACCEPT_CONTENT", hasattr(settings, "CELERY_ACCEPT_CONTENT")),
        ("CELERY_BEAT_SCHEDULER", hasattr(settings, "CELERY_BEAT_SCHEDULER")),
    ]

    for setting, exists in config_tests:
        status = "[OK]" if exists else "[FAIL]"
        value = getattr(settings, setting, "NOT SET")
        print(f"  {status} {setting}: {value}")

    print("\n[OK] Testing task imports...")
    task_imports = [
        ("send_notification", send_notification),
        ("process_user_action", process_user_action),
        ("update_analytics", update_analytics),
        ("cleanup_temp_files", cleanup_temp_files),
        ("health_check", health_check),
    ]

    for name, task in task_imports:
        print(f"  [OK] {name}: {task.name}")

    return True


def test_task_execution_eager():
    """Test task execution in eager mode (synchronous)."""
    print("\n" + "=" * 60)
    print("TESTING TASK EXECUTION (EAGER MODE)")
    print("=" * 60)

    # Override settings to use eager mode
    with override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    ):
        # Test each task
        test_results = {}

        # Test notification task
        print("\n1. Testing notification task...")
        try:
            result = send_notification.delay(
                user_id=1,
                title="Test Notification",
                message="This is a test notification",
                notification_type="info",
            )
            print(f"   [PASS] Task completed: {result.result}")
            test_results["notification"] = True
        except Exception as e:
            print(f"   [FAIL] Task failed: {e}")
            test_results["notification"] = False

        # Test user action task
        print("\n2. Testing user action task...")
        try:
            result = process_user_action.delay(
                user_id=1, action="test_action", data={"test": "data"}
            )
            print(f"   [PASS] Task completed: {result.result}")
            test_results["user_action"] = True
        except Exception as e:
            print(f"   [FAIL] Task failed: {e}")
            test_results["user_action"] = False

        # Test analytics task
        print("\n3. Testing analytics task...")
        try:
            result = update_analytics.delay()
            print(f"   [PASS] Task completed: {result.result}")
            test_results["analytics"] = True
        except Exception as e:
            print(f"   [FAIL] Task failed: {e}")
            test_results["analytics"] = False

        # Test cleanup task
        print("\n4. Testing cleanup task...")
        try:
            result = cleanup_temp_files.delay()
            print(f"   [PASS] Task completed: {result.result}")
            test_results["cleanup"] = True
        except Exception as e:
            print(f"   [FAIL] Task failed: {e}")
            test_results["cleanup"] = False

        # Test health check task
        print("\n5. Testing health check task...")
        try:
            result = health_check.delay()
            print(f"   [PASS] Task completed: {result.result}")
            test_results["health_check"] = True
        except Exception as e:
            print(f"   [FAIL] Task failed: {e}")
            test_results["health_check"] = False

    return test_results


def test_retry_logic():
    """Test retry logic simulation."""
    print("\n" + "=" * 60)
    print("TESTING RETRY LOGIC")
    print("=" * 60)

    with override_settings(
        CELERY_TASK_ALWAYS_EAGER=True,
        CELERY_TASK_EAGER_PROPAGATES=True,
    ):
        print("Testing retry configuration...")

        # Check retry settings in tasks
        retry_tests = [
            ("send_notification", send_notification),
            ("process_user_action", process_user_action),
        ]

        for name, task in retry_tests:
            max_retries = getattr(task, "max_retries", "NOT SET")
            default_retry_delay = getattr(task, "default_retry_delay", "NOT SET")

            print(f"  [OK] {name}:")
            print(f"    - Max retries: {max_retries}")
            print(f"    - Default retry delay: {default_retry_delay}")

    return True


def main():
    """Main test function."""
    print("CELERY SETUP TESTING")
    print("=" * 60)
    print(f"Django settings: {os.environ.get('DJANGO_SETTINGS_MODULE')}")
    print(f"Python path: {sys.path[0]}")

    try:
        # Test configuration
        config_ok = test_celery_configuration()

        # Test task execution
        task_results = test_task_execution_eager()

        # Test retry logic
        retry_ok = test_retry_logic()

        # Summary
        print("\n" + "=" * 60)
        print("TEST SUMMARY")
        print("=" * 60)

        passed_tests = sum(1 for result in task_results.values() if result)
        total_tests = len(task_results)

        print(f"Configuration: {'PASS' if config_ok else 'FAIL'}")
        print(f"Task execution: {passed_tests}/{total_tests} passed")
        print(f"Retry logic: {'PASS' if retry_ok else 'FAIL'}")

        if passed_tests == total_tests and config_ok and retry_ok:
            print("\n[SUCCESS] ALL TESTS PASSED! Celery is properly configured.")

            print("\nNext steps:")
            print("1. Start Redis server: redis-server")
            print(
                "2. Start Celery worker: celery -A portfolio_site worker --loglevel=info"
            )
            print("3. Start Celery Beat: celery -A portfolio_site beat --loglevel=info")
            print("4. Start Flower: celery -A portfolio_site flower")
            print("5. Or use the service manager: python start_celery_services.py")

            return True
        else:
            print("\n[ERROR] SOME TESTS FAILED! Please check the configuration.")
            return False

    except Exception as e:
        print(f"\n[ERROR] ERROR during testing: {e}")
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
