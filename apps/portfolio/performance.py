"""
Performance Monitoring System
============================

This module provides comprehensive performance monitoring capabilities including:
- Core Web Vitals tracking (LCP, FID, CLS, FCP, TTFB)
- Performance metrics collection and storage
- Real-time alerting system
- Dashboard data aggregation

Features:
- In-memory storage for real-time metrics
- Configurable thresholds and alerting
- Performance scoring and health calculation
- Thread-safe operations for concurrent access
"""

import logging
import threading
import time
from collections import defaultdict, deque
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import Any, Dict, List, Tuple

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from apps.portfolio.utils.metrics_summary import create_summary_generator

logger = logging.getLogger(__name__)


@dataclass
class MetricEntry:
    """Single performance metric entry"""

    metric_type: str
    value: float
    timestamp: datetime
    url: str = ""
    user_agent: str = ""
    device_type: str = "desktop"
    connection_type: str = "unknown"
    additional_data: Dict[str, Any] = field(default_factory=dict)


@dataclass
class AlertConfig:
    """Alert configuration for performance thresholds"""

    metric_type: str
    threshold: float
    enabled: bool = True
    cooldown_minutes: int = 30
    email_enabled: bool = True
    console_enabled: bool = True
    cache_enabled: bool = True


class PerformanceMetrics:
    """
    High-performance in-memory metrics collection system

    Features:
    - Thread-safe operations
    - Configurable data retention
    - Real-time aggregation
    - Performance scoring
    - Alert management
    """

    def __init__(self, max_entries: int = 10000, retention_hours: int = 24):
        self.max_entries = max_entries
        self.retention_hours = retention_hours
        self._lock = threading.RLock()

        # In-memory storage: metric_type -> deque of MetricEntry
        self._metrics: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=self.max_entries)
        )

        # Alert tracking: metric_type -> last_alert_time
        self._last_alerts: Dict[str, datetime] = {}

        # Statistics cache for performance
        self._stats_cache: Dict[str, Tuple[Dict, datetime]] = {}
        self._cache_ttl = 60  # Cache for 60 seconds

        # Core Web Vitals thresholds (in milliseconds or ratio)
        self.thresholds = {
            "lcp": {"good": 2500, "needs_improvement": 4000},  # ms
            "fid": {"good": 100, "needs_improvement": 300},  # ms
            "cls": {"good": 0.1, "needs_improvement": 0.25},  # ratio
            "inp": {"good": 200, "needs_improvement": 500},  # ms
            "ttfb": {"good": 800, "needs_improvement": 1800},  # ms
            "fcp": {"good": 1800, "needs_improvement": 3000},  # ms
        }

        # Alert configurations
        self.alerts = {
            "lcp": AlertConfig("lcp", 4000, cooldown_minutes=15),
            "fid": AlertConfig("fid", 300, cooldown_minutes=15),
            "cls": AlertConfig("cls", 0.25, cooldown_minutes=15),
            "inp": AlertConfig("inp", 500, cooldown_minutes=15),
            "ttfb": AlertConfig("ttfb", 1800, cooldown_minutes=10),
            "fcp": AlertConfig("fcp", 3000, cooldown_minutes=15),
        }

        # Initialize summary generator
        self._summary_generator = create_summary_generator(
            percentile_func=self._percentile,
            thresholds=self.thresholds,
            calculate_score_func=self._calculate_score,
            get_status_func=self._get_status,
        )

        logger.info("PerformanceMetrics initialized with in-memory storage")

    def add_metric(self, metric_type: str, value: float, **kwargs) -> bool:
        """
        Add a performance metric to the collection

        Args:
            metric_type: Type of metric (lcp, fid, cls, etc.)
            value: Metric value
            **kwargs: Additional metadata

        Returns:
            bool: True if metric was added successfully
        """
        try:
            with self._lock:
                entry = MetricEntry(
                    metric_type=metric_type,
                    value=value,
                    timestamp=timezone.now(),
                    url=kwargs.get("url", ""),
                    user_agent=kwargs.get("user_agent", ""),
                    device_type=kwargs.get("device_type", "desktop"),
                    connection_type=kwargs.get("connection_type", "unknown"),
                    additional_data=kwargs.get("additional_data", {}),
                )

                # Add to metrics storage
                self._metrics[metric_type].append(entry)

                # Clear stats cache for this metric type
                if metric_type in self._stats_cache:
                    del self._stats_cache[metric_type]

                # Check for alerts
                self._check_alert(metric_type, value)

                # Clean old entries periodically (every 100 additions)
                if len(self._metrics[metric_type]) % 100 == 0:
                    self._cleanup_old_entries()

                logger.debug(f"Added {metric_type} metric: {value}")
                return True

        except Exception as e:
            logger.error(f"Error adding metric {metric_type}={value}: {e}")
            return False

    def get_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """
        Get aggregated metrics summary for the last N hours

        Args:
            hours: Number of hours to look back

        Returns:
            Dict containing metrics summary

        REFACTORED: Complexity reduced from C:16 to A:1
        """
        cache_key = f"metrics_summary_{hours}h"

        # Check cache first
        cached_summary = self._get_cached_summary(cache_key)
        if cached_summary:
            return cached_summary

        try:
            with self._lock:
                # Get recent metrics data
                recent_metrics = self._filter_recent_metrics(hours)

                # Generate summary using helper
                summary = self._summary_generator.generate(
                    recent_metrics, hours, timezone.now
                )

                # Cache the result
                self._stats_cache[cache_key] = (summary, timezone.now())

                return summary

        except Exception as e:
            logger.error(f"Error generating metrics summary: {e}")
            return self._error_summary(hours, str(e))

    def _get_cached_summary(self, cache_key: str) -> Dict[str, Any] | None:
        """
        Get cached summary if available and not expired

        Complexity: A:3
        """
        if cache_key not in self._stats_cache:
            return None

        cached_data, cached_time = self._stats_cache[cache_key]
        if timezone.now() - cached_time < timedelta(seconds=self._cache_ttl):
            return cached_data

        return None

    def _filter_recent_metrics(self, hours: int) -> Dict[str, List]:
        """
        Filter metrics to only include entries from the last N hours

        Complexity: A:4
        """
        cutoff_time = timezone.now() - timedelta(hours=hours)
        recent_metrics = {}

        for metric_type, entries in self._metrics.items():
            recent_entries = [
                entry for entry in entries if entry.timestamp >= cutoff_time
            ]
            if recent_entries:
                recent_metrics[metric_type] = recent_entries

        return recent_metrics

    def _error_summary(self, hours: int, error_msg: str) -> Dict[str, Any]:
        """
        Generate error summary response

        Complexity: A:1
        """
        return {
            "period_hours": hours,
            "generated_at": timezone.now().isoformat(),
            "metrics": {},
            "health_score": "F",
            "total_entries": 0,
            "error": error_msg,
        }

    def get_real_time_data(self) -> Dict[str, Any]:
        """
        Get real-time performance data for dashboard

        Returns:
            Dict containing current performance state
        """
        try:
            with self._lock:
                current_time = timezone.now()

                # Get metrics from last 5 minutes for real-time view
                cutoff_time = current_time - timedelta(minutes=5)

                real_time_data = {
                    "timestamp": current_time.isoformat(),
                    "status": "active",
                    "current_metrics": {},
                    "alerts": [],
                    "system_health": "healthy",
                }

                for metric_type, entries in self._metrics.items():
                    recent = [e for e in entries if e.timestamp >= cutoff_time]

                    if recent:
                        latest_value = recent[-1].value
                        avg_value = sum(e.value for e in recent) / len(recent)

                        real_time_data["current_metrics"][metric_type] = {
                            "latest": latest_value,
                            "average_5min": avg_value,
                            "count_5min": len(recent),
                            "status": (
                                self._get_status(metric_type, latest_value)
                                if metric_type in self.thresholds
                                else "unknown"
                            ),
                        }

                # Check for recent alerts
                alert_cutoff = current_time - timedelta(minutes=30)
                for metric_type, last_alert in self._last_alerts.items():
                    if last_alert >= alert_cutoff:
                        real_time_data["alerts"].append(
                            {
                                "metric_type": metric_type,
                                "triggered_at": last_alert.isoformat(),
                                "minutes_ago": int(
                                    (current_time - last_alert).total_seconds() / 60
                                ),
                            }
                        )

                return real_time_data

        except Exception as e:
            logger.error(f"Error getting real-time data: {e}")
            return {
                "timestamp": timezone.now().isoformat(),
                "status": "error",
                "error": str(e),
            }

    def _check_alert(self, metric_type: str, value: float) -> None:
        """Check if metric value triggers an alert"""
        if metric_type not in self.alerts:
            return

        alert_config = self.alerts[metric_type]
        if not alert_config.enabled:
            return

        # Check if value exceeds threshold
        if value <= alert_config.threshold:
            return

        # Check cooldown period
        current_time = timezone.now()
        if metric_type in self._last_alerts:
            time_since_last = current_time - self._last_alerts[metric_type]
            if time_since_last < timedelta(minutes=alert_config.cooldown_minutes):
                return

        # Trigger alert
        self._trigger_alert(metric_type, value, alert_config)
        self._last_alerts[metric_type] = current_time

    def _trigger_alert(
        self, metric_type: str, value: float, config: AlertConfig
    ) -> None:
        """Trigger performance alert"""
        alert_message = f"Performance Alert: {metric_type.upper()} = {value:.2f} (threshold: {config.threshold})"

        try:
            # Console alert
            if config.console_enabled:
                logger.warning(alert_message)

            # Cache alert (for dashboard display)
            if config.cache_enabled:
                cache_key = f"perf_alert_{metric_type}_{int(time.time())}"
                cache.set(
                    cache_key,
                    {
                        "metric_type": metric_type,
                        "value": value,
                        "threshold": config.threshold,
                        "timestamp": timezone.now().isoformat(),
                    },
                    timeout=3600,
                )  # Keep for 1 hour

            # Email alert (if configured)
            if config.email_enabled and hasattr(settings, "PERFORMANCE_ALERT_EMAIL"):
                self._send_email_alert(metric_type, value, config.threshold)

            logger.info(
                f"Alert triggered for {metric_type}: {value} > {config.threshold}"
            )

        except Exception as e:
            logger.error(f"Error triggering alert for {metric_type}: {e}")

    def _send_email_alert(
        self, metric_type: str, value: float, threshold: float
    ) -> None:
        """Send email alert for performance issue"""
        try:
            subject = f"Performance Alert: {metric_type.upper()} Threshold Exceeded"
            message = f"""
Performance Alert Triggered
========================

Metric: {metric_type.upper()}
Current Value: {value:.2f}
Threshold: {threshold}
Time: {timezone.now().strftime('%Y-%m-%d %H:%M:%S')}

This metric has exceeded the configured threshold. Please investigate.

Dashboard: {getattr(settings, 'SITE_URL', 'http://localhost:8000')}/dashboard/
            """.strip()

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[settings.PERFORMANCE_ALERT_EMAIL],
                fail_silently=True,
            )

        except Exception as e:
            logger.error(f"Error sending email alert: {e}")

    def _cleanup_old_entries(self) -> None:
        """Remove entries older than retention period"""
        cutoff_time = timezone.now() - timedelta(hours=self.retention_hours)

        for metric_type, entries in self._metrics.items():
            # Convert to list for modification
            entries_list = list(entries)

            # Filter out old entries
            recent_entries = [e for e in entries_list if e.timestamp >= cutoff_time]

            # Replace deque contents
            entries.clear()
            entries.extend(recent_entries)

    def _calculate_score(self, metric_type: str, value: float) -> int:
        """Calculate performance score (0-100) for a metric"""
        if metric_type not in self.thresholds:
            return 50  # Neutral score for unknown metrics

        thresholds = self.thresholds[metric_type]
        good_threshold = thresholds["good"]
        needs_improvement_threshold = thresholds["needs_improvement"]

        if value <= good_threshold:
            return 100  # Perfect score
        elif value <= needs_improvement_threshold:
            # Linear scale between good and needs improvement
            ratio = (value - good_threshold) / (
                needs_improvement_threshold - good_threshold
            )
            return max(50, int(100 - (ratio * 50)))
        else:
            # Poor performance
            return max(
                0,
                int(
                    50
                    - min(
                        50,
                        (value - needs_improvement_threshold)
                        / needs_improvement_threshold
                        * 50,
                    )
                ),
            )

    def _get_status(self, metric_type: str, value: float) -> str:
        """Get status string for a metric value"""
        if metric_type not in self.thresholds:
            return "unknown"

        thresholds = self.thresholds[metric_type]
        if value <= thresholds["good"]:
            return "good"
        elif value <= thresholds["needs_improvement"]:
            return "needs_improvement"
        else:
            return "poor"

    def _percentile(self, sorted_values: List[float], percentile: int) -> float:
        """Calculate percentile value from sorted list"""
        if not sorted_values:
            return 0.0

        index = (percentile / 100.0) * (len(sorted_values) - 1)
        lower_index = int(index)
        upper_index = min(lower_index + 1, len(sorted_values) - 1)

        if lower_index == upper_index:
            return sorted_values[lower_index]

        weight = index - lower_index
        return (
            sorted_values[lower_index] * (1 - weight)
            + sorted_values[upper_index] * weight
        )

    def get_health_status(self) -> Dict[str, Any]:
        """Get overall system health status"""
        summary = self.get_metrics_summary(hours=1)

        return {
            "status": (
                "healthy" if summary["health_score"] in ["A", "B"] else "degraded"
            ),
            "health_score": summary["health_score"],
            "metrics_count": summary["total_entries"],
            "active_alerts": len(
                [
                    alert_time
                    for alert_time in self._last_alerts.values()
                    if timezone.now() - alert_time < timedelta(minutes=30)
                ]
            ),
            "timestamp": timezone.now().isoformat(),
        }


