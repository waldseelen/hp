"""
Performance Alerting System
"""

import json
import logging
from datetime import datetime, timedelta

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail

logger = logging.getLogger(__name__)


class AlertManager:
    """
    Manage performance alerts and notifications
    """

    def __init__(self):
        self.alert_types = {
            "performance_degradation": {
                "threshold_multiplier": 1.5,
                "cooldown": 300,  # 5 minutes
                "severity": "warning",
            },
            "critical_performance": {
                "threshold_multiplier": 2.0,
                "cooldown": 60,  # 1 minute
                "severity": "critical",
            },
            "high_error_rate": {
                "threshold": 0.05,  # 5% error rate
                "cooldown": 300,
                "severity": "warning",
            },
            "service_unavailable": {"cooldown": 60, "severity": "critical"},
            "memory_usage_high": {
                "threshold": 0.9,  # 90% memory usage
                "cooldown": 600,  # 10 minutes
                "severity": "warning",
            },
        }

        self.notification_channels = ["email", "console", "cache"]

    def create_alert(
        self, alert_type, metric_name, current_value, threshold=None, metadata=None
    ):
        """
        Create a new performance alert
        """
        try:
            alert_config = self.alert_types.get(alert_type, {})

            # Check cooldown period
            cooldown_key = f"alert_cooldown_{alert_type}_{metric_name}"
            if cache.get(cooldown_key):
                return False  # Alert in cooldown

            alert = {
                "id": f"{alert_type}_{metric_name}_{int(datetime.now().timestamp())}",
                "type": alert_type,
                "metric": metric_name,
                "current_value": current_value,
                "threshold": threshold,
                "severity": alert_config.get("severity", "info"),
                "timestamp": datetime.now().isoformat(),
                "metadata": metadata or {},
                "status": "active",
            }

            # Set cooldown
            cooldown_duration = alert_config.get("cooldown", 300)
            cache.set(cooldown_key, True, cooldown_duration)

            # Send notifications
            self._send_notifications(alert)

            # Store alert
            self._store_alert(alert)

            logger.warning(f"Performance alert created: {alert['id']}")
            return True

        except Exception as e:
            logger.error(f"Failed to create alert: {e}")
            return False

    def _send_notifications(self, alert):
        """
        Send alert notifications through various channels
        """
        for channel in self.notification_channels:
            try:
                if channel == "email":
                    self._send_email_notification(alert)
                elif channel == "console":
                    self._send_console_notification(alert)
                elif channel == "cache":
                    self._send_cache_notification(alert)
            except Exception as e:
                logger.error(f"Failed to send {channel} notification: {e}")

    def _send_email_notification(self, alert):
        """
        Send email notification for critical alerts
        """
        if alert["severity"] not in ["critical", "warning"]:
            return

        try:
            # Get recipient from settings
            recipient = getattr(settings, "ALERT_EMAIL", None)
            if not recipient:
                return

            subject = f"🚨 Performance Alert - {alert['metric'].upper()}"

            # Create email content
            message = self._format_email_message(alert)

            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[recipient],
                fail_silently=True,
            )

            logger.info(f"Email alert sent for {alert['id']}")

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")

    def _format_email_message(self, alert):
        """
        Format alert message for email
        """
        severity_emoji = {"critical": "🔴", "warning": "🟡", "info": "🔵"}

        emoji = severity_emoji.get(alert["severity"], "⚪")

        message = f"""
{emoji} Performance Alert Triggered

Alert ID: {alert['id']}
Severity: {alert['severity'].upper()}
Metric: {alert['metric']}
Current Value: {alert['current_value']}
Threshold: {alert.get('threshold', 'N/A')}
Time: {alert['timestamp']}

Details:
{json.dumps(alert['metadata'], indent=2) if alert['metadata'] else 'No additional details'}

Dashboard: {settings.SITE_URL}/dashboard/

This is an automated alert from your performance monitoring system.
"""
        return message.strip()

    def _send_console_notification(self, alert):
        """
        Send console notification (for development)
        """
        severity_color = {
            "critical": "\033[91m",  # Red
            "warning": "\033[93m",  # Yellow
            "info": "\033[94m",  # Blue
        }
        reset_color = "\033[0m"

        color = severity_color.get(alert["severity"], "")

        message = f"""
{color}🚨 PERFORMANCE ALERT {reset_color}
Severity: {alert['severity'].upper()}
Metric: {alert['metric']}
Value: {alert['current_value']} (threshold: {alert.get('threshold', 'N/A')})
Time: {alert['timestamp']}
"""

        print(message)
        logger.warning(message.replace(color, "").replace(reset_color, ""))

    def _send_cache_notification(self, alert):
        """
        Store alert in cache for dashboard display
        """
        # Store individual alert
        cache_key = f"alert_{alert['id']}"
        cache.set(cache_key, alert, 3600)  # 1 hour

        # Add to alerts list
        alerts_key = "performance_alerts"
        alerts = cache.get(alerts_key, [])
        alerts.append(alert)

        # Keep only last 100 alerts
        if len(alerts) > 100:
            alerts = alerts[-100:]

        cache.set(alerts_key, alerts, 3600)

    def _store_alert(self, alert):
        """
        Store alert for persistence (could be database in production)
        """
        # For now, just log it
        logger.info(f"Alert stored: {json.dumps(alert, indent=2)}")

    def check_metric_thresholds(self, metric_type, value, baseline=None):
        """
        Check if a metric value exceeds alert thresholds
        """
        alerts_triggered = []

        try:
            # Define metric-specific thresholds
            thresholds = {
                "lcp": 2500,  # milliseconds
                "fid": 100,  # milliseconds
                "cls": 0.1,  # score
                "fcp": 1800,  # milliseconds
                "ttfb": 600,  # milliseconds
                "resource_load": 3000,  # milliseconds
                "long_task": 50,  # milliseconds
                "memory_usage": 0.85,  # percentage
            }

            threshold = thresholds.get(metric_type)
            if not threshold:
                return alerts_triggered

            # Check warning threshold (1.5x normal)
            if value > threshold * 1.5:
                if self.create_alert(
                    "performance_degradation", metric_type, value, threshold * 1.5
                ):
                    alerts_triggered.append("performance_degradation")

            # Check critical threshold (2x normal)
            if value > threshold * 2:
                if self.create_alert(
                    "critical_performance", metric_type, value, threshold * 2
                ):
                    alerts_triggered.append("critical_performance")

            return alerts_triggered

        except Exception as e:
            logger.error(f"Failed to check thresholds for {metric_type}: {e}")
            return alerts_triggered

    def get_active_alerts(self, severity=None):
        """
        Get currently active alerts
        """
        try:
            alerts = cache.get("performance_alerts", [])

            if severity:
                alerts = [alert for alert in alerts if alert["severity"] == severity]

            # Filter active alerts (last 24 hours)
            cutoff_time = datetime.now() - timedelta(hours=24)
            active_alerts = []

            for alert in alerts:
                alert_time = datetime.fromisoformat(alert["timestamp"])
                if alert_time > cutoff_time and alert["status"] == "active":
                    active_alerts.append(alert)

            return active_alerts

        except Exception as e:
            logger.error(f"Failed to get active alerts: {e}")
            return []

    def resolve_alert(self, alert_id):
        """
        Mark an alert as resolved
        """
        try:
            alerts = cache.get("performance_alerts", [])

            for alert in alerts:
                if alert["id"] == alert_id:
                    alert["status"] = "resolved"
                    alert["resolved_at"] = datetime.now().isoformat()
                    break

            cache.set("performance_alerts", alerts, 3600)
            logger.info(f"Alert {alert_id} resolved")
            return True

        except Exception as e:
            logger.error(f"Failed to resolve alert {alert_id}: {e}")
            return False

    def get_alert_summary(self):
        """
        Get summary of alerts by severity
        """
        try:
            active_alerts = self.get_active_alerts()

            summary = {
                "total": len(active_alerts),
                "critical": len(
                    [a for a in active_alerts if a["severity"] == "critical"]
                ),
                "warning": len(
                    [a for a in active_alerts if a["severity"] == "warning"]
                ),
                "info": len([a for a in active_alerts if a["severity"] == "info"]),
            }

            return summary

        except Exception as e:
            logger.error(f"Failed to get alert summary: {e}")
            return {"total": 0, "critical": 0, "warning": 0, "info": 0}


# Global alert manager instance
alert_manager = AlertManager()
