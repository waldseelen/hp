"""
Log-Based Alerting System
========================

Advanced alerting system for log analysis with multiple notification channels,
alert rules, and escalation policies.
"""

import logging
import threading
from collections import deque
from dataclasses import asdict, dataclass
from datetime import datetime, timedelta
from enum import Enum
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class AlertSeverity(Enum):
    """Alert severity levels"""

    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class AlertStatus(Enum):
    """Alert status"""

    ACTIVE = "active"
    ACKNOWLEDGED = "acknowledged"
    RESOLVED = "resolved"
    SUPPRESSED = "suppressed"


@dataclass
class AlertRule:
    """Alert rule configuration"""

    name: str
    description: str
    condition: str  # Log pattern or condition
    severity: AlertSeverity
    threshold: int  # Number of occurrences
    time_window: int  # Time window in seconds
    cooldown: int  # Cooldown period in seconds
    enabled: bool = True
    tags: Optional[Dict[str, str]] = None
    notification_channels: Optional[List[str]] = None


@dataclass
class Alert:
    """Alert instance"""

    id: str
    rule_name: str
    severity: AlertSeverity
    status: AlertStatus
    message: str
    description: str
    first_seen: datetime
    last_seen: datetime
    count: int
    details: Dict[str, Any]
    tags: Dict[str, str]
    acknowledged_by: Optional[str] = None
    acknowledged_at: Optional[datetime] = None
    resolved_at: Optional[datetime] = None


class NotificationChannel:
    """Base notification channel"""

    def __init__(self, name: str, config: Dict[str, Any]):
        self.name = name
        self.config = config

    def send(self, alert: Alert) -> bool:
        """Send alert notification"""
        raise NotImplementedError


class EmailNotificationChannel(NotificationChannel):
    """Email notification channel"""

    def send(self, alert: Alert) -> bool:
        try:
            subject = f"[{alert.severity.value.upper()}] {alert.message}"

            # Render email template
            site_url = getattr(settings, "SITE_URL", "http://localhost:8000")
            email_body = (
                render_to_string(
                    "pages/portfolio/alerts/email_alert.html",
                    {
                        "alert": alert,
                        "alert_url": f"{site_url}/admin/logging/dashboard/",
                    },
                )
                if hasattr(render_to_string, "__call__")
                else f"""
Alert: {alert.message}
Severity: {alert.severity.value.upper()}
Rule: {alert.rule_name}
Count: {alert.count}
First Seen: {alert.first_seen}
Description: {alert.description}

View Dashboard: {site_url}/admin/logging/dashboard/
"""
            )

            recipients = self.config.get("recipients", [])
            if not recipients:
                recipients = getattr(
                    settings, "ADMIN_EMAIL_LIST", ["admin@example.com"]
                )

            send_mail(
                subject=subject,
                message=email_body,
                html_message=email_body,
                from_email=getattr(
                    settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
                ),
                recipient_list=recipients,
                fail_silently=False,
            )

            logger.info(
                f"Alert email sent for {alert.rule_name} to {len(recipients)} recipients"
            )
            return True

        except Exception as e:
            logger.error(f"Failed to send email alert: {e}")
            return False


class SlackNotificationChannel(NotificationChannel):
    """Slack notification channel"""

    def send(self, alert: Alert) -> bool:
        try:
            import requests

            webhook_url = self.config.get("webhook_url")
            if not webhook_url:
                logger.warning("Slack webhook URL not configured")
                return False

            # Color coding based on severity
            color_map = {
                AlertSeverity.LOW: "#36a64f",
                AlertSeverity.MEDIUM: "#ff9500",
                AlertSeverity.HIGH: "#ff4500",
                AlertSeverity.CRITICAL: "#ff0000",
            }

            payload = {
                "text": f"Alert: {alert.message}",
                "attachments": [
                    {
                        "color": color_map.get(alert.severity, "#808080"),
                        "fields": [
                            {
                                "title": "Severity",
                                "value": alert.severity.value.upper(),
                                "short": True,
                            },
                            {"title": "Rule", "value": alert.rule_name, "short": True},
                            {
                                "title": "Count",
                                "value": str(alert.count),
                                "short": True,
                            },
                            {
                                "title": "First Seen",
                                "value": alert.first_seen.strftime("%Y-%m-%d %H:%M:%S"),
                                "short": True,
                            },
                        ],
                        "footer": "Log Alert System",
                        "ts": int(alert.first_seen.timestamp()),
                    }
                ],
            }

            response = requests.post(webhook_url, json=payload, timeout=10)
            response.raise_for_status()

            logger.info(f"Alert sent to Slack for {alert.rule_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send Slack alert: {e}")
            return False


