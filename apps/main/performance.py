"""
Performance monitoring and alerting system.

Tracks:
- Response times
- Database query times
- Cache hit rates
- Error rates
- System resources
"""

import logging
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class PerformanceMetric:
    """Data class for performance metrics."""

    name: str
    value: float
    unit: str
    timestamp: datetime
    threshold: Optional[float] = None
    status: str = "normal"  # normal, warning, critical

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "value": self.value,
            "unit": self.unit,
            "timestamp": self.timestamp.isoformat(),
            "threshold": self.threshold,
            "status": self.status,
        }


@dataclass
class Alert:
    """Data class for performance alerts."""

    id: str
    title: str
    message: str
    severity: str  # P0, P1, P2
    metric_name: str
    metric_value: float
    threshold: float
    timestamp: datetime
    resolved: bool = False
    resolved_at: Optional[datetime] = None

    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "id": self.id,
            "title": self.title,
            "message": self.message,
            "severity": self.severity,
            "metric_name": self.metric_name,
            "metric_value": self.metric_value,
            "threshold": self.threshold,
            "timestamp": self.timestamp.isoformat(),
            "resolved": self.resolved,
            "resolved_at": self.resolved_at.isoformat() if self.resolved_at else None,
        }


class PerformanceMetrics:
    """Track and manage performance metrics."""

    # Thresholds for different metrics
    THRESHOLDS = {
        "response_time": 500,  # ms
        "database_query": 100,  # ms
        "cache_hit_rate": 70,  # percentage
        "error_rate": 0.1,  # percentage
        "memory_usage": 80,  # percentage
        "cpu_usage": 80,  # percentage
    }

    # Alerts thresholds
    ALERT_THRESHOLDS = {
        "response_time": {
            "warning": 500,  # ms (P1)
            "critical": 1000,  # ms (P0)
        },
        "error_rate": {
            "warning": 0.5,  # % (P1)
            "critical": 1.0,  # % (P0)
        },
        "cache_hit_rate": {
            "warning": 50,  # % (P2)
            "critical": 30,  # % (P1)
        },
    }

    def __init__(self):
        """Initialize performance metrics tracker."""
        self.metrics: List[PerformanceMetric] = []
        self.alerts: List[Alert] = []
        self.cache_prefix = "perf_metric_"

    def record_metric(
        self,
        name: str,
        value: float,
        unit: str,
        threshold: Optional[float] = None,
    ) -> PerformanceMetric:
        """
        Record a performance metric.

        Args:
            name: Metric name (e.g., 'response_time')
            value: Metric value
            unit: Unit of measurement (e.g., 'ms', '%')
            threshold: Optional threshold for the metric

        Returns:
            PerformanceMetric object
        """
        now = timezone.now()
        threshold = threshold or self.THRESHOLDS.get(name)

        # Determine status
        if threshold:
            if name == "cache_hit_rate" and value < threshold:
                status = "warning"
            elif value > threshold:
                status = "warning"
            else:
                status = "normal"
        else:
            status = "normal"

        metric = PerformanceMetric(
            name=name,
            value=value,
            unit=unit,
            timestamp=now,
            threshold=threshold,
            status=status,
        )

        self.metrics.append(metric)

        # Cache the metric
        cache_key = f"{self.cache_prefix}{name}:{now.timestamp()}"
        cache.set(cache_key, asdict(metric), timeout=3600)

        logger.info(f"Recorded metric: {name}={value}{unit} (status={status})")

        return metric

    def get_metrics(
        self,
        name: Optional[str] = None,
        minutes: int = 60,
    ) -> List[PerformanceMetric]:
        """
        Get recorded metrics.

        Args:
            name: Optional metric name to filter by
            minutes: Look back time in minutes

        Returns:
            List of PerformanceMetric objects
        """
        cutoff = timezone.now() - timedelta(minutes=minutes)

        if name:
            return [m for m in self.metrics if m.name == name and m.timestamp >= cutoff]

        return [m for m in self.metrics if m.timestamp >= cutoff]

    def get_average_metric(self, name: str, minutes: int = 60) -> float:
        """
        Get average value of a metric over time period.

        Args:
            name: Metric name
            minutes: Time period in minutes

        Returns:
            Average metric value
        """
        metrics = self.get_metrics(name=name, minutes=minutes)

        if not metrics:
            return 0.0

        return sum(m.value for m in metrics) / len(metrics)

    def to_dict(self) -> Dict:
        """Convert metrics to dictionary."""
        return {
            "metrics": [m.to_dict() for m in self.metrics[-100:]],  # Last 100
            "count": len(self.metrics),
        }


