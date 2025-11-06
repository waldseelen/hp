#!/usr/bin/env python
"""
Load Testing Runner Script

Automated script to run Locust load tests and generate comprehensive reports.
Usage: python scripts/run_load_tests.py
"""

import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path


def ensure_django_running():
    """Check if Django dev server is running."""
    import socket

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    result = sock.connect_ex(("127.0.0.1", 8000))
    sock.close()

    if result != 0:
        print("❌ Django server not running on port 8000!")
        print("Please start Django server first:")
        print("  python manage.py runserver")
        sys.exit(1)

    print("✅ Django server is running")


def run_load_test(users, spawn_rate, duration, test_name):
    """Run a load test with specified parameters."""
    print(f"\n{'=' * 70}")
    print(f"🚀 Running {test_name}")
    print(f"   Users: {users} | Spawn Rate: {spawn_rate} | Duration: {duration}")
    print(f"{'=' * 70}\n")

    # Create reports directory
    reports_dir = Path("reports/load_tests")
    reports_dir.mkdir(parents=True, exist_ok=True)

    # Generate report filename with timestamp
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    report_name = f"{test_name}_{users}users_{timestamp}"
    html_report = reports_dir / f"{report_name}.html"
    csv_report = reports_dir / f"{report_name}_stats.csv"

    # Run Locust in headless mode
    cmd = [
        "locust",
        "-f",
        "locustfile.py",
        "--host",
        "http://localhost:8000",
        "--users",
        str(users),
        "--spawn-rate",
        str(spawn_rate),
        "--run-time",
        duration,
        "--headless",
        "--html",
        str(html_report),
        "--csv",
        str(csv_report.with_suffix("")),
        "--loglevel",
        "INFO",
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print(result.stdout)
        print(f"\n✅ {test_name} completed!")
        print(f"📊 HTML Report: {html_report}")
        print(f"📈 CSV Stats: {csv_report}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"\n❌ {test_name} failed!")
        print(f"Error: {e.stderr}")
        return False


def run_test_suite():
    """Run complete load testing suite."""
    print("\n" + "=" * 70)
    print("🧪 LOAD TESTING SUITE")
    print("=" * 70)

    tests = [
        # (users, spawn_rate, duration, name)
        (10, 2, "2m", "warmup"),
        (50, 10, "3m", "light_load"),
        (100, 20, "5m", "medium_load"),
        (500, 50, "5m", "heavy_load"),
        (1000, 100, "10m", "stress_test"),
    ]

    results = []

    for users, spawn_rate, duration, test_name in tests:
        print(f"\n⏳ Waiting 30 seconds before next test...")
        time.sleep(30)

        success = run_load_test(users, spawn_rate, duration, test_name)
        results.append((test_name, success))

    # Summary
    print("\n" + "=" * 70)
    print("📊 LOAD TESTING SUMMARY")
    print("=" * 70)

    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name:20s} {status}")

    print("\n" + "=" * 70)

    total_tests = len(results)
    passed_tests = sum(1 for _, success in results if success)

    print(f"\nTotal Tests: {total_tests}")
    print(f"Passed: {passed_tests}")
    print(f"Failed: {total_tests - passed_tests}")
    print(f"Success Rate: {(passed_tests / total_tests * 100):.1f}%")

    if passed_tests == total_tests:
        print("\n🎉 All load tests passed!")
        return 0
    else:
        print("\n⚠️  Some load tests failed. Check reports for details.")
        return 1


def quick_test():
    """Run a quick load test for development."""
    print("\n🏃 Running Quick Load Test")
    return run_load_test(50, 10, "2m", "quick_test")


def stress_test():
    """Run stress test only."""
    print("\n💪 Running Stress Test")
    return run_load_test(1000, 100, "10m", "stress_test")


def main():
    """Main entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Load Testing Runner")
    parser.add_argument(
        "--mode",
        choices=["quick", "stress", "full"],
        default="quick",
        help="Test mode: quick (50 users), stress (1000 users), full (complete suite)",
    )

    args = parser.parse_args()

    # Check Django server
    ensure_django_running()

    # Run tests based on mode
    if args.mode == "quick":
        success = quick_test()
        return 0 if success else 1
    elif args.mode == "stress":
        success = stress_test()
        return 0 if success else 1
    elif args.mode == "full":
        return run_test_suite()


if __name__ == "__main__":
    sys.exit(main())
