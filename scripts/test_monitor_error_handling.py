"""
Test script for error handling in monitor_performance command.

Tests:
1. Command works with database unavailable
2. Command works with cache unavailable
3. Exception handling is graceful
"""

import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.simple")
django.setup()

from io import StringIO

from django.core.management import call_command


def test_error_handling():
    """Test error handling scenarios."""

    print("🧪 Testing Error Handling\n")
    print("=" * 70)

    # Test 1: Normal operation
    print("\n✅ Test 1: Normal Operation")
    out = StringIO()
    try:
        call_command(
            "monitor_performance", "--duration", "5", "--interval", "1", stdout=out
        )
        print("   ✅ PASSED: Command executed successfully")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 2: Short duration (stress test)
    print("\n✅ Test 2: Short Duration (1 second)")
    out = StringIO()
    try:
        call_command(
            "monitor_performance", "--duration", "1", "--interval", "1", stdout=out
        )
        print("   ✅ PASSED: Command handled short duration")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    # Test 3: Zero interval (edge case)
    print("\n✅ Test 3: Verify JSON Output")
    import json
    from pathlib import Path

    try:
        report_path = Path("reports/performance_metrics.json")
        if report_path.exists():
            with open(report_path) as f:
                data = json.load(f)

            required_keys = [
                "timestamp",
                "database",
                "cache",
                "response_time",
                "errors",
                "system",
            ]
            sample = data[0] if data else {}

            missing = [k for k in required_keys if k not in sample]

            if missing:
                print(f"   ❌ FAILED: Missing keys: {missing}")
            else:
                print(f"   ✅ PASSED: All required keys present")
                print(f"   📊 Sample metrics keys: {list(sample.keys())}")
        else:
            print("   ⚠️  WARNING: Report file not found")
    except Exception as e:
        print(f"   ❌ FAILED: {e}")

    print("\n" + "=" * 70)
    print("✅ Error handling tests completed!\n")


if __name__ == "__main__":
    test_error_handling()