class AlertManager:
    """Manage performance alerts."""

    def __init__(self):
        """Initialize alert manager."""
        self.alerts: List[Alert] = []
        self.cache_prefix = "perf_alert_"

    def create_alert(
        self,
        title: str,
        message: str,
        severity: str,
        metric_name: str,
        metric_value: float,
        threshold: float,
    ) -> Alert:
        """
        Create a new alert.

        Args:
            title: Alert title
            message: Alert message
            severity: Alert severity (P0, P1, P2)
            metric_name: Name of the metric triggering the alert
            metric_value: Current metric value
            threshold: Threshold that was exceeded

        Returns:
            Alert object
        """
        alert_id = f"{metric_name}_{timezone.now().timestamp()}"

        alert = Alert(
            id=alert_id,
            title=title,
            message=message,
            severity=severity,
            metric_name=metric_name,
            metric_value=metric_value,
            threshold=threshold,
            timestamp=timezone.now(),
        )

        self.alerts.append(alert)

        # Cache the alert
        cache_key = f"{self.cache_prefix}{alert_id}"
        cache.set(cache_key, asdict(alert), timeout=86400)  # 24 hours

        self._log_alert(alert)

        return alert

    def resolve_alert(self, alert_id: str) -> Optional[Alert]:
        """
        Resolve an alert.

        Args:
            alert_id: ID of alert to resolve

        Returns:
            Resolved Alert object or None
        """
        for alert in self.alerts:
            if alert.id == alert_id:
                alert.resolved = True
                alert.resolved_at = timezone.now()
                logger.info(f"Alert resolved: {alert_id}")
                return alert

        return None

    def get_active_alerts(self, severity: Optional[str] = None) -> List[Alert]:
        """
        Get active (unresolved) alerts.

        Args:
            severity: Optional severity filter (P0, P1, P2)

        Returns:
            List of active Alert objects
        """
        active = [a for a in self.alerts if not a.resolved]

        if severity:
            return [a for a in active if a.severity == severity]

        return active

    def get_alerts(
        self,
        metric_name: Optional[str] = None,
        hours: int = 24,
    ) -> List[Alert]:
        """
        Get alerts from recent time period.

        Args:
            metric_name: Optional metric name to filter by
            hours: Look back time in hours

        Returns:
            List of Alert objects
        """
        cutoff = timezone.now() - timedelta(hours=hours)

        if metric_name:
            return [
                a
                for a in self.alerts
                if a.metric_name == metric_name and a.timestamp >= cutoff
            ]

        return [a for a in self.alerts if a.timestamp >= cutoff]

    def _log_alert(self, alert: Alert) -> None:
        """Log alert based on severity."""
        if alert.severity == "P0":
            logger.critical(f"[P0 CRITICAL] {alert.title}: {alert.message}")
        elif alert.severity == "P1":
            logger.warning(f"[P1 WARNING] {alert.title}: {alert.message}")
        else:
            logger.info(f"[P2 INFO] {alert.title}: {alert.message}")

    def to_dict(self) -> Dict:
        """Convert alerts to dictionary."""
        return {
            "alerts": [a.to_dict() for a in self.alerts[-100:]],  # Last 100
            "active_count": len(self.get_active_alerts()),
            "p0_count": len(self.get_active_alerts(severity="P0")),
            "p1_count": len(self.get_active_alerts(severity="P1")),
            "p2_count": len(self.get_active_alerts(severity="P2")),
        }


# Singleton instances
performance_metrics = PerformanceMetrics()
alert_manager = AlertManager()
