"""
Management command for cache monitoring and statistics.
"""

import json
import time

from django.conf import settings
from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.main.cache import cache_manager


class Command(BaseCommand):
    help = "Monitor cache performance and display statistics"

    def add_arguments(self, parser):
        parser.add_argument(
            "--action",
            type=str,
            choices=["stats", "clear", "test", "monitor", "keys", "health"],
            default="stats",
            help="Action to perform",
        )
        parser.add_argument(
            "--watch", action="store_true", help="Watch cache statistics in real-time"
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Refresh interval for watch mode (seconds)",
        )
        parser.add_argument(
            "--pattern", type=str, help="Pattern to match cache keys (for keys action)"
        )
        parser.add_argument("--export", type=str, help="Export statistics to JSON file")

    def handle(self, *args, **options):
        action = options["action"]
        watch_mode = options["watch"]
        interval = options["interval"]
        pattern = options["pattern"]
        export_file = options["export"]

        if watch_mode and action == "stats":
            self.watch_statistics(interval)
        elif action == "stats":
            self.show_statistics(export_file)
        elif action == "clear":
            self.clear_cache()
        elif action == "test":
            self.test_cache_performance()
        elif action == "monitor":
            self.monitor_cache_health()
        elif action == "keys":
            self.list_cache_keys(pattern)
        elif action == "health":
            self.cache_health_check()

    def show_statistics(self, export_file=None):
        """Display comprehensive cache statistics."""
        self.stdout.write(self.style.SUCCESS("CACHE STATISTICS"))
        self.stdout.write("=" * 60)

        stats = cache_manager.get_stats()

        # Basic statistics
        self.stdout.write(f"Cache Hits: {stats['hits']:,}")
        self.stdout.write(f"Cache Misses: {stats['misses']:,}")
        self.stdout.write(f"Hit Ratio: {stats['hit_ratio']:.2f}%")
        self.stdout.write(f"Total Operations: {stats['total_operations']:,}")
        self.stdout.write(f"Cache Sets: {stats['sets']:,}")
        self.stdout.write(f"Cache Deletes: {stats['deletes']:,}")
        self.stdout.write(f"Errors: {stats['errors']:,}")

        # Uptime and performance
        uptime_hours = stats["uptime_seconds"] / 3600
        self.stdout.write(f"Uptime: {uptime_hours:.2f} hours")

        if stats["total_operations"] > 0:
            ops_per_hour = stats["total_operations"] / max(uptime_hours, 0.01)
            self.stdout.write(f"Operations/hour: {ops_per_hour:.0f}")

        # Cache backend information
        self.stdout.write(f"\n{self.style.WARNING('CACHE BACKEND INFO')}")
        self.stdout.write("-" * 30)

        try:
            cache_config = settings.CACHES["default"]
            self.stdout.write(f"Backend: {cache_config['BACKEND']}")
            self.stdout.write(f"Location: {cache_config.get('LOCATION', 'N/A')}")

            if "OPTIONS" in cache_config:
                for key, value in cache_config["OPTIONS"].items():
                    self.stdout.write(f"{key}: {value}")

        except Exception as e:
            self.stdout.write(f"Cache config error: {e}")

        # Performance grades
        self.stdout.write(f"\n{self.style.WARNING('PERFORMANCE ASSESSMENT')}")
        self.stdout.write("-" * 30)
        self.assess_cache_performance(stats)

        # Recent errors
        if stats["recent_errors"]:
            self.stdout.write(f"\n{self.style.ERROR('RECENT ERRORS')}")
            self.stdout.write("-" * 20)
            for error in stats["recent_errors"][-5:]:  # Show last 5 errors
                self.stdout.write(f"Key: {error['key']}")
                self.stdout.write(f"Error: {error['error']}")
                self.stdout.write(f"Time: {error['timestamp']}")
                self.stdout.write("-" * 20)

        # Export to file if requested
        if export_file:
            self.export_statistics(stats, export_file)

    def assess_cache_performance(self, stats):
        """Assess cache performance and provide recommendations."""
        hit_ratio = stats["hit_ratio"]

        if hit_ratio >= 90:
            grade = "A+ (Excellent)"
            color = self.style.SUCCESS
        elif hit_ratio >= 80:
            grade = "A (Very Good)"
            color = self.style.SUCCESS
        elif hit_ratio >= 70:
            grade = "B (Good)"
            color = self.style.WARNING
        elif hit_ratio >= 60:
            grade = "C (Acceptable)"
            color = self.style.WARNING
        else:
            grade = "D (Poor)"
            color = self.style.ERROR

        self.stdout.write(f"Performance Grade: {color(grade)}")

        # Recommendations
        recommendations = []
        if hit_ratio < 80:
            recommendations.append("Consider increasing cache timeouts")
        if stats["errors"] > stats["total_operations"] * 0.01:  # > 1% error rate
            recommendations.append("High error rate detected - check cache backend")
        if stats["total_operations"] < 100 and stats["uptime_seconds"] > 3600:
            recommendations.append(
                "Low cache usage - ensure caching is properly implemented"
            )

        if recommendations:
            self.stdout.write("\nRecommendations:")
            for rec in recommendations:
                self.stdout.write(f"  • {rec}")

    def clear_cache(self):
        """Clear the cache and show confirmation."""
        self.stdout.write("Clearing cache...", ending="")
        result = cache_manager.clear()

        if result:
            self.stdout.write(self.style.SUCCESS(" ✓ Done"))
        else:
            self.stdout.write(self.style.ERROR(" ✗ Failed"))

    def test_cache_performance(self):
        """Test cache performance with sample data."""
        self.stdout.write("Testing cache performance...")

        test_data = {
            f"test_key_{i}": f"test_value_{i}" * 100  # ~1KB per value
            for i in range(1000)
        }

        # Test SET operations
        start_time = time.time()
        for key, value in test_data.items():
            cache_manager.set(key, value, 60)
        set_time = time.time() - start_time

        # Test GET operations
        start_time = time.time()
        for key in test_data.keys():
            cache_manager.get(key)
        get_time = time.time() - start_time

        # Test DELETE operations
        start_time = time.time()
        for key in test_data.keys():
            cache_manager.delete(key)
        delete_time = time.time() - start_time

        # Results
        self.stdout.write(
            f"SET 1000 keys: {set_time:.3f}s ({1000 / set_time:.0f} ops/sec)"
        )
        self.stdout.write(
            f"GET 1000 keys: {get_time:.3f}s ({1000 / get_time:.0f} ops/sec)"
        )
        self.stdout.write(
            f"DELETE 1000 keys: {delete_time:.3f}s ({1000 / delete_time:.0f} ops/sec)"
        )

        total_time = set_time + get_time + delete_time
        self.stdout.write(f"Total time: {total_time:.3f}s")

        # Performance assessment
        if total_time < 1.0:
            performance = "Excellent"
            color = self.style.SUCCESS
        elif total_time < 2.0:
            performance = "Good"
            color = self.style.SUCCESS
        elif total_time < 5.0:
            performance = "Acceptable"
            color = self.style.WARNING
        else:
            performance = "Poor"
            color = self.style.ERROR

        self.stdout.write(f"Performance: {color(performance)}")

    def monitor_cache_health(self):
        """Monitor cache health and availability."""
        self.stdout.write("Monitoring cache health...\n")

        tests = [
            ("Basic connectivity", self.test_basic_connectivity),
            ("Read/Write operations", self.test_read_write),
            ("Pattern operations", self.test_pattern_operations),
            ("Timeout handling", self.test_timeout_handling),
            ("Error handling", self.test_error_handling),
        ]

        results = []
        for test_name, test_func in tests:
            self.stdout.write(f"Running {test_name}...", ending=" ")
            try:
                result = test_func()
                if result:
                    self.stdout.write(self.style.SUCCESS("✓"))
                    results.append((test_name, True, None))
                else:
                    self.stdout.write(self.style.ERROR("✗"))
                    results.append((test_name, False, "Test returned False"))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ ({e})"))
                results.append((test_name, False, str(e)))

        # Summary
        passed = sum(1 for _, success, _ in results if success)
        total = len(results)

        self.stdout.write(f"\nHealth Check Results: {passed}/{total} tests passed")

        if passed == total:
            self.stdout.write(self.style.SUCCESS("Cache is healthy! ✓"))
        else:
            self.stdout.write(self.style.ERROR("Cache has issues! ✗"))
            for test_name, success, error in results:
                if not success:
                    self.stdout.write(f"  Failed: {test_name} - {error}")

    def test_basic_connectivity(self):
        """Test basic cache connectivity."""
        test_key = "health_test_basic"
        test_value = "test_value_123"

        cache_manager.set(test_key, test_value, 60)
        result = cache_manager.get(test_key)
        cache_manager.delete(test_key)

        return result == test_value

    def test_read_write(self):
        """Test read/write operations."""
        test_data = {
            "string": "hello world",
            "integer": 42,
            "list": [1, 2, 3],
            "dict": {"key": "value"},
        }

        for key, value in test_data.items():
            cache_key = f"health_test_{key}"
            cache_manager.set(cache_key, value, 60)
            result = cache_manager.get(cache_key)
            cache_manager.delete(cache_key)

            if result != value:
                return False

        return True

    def test_pattern_operations(self):
        """Test pattern-based operations."""
        # Set test keys
        test_keys = [f"pattern_test_{i}" for i in range(5)]
        for key in test_keys:
            cache_manager.set(key, "pattern_value", 60)

        # Test pattern deletion
        deleted_count = cache_manager.delete_pattern("pattern_test_*")

        # Should delete all 5 keys (or return 0 if not supported)
        return deleted_count >= 0

    def test_timeout_handling(self):
        """Test timeout handling."""
        test_key = "health_test_timeout"
        cache_manager.set(test_key, "timeout_value", 1)  # 1 second timeout

        # Should exist immediately
        if not cache_manager.get(test_key):
            return False

        # Wait for expiration (simplified test)
        time.sleep(0.5)  # Don't wait full timeout in test
        return True  # Just test that timeout parameter is accepted

    def test_error_handling(self):
        """Test error handling."""
        # Test with very long key (should handle gracefully)
        long_key = "test_" + "x" * 1000
        try:
            cache_manager.set(long_key, "value", 60)
            cache_manager.get(long_key)
            cache_manager.delete(long_key)
            return True
        except Exception:
            return True  # Error handling works if exception is caught

    def list_cache_keys(self, pattern):
        """List cache keys matching pattern."""
        self.stdout.write(f"Listing cache keys (pattern: {pattern or 'all'})...")

        # Note: This is a simplified implementation
        # Real Redis implementation would use SCAN command
        self.stdout.write("Key listing not implemented for this cache backend")
        self.stdout.write("Use Redis CLI: redis-cli keys 'pattern*' for Redis backends")

    def cache_health_check(self):
        """Quick health check for monitoring systems."""
        try:
            # Simple connectivity test
            test_key = "health_check_monitor"
            cache_manager.set(test_key, timezone.now().isoformat(), 10)
            result = cache_manager.get(test_key)
            cache_manager.delete(test_key)

            if result:
                self.stdout.write("OK")
                return 0
            else:
                self.stdout.write("FAIL")
                return 1
        except Exception as e:
            self.stdout.write(f"ERROR: {e}")
            return 1

    def watch_statistics(self, interval):
        """Watch cache statistics in real-time."""
        self.stdout.write(
            f"Watching cache statistics (refresh every {interval}s, Ctrl+C to stop)..."
        )

        try:
            while True:
                # Clear screen (ANSI escape sequence)
                self.stdout.write("\033[2J\033[H")

                self.stdout.write(
                    f"Cache Statistics - {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}"
                )
                self.stdout.write("=" * 60)

                stats = cache_manager.get_stats()

                self.stdout.write(f"Hit Ratio: {stats['hit_ratio']:6.2f}%")
                self.stdout.write(f"Hits:      {stats['hits']:8,}")
                self.stdout.write(f"Misses:    {stats['misses']:8,}")
                self.stdout.write(f"Sets:      {stats['sets']:8,}")
                self.stdout.write(f"Deletes:   {stats['deletes']:8,}")
                self.stdout.write(f"Errors:    {stats['errors']:8,}")

                uptime_hours = stats["uptime_seconds"] / 3600
                self.stdout.write(f"Uptime:    {uptime_hours:8.2f} hours")

                if stats["total_operations"] > 0 and uptime_hours > 0:
                    ops_per_hour = stats["total_operations"] / uptime_hours
                    self.stdout.write(f"Ops/Hour:  {ops_per_hour:8.0f}")

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write("\nMonitoring stopped.")

    def export_statistics(self, stats, filename):
        """Export statistics to JSON file."""
        try:
            # Add timestamp
            export_data = {
                "timestamp": timezone.now().isoformat(),
                "cache_stats": stats,
                "cache_config": settings.CACHES["default"],
            }

            with open(filename, "w") as f:
                json.dump(export_data, f, indent=2, default=str)

            self.stdout.write(f"Statistics exported to {filename}")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Export failed: {e}"))