# Global instance
performance_metrics = PerformanceMetrics()


class AlertManager:
    """
    Performance Alert Management System

    Handles:
    - Threshold-based alerting
    - Multiple notification channels (email, console, cache)
    - Alert cooldown and rate limiting
    - Alert history tracking
    """

    def __init__(self, metrics_instance: PerformanceMetrics):
        self.metrics = metrics_instance
        self.logger = logging.getLogger(f"{__name__}.AlertManager")

    def configure_alert(self, metric_type: str, threshold: float, **kwargs) -> bool:
        """Configure alert for a specific metric type"""
        try:
            if metric_type not in self.metrics.alerts:
                self.metrics.alerts[metric_type] = AlertConfig(metric_type, threshold)
            else:
                self.metrics.alerts[metric_type].threshold = threshold

            # Update optional parameters
            alert_config = self.metrics.alerts[metric_type]
            alert_config.enabled = kwargs.get("enabled", alert_config.enabled)
            alert_config.cooldown_minutes = kwargs.get(
                "cooldown_minutes", alert_config.cooldown_minutes
            )
            alert_config.email_enabled = kwargs.get(
                "email_enabled", alert_config.email_enabled
            )
            alert_config.console_enabled = kwargs.get(
                "console_enabled", alert_config.console_enabled
            )
            alert_config.cache_enabled = kwargs.get(
                "cache_enabled", alert_config.cache_enabled
            )

            self.logger.info(
                f"Alert configured for {metric_type}: threshold={threshold}"
            )
            return True

        except Exception as e:
            self.logger.error(f"Error configuring alert for {metric_type}: {e}")
            return False

    def get_recent_alerts(self, minutes: int = 60) -> List[Dict[str, Any]]:
        """Get alerts from the last N minutes"""
        cutoff_time = timezone.now() - timedelta(minutes=minutes)
        recent_alerts = []

        for metric_type, alert_time in self.metrics._last_alerts.items():
            if alert_time >= cutoff_time:
                recent_alerts.append(
                    {
                        "metric_type": metric_type,
                        "triggered_at": alert_time.isoformat(),
                        "minutes_ago": int(
                            (timezone.now() - alert_time).total_seconds() / 60
                        ),
                        "threshold": (
                            self.metrics.alerts.get(metric_type, {}).threshold
                            if metric_type in self.metrics.alerts
                            else None
                        ),
                    }
                )

        return sorted(recent_alerts, key=lambda x: x["triggered_at"], reverse=True)

    def test_alert_system(self) -> Dict[str, Any]:
        """Test the alert system functionality"""
        try:
            test_results = {
                "console_alert": False,
                "cache_alert": False,
                "email_alert": False,
                "timestamp": timezone.now().isoformat(),
            }

            # Test console alert
            try:
                self.logger.warning("Alert system test: Console alert")
                test_results["console_alert"] = True
            except Exception as e:
                self.logger.error(f"Console alert test failed: {e}")

            # Test cache alert
            try:
                cache_key = f"test_alert_{int(time.time())}"
                cache.set(cache_key, {"test": True}, timeout=60)
                test_results["cache_alert"] = cache.get(cache_key) is not None
            except Exception as e:
                self.logger.error(f"Cache alert test failed: {e}")

            # Test email alert (if configured)
            if hasattr(settings, "PERFORMANCE_ALERT_EMAIL"):
                try:
                    # Don't actually send email in test, just check configuration
                    test_results["email_alert"] = bool(settings.EMAIL_HOST)
                except (AttributeError, Exception):
                    test_results["email_alert"] = False

            return test_results

        except Exception as e:
            self.logger.error(f"Alert system test failed: {e}")
            return {"error": str(e), "timestamp": timezone.now().isoformat()}


# Global alert manager instance
alert_manager = AlertManager(performance_metrics)

# Export main classes and instances
__all__ = [
    "PerformanceMetrics",
    "AlertManager",
    "MetricEntry",
    "AlertConfig",
    "performance_metrics",
    "alert_manager",
]