class WebhookNotificationChannel(NotificationChannel):
    """Generic webhook notification channel"""

    def send(self, alert: Alert) -> bool:
        try:
            import requests

            webhook_url = self.config.get("url")
            if not webhook_url:
                logger.warning("Webhook URL not configured")
                return False

            payload = {
                "alert": {
                    "id": alert.id,
                    "rule_name": alert.rule_name,
                    "severity": alert.severity.value,
                    "status": alert.status.value,
                    "message": alert.message,
                    "description": alert.description,
                    "first_seen": alert.first_seen.isoformat(),
                    "last_seen": alert.last_seen.isoformat(),
                    "count": alert.count,
                    "details": alert.details,
                    "tags": alert.tags,
                }
            }

            headers = self.config.get("headers", {})
            headers.setdefault("Content-Type", "application/json")

            response = requests.post(
                webhook_url, json=payload, headers=headers, timeout=10
            )
            response.raise_for_status()

            logger.info(f"Alert sent to webhook {webhook_url} for {alert.rule_name}")
            return True

        except Exception as e:
            logger.error(f"Failed to send webhook alert: {e}")
            return False


class LogAlertSystem:
    """
    Centralized log-based alerting system
    """

    def __init__(self):
        self.alert_rules = {}
        self.active_alerts = {}
        self.notification_channels = {}
        self.alert_history = deque(maxlen=1000)
        self._lock = threading.Lock()

        # Initialize default rules and channels
        self._initialize_default_rules()
        self._initialize_notification_channels()

    def _initialize_default_rules(self):
        """Initialize default alert rules"""
        default_rules = [
            AlertRule(
                name="high_error_rate",
                description="High error rate detected",
                condition="level:ERROR",
                severity=AlertSeverity.HIGH,
                threshold=10,
                time_window=300,  # 5 minutes
                cooldown=900,  # 15 minutes
                notification_channels=["email", "slack"],
            ),
            AlertRule(
                name="critical_errors",
                description="Critical errors detected",
                condition="level:CRITICAL",
                severity=AlertSeverity.CRITICAL,
                threshold=1,
                time_window=60,  # 1 minute
                cooldown=300,  # 5 minutes
                notification_channels=["email", "slack", "webhook"],
            ),
            AlertRule(
                name="authentication_failures",
                description="Multiple authentication failures",
                condition="message:*authentication*failed* OR message:*login*failed*",
                severity=AlertSeverity.MEDIUM,
                threshold=5,
                time_window=300,  # 5 minutes
                cooldown=600,  # 10 minutes
                notification_channels=["email"],
            ),
            AlertRule(
                name="performance_degradation",
                description="Performance degradation detected",
                condition="performance.response_time:>5000",
                severity=AlertSeverity.MEDIUM,
                threshold=3,
                time_window=180,  # 3 minutes
                cooldown=600,  # 10 minutes
                notification_channels=["email"],
            ),
            AlertRule(
                name="security_events",
                description="Security-related events detected",
                condition="security.event_type:* OR message:*unauthorized* OR message:*forbidden*",
                severity=AlertSeverity.HIGH,
                threshold=3,
                time_window=300,  # 5 minutes
                cooldown=1800,  # 30 minutes
                notification_channels=["email", "slack"],
            ),
            AlertRule(
                name="database_errors",
                description="Database connection or query errors",
                condition="message:*database* OR message:*connection*refused* OR message:*timeout*",
                severity=AlertSeverity.HIGH,
                threshold=5,
                time_window=300,  # 5 minutes
                cooldown=600,  # 10 minutes
                notification_channels=["email", "slack"],
            ),
        ]

        for rule in default_rules:
            self.alert_rules[rule.name] = rule

    def _initialize_notification_channels(self):
        """Initialize notification channels"""
        # Email channel
        email_config = getattr(settings, "ALERT_EMAIL_CONFIG", {})
        self.notification_channels["email"] = EmailNotificationChannel(
            "email", email_config
        )

        # Slack channel
        slack_config = getattr(settings, "ALERT_SLACK_CONFIG", {})
        if slack_config.get("webhook_url"):
            self.notification_channels["slack"] = SlackNotificationChannel(
                "slack", slack_config
            )

        # Webhook channel
        webhook_config = getattr(settings, "ALERT_WEBHOOK_CONFIG", {})
        if webhook_config.get("url"):
            self.notification_channels["webhook"] = WebhookNotificationChannel(
                "webhook", webhook_config
            )

    def add_alert_rule(self, rule: AlertRule):
        """Add or update an alert rule"""
        with self._lock:
            self.alert_rules[rule.name] = rule
            logger.info(f"Alert rule added/updated: {rule.name}")

    def remove_alert_rule(self, rule_name: str):
        """Remove an alert rule"""
        with self._lock:
            if rule_name in self.alert_rules:
                del self.alert_rules[rule_name]
                logger.info(f"Alert rule removed: {rule_name}")

    def check_log_entry(self, log_entry: Dict[str, Any]):
        """Check a single log entry against all alert rules"""
        current_time = timezone.now()

        for rule_name, rule in self.alert_rules.items():
            if not rule.enabled:
                continue

            if self._matches_condition(log_entry, rule.condition):
                self._process_alert_match(rule, log_entry, current_time)

    def _matches_condition(
        self, log_entry: Dict[str, Any], condition: str
    ) -> bool:  # noqa: C901
        """Check if log entry matches alert condition"""
        try:
            # Simple condition matching - can be extended with more complex logic
            conditions = condition.split(" OR ")

            for cond in conditions:
                cond = cond.strip()

                if ":" in cond:
                    field, value = cond.split(":", 1)
                    field = field.strip()
                    value = value.strip()

                    # Handle wildcards
                    if "*" in value:
                        pattern = value.replace("*", ".*")
                        import re

                        if re.search(
                            pattern, str(log_entry.get(field, "")), re.IGNORECASE
                        ):
                            return True
                    else:
                        # Exact match or numeric comparison
                        if value.startswith(">"):
                            try:
                                threshold = float(value[1:])
                                log_value = float(log_entry.get(field, 0))
                                if log_value > threshold:
                                    return True
                            except ValueError:
                                pass
                        elif value.startswith("<"):
                            try:
                                threshold = float(value[1:])
                                log_value = float(log_entry.get(field, 0))
                                if log_value < threshold:
                                    return True
                            except ValueError:
                                pass
                        else:
                            if str(log_entry.get(field, "")).lower() == value.lower():
                                return True
                else:
                    # Simple text search in message
                    message = log_entry.get("message", "").lower()
                    if cond.lower() in message:
                        return True

            return False

        except Exception as e:
            logger.error(f"Error matching condition '{condition}': {e}")
            return False

    def _process_alert_match(
        self, rule: AlertRule, log_entry: Dict[str, Any], current_time: datetime
    ):
        """Process an alert rule match"""
        alert_id = f"{rule.name}_{current_time.strftime('%Y%m%d_%H')}"  # Hourly buckets

        with self._lock:
            if alert_id in self.active_alerts:
                # Update existing alert
                alert = self.active_alerts[alert_id]
                alert.count += 1
                alert.last_seen = current_time
                alert.details.setdefault("recent_entries", []).append(
                    {
                        "timestamp": current_time.isoformat(),
                        "message": log_entry.get("message", ""),
                        "logger": log_entry.get("logger", ""),
                    }
                )
                # Keep only last 10 entries
                alert.details["recent_entries"] = alert.details["recent_entries"][-10:]
            else:
                # Create new alert
                alert = Alert(
                    id=alert_id,
                    rule_name=rule.name,
                    severity=rule.severity,
                    status=AlertStatus.ACTIVE,
                    message=f"{rule.description}",
                    description=f"Alert triggered by rule: {rule.name}",
                    first_seen=current_time,
                    last_seen=current_time,
                    count=1,
                    details={
                        "rule": asdict(rule),
                        "first_entry": log_entry,
                        "recent_entries": [
                            {
                                "timestamp": current_time.isoformat(),
                                "message": log_entry.get("message", ""),
                                "logger": log_entry.get("logger", ""),
                            }
                        ],
                    },
                    tags=rule.tags or {},
                )
                self.active_alerts[alert_id] = alert

            # Check if alert should be fired
            if alert.count >= rule.threshold:
                self._fire_alert(alert, rule)

    def _fire_alert(self, alert: Alert, rule: AlertRule):
        """Fire an alert if not in cooldown"""
        cooldown_key = f"alert_cooldown_{rule.name}"
        last_fired = cache.get(cooldown_key)

        current_time = timezone.now()
        if last_fired:
            last_fired_dt = datetime.fromisoformat(last_fired)
            if (current_time - last_fired_dt).total_seconds() < rule.cooldown:
                logger.debug(f"Alert {rule.name} in cooldown, skipping")
                return

        # Set cooldown
        cache.set(cooldown_key, current_time.isoformat(), rule.cooldown)

        # Send notifications
        channels = rule.notification_channels or ["email"]
        for channel_name in channels:
            if channel_name in self.notification_channels:
                try:
                    channel = self.notification_channels[channel_name]
                    success = channel.send(alert)
                    if success:
                        logger.info(f"Alert {alert.id} sent via {channel_name}")
                    else:
                        logger.warning(
                            f"Failed to send alert {alert.id} via {channel_name}"
                        )
                except Exception as e:
                    logger.error(f"Error sending alert via {channel_name}: {e}")

        # Add to history
        self.alert_history.append(alert)

        logger.warning(
            f"Alert fired: {alert.rule_name} - {alert.message}",
            extra={
                "alert_id": alert.id,
                "severity": alert.severity.value,
                "count": alert.count,
                "rule_name": alert.rule_name,
            },
        )

    def acknowledge_alert(self, alert_id: str, acknowledged_by: str) -> bool:
        """Acknowledge an alert"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.ACKNOWLEDGED
                alert.acknowledged_by = acknowledged_by
                alert.acknowledged_at = timezone.now()

                logger.info(f"Alert {alert_id} acknowledged by {acknowledged_by}")
                return True
            return False

    def resolve_alert(self, alert_id: str) -> bool:
        """Resolve an alert"""
        with self._lock:
            if alert_id in self.active_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = timezone.now()

                # Move to history and remove from active
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]

                logger.info(f"Alert {alert_id} resolved")
                return True
            return False

    def get_active_alerts(self) -> List[Alert]:
        """Get all active alerts"""
        with self._lock:
            return list(self.active_alerts.values())

    def get_alert_history(self, limit: int = 100) -> List[Alert]:
        """Get alert history"""
        return list(self.alert_history)[-limit:]

    def cleanup_old_alerts(self):
        """Clean up old alerts"""
        current_time = timezone.now()
        cutoff_time = current_time - timedelta(hours=24)

        with self._lock:
            # Remove old active alerts
            expired_alerts = []
            for alert_id, alert in self.active_alerts.items():
                if alert.last_seen < cutoff_time:
                    expired_alerts.append(alert_id)

            for alert_id in expired_alerts:
                alert = self.active_alerts[alert_id]
                alert.status = AlertStatus.RESOLVED
                alert.resolved_at = current_time
                self.alert_history.append(alert)
                del self.active_alerts[alert_id]

            if expired_alerts:
                logger.info(f"Cleaned up {len(expired_alerts)} expired alerts")


# Global alert system instance
log_alert_system = LogAlertSystem()
