"""
Management command to monitor performance metrics during load tests.

Usage:
    python manage.py monitor_performance --duration 300

This command tracks:
- Request rates and response times
- Database query performance
- Cache hit rates
- Memory and CPU usage
"""

import time
from datetime import datetime

from django.core.cache import caches
from django.db import connection

import psutil

from .base_performance import BasePerformanceCommand


class Command(BasePerformanceCommand):
    help = "Monitor performance metrics during load tests"

    def collect_metrics_loop(self, duration, interval):
        """
        Implement metrics collection loop (Template Method Pattern).

        Collects metrics at regular intervals over the specified duration.
        """
        metrics = []
        start_time = time.time()

        try:
            while time.time() - start_time < duration:
                metric = self.collect_metrics()
                metrics.append(metric)

                # Display current metrics
                self.display_metrics(metric)

                time.sleep(interval)

        except KeyboardInterrupt:
            self.stdout.write(
                self.style.WARNING("\n\n⚠️  Monitoring interrupted by user")
            )

        return metrics

    def generate_report(self, metrics):
        """
        Generate performance report (Template Method Pattern).

        Uses _generate_performance_report() and displays summary.
        """
        # Generate structured report
        report = self._generate_performance_report(metrics)

        # Display summary to console
        self.display_summary(metrics)

        return report

    def collect_metrics(self):
        """Collect current performance metrics."""
        return {
            "timestamp": datetime.now().isoformat(),
            "database": self._collect_database_metrics(),
            "cache": self._collect_cache_metrics(),
            "response_time": self._collect_response_time_metrics(),
            "errors": self._collect_error_metrics(),
            "system": self.get_system_metrics(),
        }

    def _collect_database_metrics(self):
        """
        Collect comprehensive database metrics.

        Cyclomatic Complexity: 4 (Target: ≤6)
        Returns: dict with query counts, slow queries, and timing stats
        """
        try:
            queries = connection.queries
            query_count = len(queries)

            if not queries:
                return {
                    "query_count": 0,
                    "avg_query_time_ms": 0,
                    "slow_queries_count": 0,
                }

            # Analyze recent queries (last 100)
            recent_queries = queries[-100:]
            query_times = [float(q["time"]) for q in recent_queries]

            # Calculate stats
            total_time = sum(query_times)
            avg_time = total_time / len(query_times)
            slow_queries = sum(1 for t in query_times if t > 0.1)  # >100ms

            return {
                "query_count": query_count,
                "avg_query_time_ms": avg_time * 1000,
                "slow_queries_count": slow_queries,
                "max_query_time_ms": max(query_times) * 1000 if query_times else 0,
            }
        except Exception as e:
            return {"error": str(e)}

    def get_database_metrics(self):
        """Get database performance metrics (backward compatibility)."""
        return self._collect_database_metrics()

    def _collect_cache_metrics(self):
        """
        Collect comprehensive cache metrics from all cache backends.

        Cyclomatic Complexity: 4 (Target: ≤5)
        Returns: dict with hits, misses, hit rates for each cache backend
        """
        metrics = {}
        cache_backends = ["default", "api_cache", "query_cache", "template_cache"]

        for backend_name in cache_backends:
            try:
                cache = caches[backend_name]
                cache_info = self._get_backend_stats(cache)
                metrics[backend_name] = cache_info
            except Exception:
                metrics[backend_name] = {"status": "unavailable"}

        return metrics

    def _get_backend_stats(self, cache):
        """Extract stats from cache backend (Redis-specific)."""
        if not hasattr(cache, "_cache"):
            return {"status": "no_stats_available"}

        client = cache._cache.get_client()
        if not hasattr(client, "info"):
            return {"status": "no_stats_available"}

        info = client.info("stats")
        hits = info.get("keyspace_hits", 0)
        misses = info.get("keyspace_misses", 0)

        return {
            "hits": hits,
            "misses": misses,
            "hit_rate": self.calculate_hit_rate(hits, misses),
        }

    def get_cache_metrics(self):
        """Get cache performance metrics (backward compatibility)."""
        return self._collect_cache_metrics()

    def calculate_hit_rate(self, hits, misses):
        """Calculate cache hit rate percentage."""
        total = hits + misses
        if total == 0:
            return 0.0
        return (hits / total) * 100

    def _collect_response_time_metrics(self):
        """
        Collect response time metrics from recent queries.

        Cyclomatic Complexity: 3 (Target: ≤6)
        Returns: dict with p50, p95, p99 percentiles
        """
        try:
            queries = connection.queries[-1000:]  # Last 1000 queries
            if not queries:
                return {
                    "p50_ms": 0,
                    "p95_ms": 0,
                    "p99_ms": 0,
                    "sample_size": 0,
                }

            query_times = sorted([float(q["time"]) * 1000 for q in queries])
            n = len(query_times)

            return {
                "p50_ms": query_times[int(n * 0.50)] if n > 0 else 0,
                "p95_ms": query_times[int(n * 0.95)] if n > 0 else 0,
                "p99_ms": query_times[int(n * 0.99)] if n > 0 else 0,
                "sample_size": n,
            }
        except Exception as e:
            return {"error": str(e)}

    def _collect_error_metrics(self):
        """
        Collect error metrics from Django logs.

        Cyclomatic Complexity: 2 (Target: ≤5)
        Returns: dict with error counts and rates
        """
        try:
            # In a real implementation, this would query log files or monitoring system
            # For now, return placeholder metrics
            return {
                "error_count": 0,
                "error_rate": 0.0,
                "error_types": {},
                "status": "placeholder",
            }
        except Exception as e:
            return {"error": str(e)}

    def get_system_metrics(self):
        """Get system resource metrics."""
        try:
            cpu_percent = psutil.cpu_percent(interval=0.1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory.percent,
                "memory_available_mb": memory.available / (1024 * 1024),
                "disk_percent": disk.percent,
            }
        except Exception as e:
            return {"error": str(e)}

    def display_metrics(self, metric):
        """Display current metrics to console."""
        timestamp = metric["timestamp"]

        # Database metrics
        db = metric.get("database", {})
        db_queries = db.get("query_count", "N/A")
        db_avg_time = db.get("avg_query_time_ms", 0)

        # Cache metrics
        cache = metric.get("cache", {})
        api_cache = cache.get("api_cache", {})
        api_hit_rate = api_cache.get("hit_rate", 0)

        # System metrics
        system = metric.get("system", {})
        cpu = system.get("cpu_percent", 0)
        memory = system.get("memory_percent", 0)

        self.stdout.write(
            f"[{timestamp}] "
            f"DB: {db_queries} queries ({db_avg_time:.2f}ms avg) | "
            f"Cache: {api_hit_rate:.1f}% hit rate | "
            f"CPU: {cpu:.1f}% | Memory: {memory:.1f}%"
        )

    def _generate_performance_report(self, metrics):
        """
        Generate comprehensive performance report from collected metrics.

        Cyclomatic Complexity: 5 (Target: ≤6)
        Args:
            metrics: List of metric dictionaries
        Returns:
            dict: Formatted report with summaries
        """
        if not metrics:
            return {}

        report = {
            "database": self._summarize_database_metrics(metrics),
            "cache": self._summarize_cache_metrics(metrics),
            "system": self._summarize_system_metrics(metrics),
            "duration": len(metrics),
        }

        return report

    def _summarize_database_metrics(self, metrics):
        """Summarize database metrics."""
        query_times = [
            m["database"].get("avg_query_time_ms", 0)
            for m in metrics
            if "database" in m
        ]
        if not query_times:
            return {}

        return {
            "avg_query_time_ms": sum(query_times) / len(query_times),
            "min_query_time_ms": min(query_times),
            "max_query_time_ms": max(query_times),
        }

    def _summarize_cache_metrics(self, metrics):
        """Summarize cache metrics."""
        cache_backends = ["api_cache", "query_cache", "template_cache"]
        summary = {}

        for backend in cache_backends:
            hit_rates = [
                m["cache"].get(backend, {}).get("hit_rate", 0)
                for m in metrics
                if "cache" in m and backend in m["cache"]
            ]
            if hit_rates:
                summary[backend] = sum(hit_rates) / len(hit_rates)

        return summary

    def _summarize_system_metrics(self, metrics):
        """Summarize system resource metrics."""
        cpu_usage = [
            m["system"].get("cpu_percent", 0) for m in metrics if "system" in m
        ]
        memory_usage = [
            m["system"].get("memory_percent", 0) for m in metrics if "system" in m
        ]

        if not cpu_usage or not memory_usage:
            return {}

        return {
            "avg_cpu": sum(cpu_usage) / len(cpu_usage),
            "max_cpu": max(cpu_usage),
            "avg_memory": sum(memory_usage) / len(memory_usage),
            "max_memory": max(memory_usage),
        }

    def display_summary(self, metrics):
        """Display summary statistics."""
        if not metrics:
            return

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70))
        self.stdout.write(self.style.SUCCESS("📊 PERFORMANCE SUMMARY"))
        self.stdout.write(self.style.SUCCESS("=" * 70 + "\n"))

        # Database summary
        db_query_times = [
            m["database"].get("avg_query_time_ms", 0)
            for m in metrics
            if "database" in m
        ]
        if db_query_times:
            avg_db_time = sum(db_query_times) / len(db_query_times)
            max_db_time = max(db_query_times)
            min_db_time = min(db_query_times)

            self.stdout.write(f"Database Performance:")
            self.stdout.write(f"  Avg Query Time: {avg_db_time:.2f}ms")
            self.stdout.write(f"  Min Query Time: {min_db_time:.2f}ms")
            self.stdout.write(f"  Max Query Time: {max_db_time:.2f}ms")

            if avg_db_time < 50:
                self.stdout.write(
                    self.style.SUCCESS("  ✅ Database performance: EXCELLENT")
                )
            elif avg_db_time < 100:
                self.stdout.write(self.style.WARNING("  ⚠️  Database performance: GOOD"))
            else:
                self.stdout.write(
                    self.style.ERROR("  ❌ Database performance: NEEDS IMPROVEMENT")
                )

        # Cache summary
        self.stdout.write(f"\nCache Performance:")
        cache_backends = ["api_cache", "query_cache", "template_cache"]

        for backend in cache_backends:
            hit_rates = [
                m["cache"].get(backend, {}).get("hit_rate", 0)
                for m in metrics
                if "cache" in m and backend in m["cache"]
            ]
            if hit_rates:
                avg_hit_rate = sum(hit_rates) / len(hit_rates)
                self.stdout.write(f"  {backend}: {avg_hit_rate:.1f}% hit rate")

        # System summary
        cpu_usage = [
            m["system"].get("cpu_percent", 0) for m in metrics if "system" in m
        ]
        memory_usage = [
            m["system"].get("memory_percent", 0) for m in metrics if "system" in m
        ]

        if cpu_usage and memory_usage:
            avg_cpu = sum(cpu_usage) / len(cpu_usage)
            max_cpu = max(cpu_usage)
            avg_memory = sum(memory_usage) / len(memory_usage)
            max_memory = max(memory_usage)

            self.stdout.write(f"\nSystem Resources:")
            self.stdout.write(f"  Avg CPU: {avg_cpu:.1f}% (Max: {max_cpu:.1f}%)")
            self.stdout.write(
                f"  Avg Memory: {avg_memory:.1f}% (Max: {max_memory:.1f}%)"
            )

        self.stdout.write(self.style.SUCCESS("\n" + "=" * 70 + "\n"))
