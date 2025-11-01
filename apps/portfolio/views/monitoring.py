"""
Performance monitoring and dashboard views
"""

import json
import logging
import statistics
from datetime import datetime, timedelta

from django.conf import settings
from django.db import connection
from django.http import JsonResponse
from django.shortcuts import render
from django.views.decorators.csrf import csrf_protect
from django.views.decorators.http import require_http_methods

from ..alerting import alert_manager

logger = logging.getLogger(__name__)


class PerformanceMetrics:
    """
    In-memory performance metrics storage and analysis
    """

    def __init__(self):
        self.metrics = {
            "lcp": [],
            "fid": [],
            "cls": [],
            "fcp": [],
            "ttfb": [],
            "resource_load": [],
            "long_task": [],
            "network_change": [],
            "memory_usage": [],
        }
        self.alerts = []
        self.thresholds = {
            "lcp": 2500,  # milliseconds
            "fid": 100,  # milliseconds
            "cls": 0.1,  # cumulative score
            "fcp": 1800,  # milliseconds
            "ttfb": 800,  # milliseconds
            "resource_load": 3000,  # milliseconds
        }

    def add_metric(self, metric_type, value, metadata=None):
        """Add a performance metric with timestamp"""
        timestamp = datetime.now().isoformat()

        metric_data = {
            "value": value,
            "timestamp": timestamp,
            "metadata": metadata or {},
        }

        if metric_type in self.metrics:
            # Keep only last 1000 metrics per type
            self.metrics[metric_type].append(metric_data)
            if len(self.metrics[metric_type]) > 1000:
                self.metrics[metric_type].pop(0)

        # Check for performance alerts
        self._check_alert_threshold(metric_type, value)

        # Trigger alerting system
        alert_manager.check_metric_thresholds(metric_type, value)

    def _check_alert_threshold(self, metric_type, value):
        """Check if metric exceeds threshold and create alert"""
        threshold = self.thresholds.get(metric_type)
        if threshold and value > threshold:
            alert = {
                "type": "performance_alert",
                "metric": metric_type,
                "value": value,
                "threshold": threshold,
                "timestamp": datetime.now().isoformat(),
                "severity": "warning" if value < threshold * 1.5 else "critical",
            }
            self.alerts.append(alert)

            # Keep only last 100 alerts
            if len(self.alerts) > 100:
                self.alerts.pop(0)

            logger.warning(f"Performance alert: {metric_type} = {value} > {threshold}")

    def get_summary(self, hours=24):
        """Get performance summary for the last N hours"""
        cutoff_time = datetime.now() - timedelta(hours=hours)
        summary = {}

        for metric_type, data in self.metrics.items():
            if not data:
                continue

            # Filter by time
            recent_data = [
                item
                for item in data
                if datetime.fromisoformat(item["timestamp"]) > cutoff_time
            ]

            if recent_data:
                values = [item["value"] for item in recent_data]
                summary[metric_type] = {
                    "count": len(values),
                    "avg": round(statistics.mean(values), 2),
                    "min": min(values),
                    "max": max(values),
                    "median": round(statistics.median(values), 2),
                    "p95": round(self._percentile(values, 95), 2),
                    "recent": values[-10:] if len(values) >= 10 else values,
                }

        return summary

    def _percentile(self, values, p):
        """Calculate percentile"""
        k = (len(values) - 1) * p / 100
        f = int(k)
        c = k - f
        if f == len(values) - 1:
            return values[f]
        return values[f] * (1 - c) + values[f + 1] * c

    def get_health_score(self):
        """Calculate overall performance health score (0-100)"""
        scores = {}
        total_score = 0
        count = 0

        recent_summary = self.get_summary(hours=1)  # Last hour

        # Score each metric type
        for metric_type, data in recent_summary.items():
            if metric_type in self.thresholds:
                threshold = self.thresholds[metric_type]
                avg_value = data["avg"]

                if avg_value <= threshold * 0.5:
                    score = 100  # Excellent
                elif avg_value <= threshold:
                    score = 80  # Good
                elif avg_value <= threshold * 1.5:
                    score = 60  # Fair
                elif avg_value <= threshold * 2:
                    score = 40  # Poor
                else:
                    score = 20  # Critical

                scores[metric_type] = score
                total_score += score
                count += 1

        overall_score = round(total_score / count) if count > 0 else 100

        return {
            "overall": overall_score,
            "individual": scores,
            "grade": self._get_grade(overall_score),
        }

    def _get_grade(self, score):
        """Convert score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"


# Global metrics instance
performance_metrics = PerformanceMetrics()


@csrf_protect
@require_http_methods(["GET"])
def dashboard(request):
    """
    Performance monitoring dashboard
    """
    try:
        # Get performance summary
        summary = performance_metrics.get_summary()
        health_score = performance_metrics.get_health_score()
        recent_alerts = alert_manager.get_active_alerts()[-10:]  # Last 10 alerts
        alert_summary = alert_manager.get_alert_summary()

        # Get system info
        system_info = {
            "cache_status": "Redis" if hasattr(settings, "CACHES") else "Local",
            "debug_mode": settings.DEBUG,
            "database_status": "Connected",
            "timestamp": datetime.now().isoformat(),
        }

        # Test database connection
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                system_info["database_status"] = "Connected"
        except Exception:
            system_info["database_status"] = "Error"

        context = {
            "summary": summary,
            "health_score": health_score,
            "alerts": recent_alerts,
            "alert_summary": alert_summary,
            "system_info": system_info,
            "thresholds": performance_metrics.thresholds,
        }

        return render(request, "monitoring/dashboard.html", context)

    except Exception as e:
        logger.error(f"Dashboard error: {e}")
        return render(
            request,
            "monitoring/dashboard.html",
            {"error": "Unable to load performance data"},
        )


@csrf_protect
@require_http_methods(["GET"])
def metrics_api(request):
    """
    API endpoint for real-time metrics data
    """
    try:
        hours = int(request.GET.get("hours", 1))
        summary = performance_metrics.get_summary(hours=hours)
        health_score = performance_metrics.get_health_score()

        return JsonResponse(
            {
                "status": "ok",
                "summary": summary,
                "health_score": health_score,
                "alerts_count": len(performance_metrics.alerts),
                "timestamp": datetime.now().isoformat(),
            }
        )

    except Exception as e:
        logger.error(f"Metrics API error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Unable to fetch metrics"}, status=500
        )


@csrf_protect
@require_http_methods(["POST"])
def collect_metric(request):
    """
    Collect performance metric from client
    """
    try:
        data = json.loads(request.body)

        # Validate and sanitize the incoming metric
        from ..api_views import validate_performance_data

        validated_data = validate_performance_data(data)

        if "error" in validated_data:
            return JsonResponse(
                {"status": "error", "message": validated_data["error"]}, status=400
            )

        # Add metric to our collection
        metric_type = validated_data["metric_type"]
        value = validated_data["value"]
        metadata = {
            "url": validated_data.get("url"),
            "user_agent": validated_data.get("user_agent"),
            "viewport_size": validated_data.get("viewport_size"),
            "connection_type": validated_data.get("connection_type"),
            "device_type": validated_data.get("device_type"),
        }

        performance_metrics.add_metric(metric_type, value, metadata)

        return JsonResponse(
            {
                "status": "ok",
                "message": "Metric collected",
                "timestamp": datetime.now().isoformat(),
            }
        )

    except json.JSONDecodeError:
        return JsonResponse({"status": "error", "message": "Invalid JSON"}, status=400)
    except Exception as e:
        logger.error(f"Metric collection error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Internal server error"}, status=500
        )


@csrf_protect
@require_http_methods(["GET"])
def alerts_api(request):
    """
    Get performance alerts
    """
    try:
        severity = request.GET.get("severity")
        alerts = alert_manager.get_active_alerts(severity=severity)
        alert_summary = alert_manager.get_alert_summary()

        return JsonResponse(
            {
                "status": "ok",
                "alerts": alerts[-50:],  # Last 50 alerts
                "summary": alert_summary,
                "count": len(alerts),
            }
        )

    except Exception as e:
        logger.error(f"Alerts API error: {e}")
        return JsonResponse(
            {"status": "error", "message": "Unable to fetch alerts"}, status=500
        )
