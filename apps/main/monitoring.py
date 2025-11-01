"""
Search Performance Monitoring & Logging

This module provides comprehensive monitoring for search functionality:
- Query latency tracking
- Index sync monitoring
- Error logging and alerting
- Performance metrics collection
- Dashboard data aggregation

Usage:
    from apps.main.monitoring import search_monitor

    # Log a search query
    with search_monitor.track_query('search_term'):
        results = perform_search('search_term')

    # Get performance metrics
    metrics = search_monitor.get_metrics()

    # Check index health
    health = search_monitor.check_index_health()
"""

import logging
import time
from contextlib import contextmanager
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

try:
    import sentry_sdk

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False


logger = logging.getLogger(__name__)


class SearchMonitor:
    """
    Centralized monitoring for search functionality.
    Tracks performance, errors, and usage patterns.
    """

    # Cache keys
    CACHE_KEY_METRICS = "search:metrics"
    CACHE_KEY_ERRORS = "search:errors:recent"
    CACHE_KEY_QUERIES = "search:queries:recent"
    CACHE_KEY_HEALTH = "search:health:status"

    # Thresholds
    LATENCY_WARNING_MS = 100
    LATENCY_ERROR_MS = 500
    ERROR_RATE_WARNING = 0.05  # 5%

    def __init__(self):
        """Initialize search monitor"""
        self.metrics_ttl = 3600  # 1 hour
        self.error_log_ttl = 86400  # 24 hours
        self.query_log_ttl = 3600  # 1 hour

    @contextmanager
    def track_query(self, query: str, user_id: Optional[int] = None):
        """
        Context manager to track search query performance.

        Usage:
            with search_monitor.track_query('django tutorial'):
                results = search_api(query)
        """
        start_time = time.time()
        error_occurred = False
        error_message = None

        try:
            yield
        except Exception as e:
            error_occurred = True
            error_message = str(e)
            logger.error(f"Search query error: {query} - {e}", exc_info=True)

            # Send to Sentry if available
            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)

            raise
        finally:
            duration_ms = (time.time() - start_time) * 1000

            # Log query
            self._log_query(
                query=query,
                duration_ms=duration_ms,
                error=error_occurred,
                error_message=error_message,
                user_id=user_id,
            )

            # Check if latency exceeds thresholds
            if duration_ms > self.LATENCY_ERROR_MS:
                logger.error(
                    f"Search query exceeded error threshold: {duration_ms:.2f}ms for '{query}'"
                )
            elif duration_ms > self.LATENCY_WARNING_MS:
                logger.warning(f"Search query slow: {duration_ms:.2f}ms for '{query}'")

    def _log_query(
        self,
        query: str,
        duration_ms: float,
        error: bool,
        error_message: Optional[str],
        user_id: Optional[int],
    ):
        """Log search query with metadata"""
        log_entry = {
            "timestamp": timezone.now().isoformat(),
            "query": query,
            "duration_ms": round(duration_ms, 2),
            "error": error,
            "error_message": error_message,
            "user_id": user_id,
        }

        # Update metrics
        self._update_metrics(duration_ms, error)

        # Store recent queries
        recent_queries = cache.get(self.CACHE_KEY_QUERIES, [])
        recent_queries.insert(0, log_entry)
        recent_queries = recent_queries[:100]  # Keep last 100
        cache.set(self.CACHE_KEY_QUERIES, recent_queries, self.query_log_ttl)

        # Store errors separately
        if error:
            self._log_error(log_entry)

    def _update_metrics(self, duration_ms: float, error: bool):
        """Update aggregate metrics"""
        metrics = cache.get(
            self.CACHE_KEY_METRICS,
            {
                "total_queries": 0,
                "total_errors": 0,
                "total_duration_ms": 0,
                "min_duration_ms": float("inf"),
                "max_duration_ms": 0,
                "last_updated": timezone.now().isoformat(),
            },
        )

        metrics["total_queries"] += 1
        if error:
            metrics["total_errors"] += 1

        metrics["total_duration_ms"] += duration_ms
        metrics["min_duration_ms"] = min(metrics["min_duration_ms"], duration_ms)
        metrics["max_duration_ms"] = max(metrics["max_duration_ms"], duration_ms)
        metrics["avg_duration_ms"] = (
            metrics["total_duration_ms"] / metrics["total_queries"]
        )
        metrics["error_rate"] = metrics["total_errors"] / metrics["total_queries"]
        metrics["last_updated"] = timezone.now().isoformat()

        cache.set(self.CACHE_KEY_METRICS, metrics, self.metrics_ttl)

        # Alert if error rate is high
        if metrics["error_rate"] > self.ERROR_RATE_WARNING:
            logger.warning(
                f"High search error rate: {metrics['error_rate']:.2%} "
                f"({metrics['total_errors']}/{metrics['total_queries']})"
            )

    def _log_error(self, log_entry: Dict):
        """Store error for later analysis"""
        errors = cache.get(self.CACHE_KEY_ERRORS, [])
        errors.insert(0, log_entry)
        errors = errors[:50]  # Keep last 50 errors
        cache.set(self.CACHE_KEY_ERRORS, errors, self.error_log_ttl)

    def get_metrics(self) -> Dict[str, Any]:
        """
        Get current performance metrics.

        Returns:
            dict: Performance metrics including latency, error rates, query counts
        """
        metrics = cache.get(self.CACHE_KEY_METRICS, {})

        # Add health status
        health = self.check_index_health()
        metrics["health_status"] = health["status"]
        metrics["health_message"] = health["message"]

        return metrics

    def get_recent_queries(self, limit: int = 20) -> List[Dict]:
        """Get recent search queries"""
        queries = cache.get(self.CACHE_KEY_QUERIES, [])
        return queries[:limit]

    def get_recent_errors(self, limit: int = 20) -> List[Dict]:
        """Get recent search errors"""
        errors = cache.get(self.CACHE_KEY_ERRORS, [])
        return errors[:limit]

    def check_index_health(self) -> Dict[str, Any]:
        """
        Check search index health status.

        Returns:
            dict: Health status with details
        """
        # Check cache first
        cached_health = cache.get(self.CACHE_KEY_HEALTH)
        if cached_health:
            return cached_health

        health = {
            "status": "unknown",
            "message": "Health check not performed",
            "checked_at": timezone.now().isoformat(),
            "details": {},
        }

        try:
            from apps.main.search_index import search_index_manager

            # Check if MeiliSearch is reachable
            stats = search_index_manager.index.get_stats()

            health["status"] = "healthy"
            health["message"] = "Search index is operational"
            health["details"] = {
                "document_count": stats.get("numberOfDocuments", 0),
                "is_indexing": stats.get("isIndexing", False),
                "field_distribution": stats.get("fieldDistribution", {}),
            }

            # Check if indexing is stuck
            if stats.get("isIndexing") and stats.get("numberOfDocuments", 0) == 0:
                health["status"] = "warning"
                health["message"] = "Indexing in progress but no documents yet"

        except Exception as e:
            health["status"] = "error"
            health["message"] = f"Health check failed: {str(e)}"
            logger.error(f"Search index health check failed: {e}", exc_info=True)

            if SENTRY_AVAILABLE:
                sentry_sdk.capture_exception(e)

        # Cache health status for 5 minutes
        cache.set(self.CACHE_KEY_HEALTH, health, 300)

        return health

    def log_index_sync(
        self,
        model_name: str,
        operation: str,
        success: bool,
        duration_ms: float,
        document_count: int = 1,
        error: Optional[str] = None,
    ):
        """
        Log index synchronization event.

        Args:
            model_name: Name of the model being synced
            operation: 'index', 'delete', 'bulk_index'
            success: Whether operation succeeded
            duration_ms: Operation duration in milliseconds
            document_count: Number of documents affected
            error: Error message if failed
        """
        log_entry = {
            "timestamp": timezone.now().isoformat(),
            "model": model_name,
            "operation": operation,
            "success": success,
            "duration_ms": round(duration_ms, 2),
            "document_count": document_count,
            "error": error,
        }

        if success:
            logger.info(
                f"Index sync: {operation} {document_count} {model_name} "
                f"documents in {duration_ms:.2f}ms"
            )
        else:
            logger.error(f"Index sync failed: {operation} {model_name} - {error}")

            if SENTRY_AVAILABLE:
                sentry_sdk.capture_message(
                    f"Index sync failure: {model_name} {operation}",
                    level="error",
                    extras=log_entry,
                )

        # Store sync events
        sync_events = cache.get("search:sync:events", [])
        sync_events.insert(0, log_entry)
        sync_events = sync_events[:100]
        cache.set("search:sync:events", sync_events, 86400)

    def get_dashboard_data(self) -> Dict[str, Any]:
        """
        Get comprehensive dashboard data.

        Returns:
            dict: All monitoring data for admin dashboard
        """
        return {
            "metrics": self.get_metrics(),
            "recent_queries": self.get_recent_queries(10),
            "recent_errors": self.get_recent_errors(10),
            "health": self.check_index_health(),
            "sync_events": cache.get("search:sync:events", [])[:10],
        }

    def reset_metrics(self):
        """Reset all metrics (use with caution)"""
        cache.delete(self.CACHE_KEY_METRICS)
        cache.delete(self.CACHE_KEY_ERRORS)
        cache.delete(self.CACHE_KEY_QUERIES)
        cache.delete(self.CACHE_KEY_HEALTH)
        cache.delete("search:sync:events")
        logger.info("Search monitoring metrics reset")


# Global instance
search_monitor = SearchMonitor()
