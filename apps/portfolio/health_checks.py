"""
Comprehensive Health Check System
=================================

This module provides a complete health monitoring system for the Django portfolio website.
Includes 7 comprehensive checks covering all critical system components with proactive monitoring,
alerting capabilities, and uptime tracking.

Features:
- Database connectivity and performance monitoring
- Cache system health verification
- Disk space and memory usage monitoring
- External service dependency checks
- Application configuration validation
- Security configuration verification
- Custom service health checks
- Email alerting with cooldown periods
- Structured logging and history tracking
- Uptime statistics with daily history
"""

import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, Optional

import requests

try:
    import psutil

    PSUTIL_AVAILABLE = True
except ImportError:
    psutil = None
    PSUTIL_AVAILABLE = False

import json
import logging

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.db import connection
from django.utils import timezone

logger = logging.getLogger(__name__)


@dataclass
class HealthCheckResult:
    """Single health check result"""

    check_name: str
    status: str  # 'healthy', 'warning', 'critical', 'unknown'
    message: str
    details: Dict[str, Any] = field(default_factory=dict)
    response_time_ms: float = 0.0
    timestamp: datetime = field(default_factory=timezone.now)
    error: Optional[str] = None


@dataclass
class AlertConfig:
    """Alert configuration for health checks"""

    check_name: str
    enabled: bool = True
    email_enabled: bool = True
    cooldown_minutes: int = 30
    critical_threshold: int = 3  # Number of consecutive failures before alert
    warning_threshold: int = 2


class HealthCheckSystem:
    """
    Comprehensive health monitoring system
    """

    def __init__(self):
        self.checks_history = {}
        self.alert_cooldown = {}
        self.alert_threshold = 300  # 5 minutes cooldown

        # Initialize alert configurations for each check
        self.alert_configs = {
            "database": AlertConfig(
                "database", enabled=True, email_enabled=True, cooldown_minutes=30
            ),
            "cache": AlertConfig(
                "cache", enabled=True, email_enabled=True, cooldown_minutes=30
            ),
            "disk_space": AlertConfig(
                "disk_space", enabled=True, email_enabled=True, cooldown_minutes=60
            ),
            "memory": AlertConfig(
                "memory", enabled=True, email_enabled=True, cooldown_minutes=30
            ),
            "external_services": AlertConfig(
                "external_services",
                enabled=True,
                email_enabled=False,
                cooldown_minutes=15,
            ),
            "application": AlertConfig(
                "application", enabled=True, email_enabled=True, cooldown_minutes=30
            ),
            "security": AlertConfig(
                "security", enabled=True, email_enabled=True, cooldown_minutes=120
            ),
        }

    def _execute_single_check(self, check_name, check_method):
        """
        Execute a single health check and return result.

        Args:
            check_name: Name of the health check
            check_method: Callable method to execute

        Returns:
            Tuple of (check_result dict, error flag bool)
        """
        try:
            check_result = check_method()
            return (check_result, False)
        except Exception as e:
            logger.error(f"Health check {check_name} failed: {e}")
            error_result = {
                "status": "error",
                "message": f"Check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }
            return (error_result, True)

    def _update_check_summary(self, results, check_result):
        """
        Update summary counters based on check result.

        Args:
            results: Main results dict to update
            check_result: Individual check result dict
        """
        results["summary"]["total_checks"] += 1

        if check_result["status"] == "healthy":
            results["summary"]["passed"] += 1
        elif check_result["status"] == "warning":
            results["summary"]["warnings"] += 1
        else:
            results["summary"]["failed"] += 1
            results["overall_status"] = "unhealthy"

    def _determine_overall_status(self, summary):
        """
        Determine overall health status from summary.

        Args:
            summary: Dict with passed/failed/warnings counts

        Returns:
            Status string: 'healthy', 'warning', or 'unhealthy'
        """
        if summary["warnings"] > 0 and summary["failed"] == 0:
            return "warning"
        elif summary["failed"] > 0:
            return "unhealthy"
        return "healthy"

    def _get_check_registry(self):
        """
        Get list of all health checks to run.

        Returns:
            List of (name, method) tuples
        """
        return [
            ("database", self.check_database),
            ("cache", self.check_cache),
            ("disk_space", self.check_disk_space),
            ("memory", self.check_memory),
            ("external_services", self.check_external_services),
            ("application", self.check_application_health),
            ("security", self.check_security_status),
        ]

    def run_all_checks(self) -> Dict:
        """
        Run all health checks and return comprehensive status.

        Refactored to reduce complexity: C:16 → C:5
        Uses registry pattern with separate execution/summary methods.
        """
        results = {
            "timestamp": timezone.now().isoformat(),
            "overall_status": "healthy",
            "checks": {},
            "summary": {"total_checks": 0, "passed": 0, "failed": 0, "warnings": 0},
        }

        # Execute all registered checks
        check_methods = self._get_check_registry()

        for check_name, check_method in check_methods:
            check_result, had_error = self._execute_single_check(
                check_name, check_method
            )
            results["checks"][check_name] = check_result
            self._update_check_summary(results, check_result)

        # Determine final status
        results["overall_status"] = self._determine_overall_status(results["summary"])

        # Store and alert
        self._store_check_history(results)

        if results["overall_status"] in ["unhealthy", "warning"]:
            self._send_health_alerts(results)

        return results

    def check_database(self) -> Dict:
        """Check database connectivity and performance"""
        try:
            start_time = time.time()

            # Test default database connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                cursor.fetchone()

                # Test query performance
                cursor.execute("SELECT COUNT(*) FROM django_session")
                session_count = cursor.fetchone()[0]

            query_time = (time.time() - start_time) * 1000  # Convert to ms

            status = "healthy"
            issues = []

            if query_time > 100:  # More than 100ms
                status = "warning"
                issues.append(f"Slow query response: {query_time:.2f}ms")

            return {
                "status": status,
                "message": (
                    "Database connection healthy"
                    if status == "healthy"
                    else "Database has issues"
                ),
                "details": {
                    "query_time_ms": round(query_time, 2),
                    "session_count": session_count,
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Database connection failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def check_cache(self) -> Dict:
        """Check cache system health"""
        try:
            test_key = "health_check_test"
            test_value = f"test_{int(time.time())}"

            start_time = time.time()

            # Test cache write
            cache.set(test_key, test_value, 60)

            # Test cache read
            retrieved_value = cache.get(test_key)

            cache_time = (time.time() - start_time) * 1000

            # Clean up
            cache.delete(test_key)

            status = "healthy"
            issues = []

            if retrieved_value != test_value:
                status = "error"
                issues.append("Cache read/write failed")
            elif cache_time > 50:  # More than 50ms
                status = "warning"
                issues.append(f"Slow cache response: {cache_time:.2f}ms")

            return {
                "status": status,
                "message": (
                    "Cache system healthy"
                    if status == "healthy"
                    else "Cache has issues"
                ),
                "details": {
                    "response_time_ms": round(cache_time, 2),
                    "read_write_success": retrieved_value == test_value,
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Cache check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def check_disk_space(self) -> Dict:
        """Check disk space availability"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    "status": "warning",
                    "message": "Disk space check unavailable - psutil not installed",
                    "timestamp": timezone.now().isoformat(),
                }

            # Get disk usage for current directory
            disk_usage = psutil.disk_usage(".")

            total_gb = disk_usage.total / (1024**3)
            free_gb = disk_usage.free / (1024**3)
            used_gb = disk_usage.used / (1024**3)
            free_percent = (disk_usage.free / disk_usage.total) * 100

            status = "healthy"
            issues = []

            if free_percent < 5:  # Less than 5% free
                status = "error"
                issues.append(f"Critical disk space: {free_percent:.1f}% free")
            elif free_percent < 15:  # Less than 15% free
                status = "warning"
                issues.append(f"Low disk space: {free_percent:.1f}% free")

            return {
                "status": status,
                "message": (
                    "Disk space healthy" if status == "healthy" else "Disk space issues"
                ),
                "details": {
                    "total_gb": round(total_gb, 2),
                    "used_gb": round(used_gb, 2),
                    "free_gb": round(free_gb, 2),
                    "free_percent": round(free_percent, 1),
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Disk space check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def check_memory(self) -> Dict:
        """Check memory usage"""
        try:
            if not PSUTIL_AVAILABLE:
                return {
                    "status": "warning",
                    "message": "Memory check unavailable - psutil not installed",
                    "timestamp": timezone.now().isoformat(),
                }

            memory = psutil.virtual_memory()

            total_gb = memory.total / (1024**3)
            available_gb = memory.available / (1024**3)
            used_percent = memory.percent

            status = "healthy"
            issues = []

            if used_percent > 90:  # More than 90% used
                status = "error"
                issues.append(f"Critical memory usage: {used_percent:.1f}%")
            elif used_percent > 80:  # More than 80% used
                status = "warning"
                issues.append(f"High memory usage: {used_percent:.1f}%")

            return {
                "status": status,
                "message": (
                    "Memory usage healthy"
                    if status == "healthy"
                    else "Memory usage issues"
                ),
                "details": {
                    "total_gb": round(total_gb, 2),
                    "available_gb": round(available_gb, 2),
                    "used_percent": round(used_percent, 1),
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Memory check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def check_external_services(self) -> Dict:
        """Check external service dependencies"""
        services_to_check = [
            ("Google Fonts", "https://fonts.googleapis.com"),
            ("CDN Services", "https://cdn.jsdelivr.net"),
        ]

        results = []
        overall_status = "healthy"

        for service_name, url in services_to_check:
            try:
                start_time = time.time()
                response = requests.get(url, timeout=5)
                response_time = (time.time() - start_time) * 1000

                if response.status_code == 200:
                    status = "healthy" if response_time < 2000 else "warning"
                else:
                    status = "warning"
                    overall_status = "warning"

                results.append(
                    {
                        "service": service_name,
                        "url": url,
                        "status": status,
                        "response_time_ms": round(response_time, 2),
                        "status_code": response.status_code,
                    }
                )

            except Exception as e:
                results.append(
                    {
                        "service": service_name,
                        "url": url,
                        "status": "error",
                        "error": str(e),
                    }
                )
                overall_status = "warning"  # External services failing shouldn't mark system as unhealthy

        return {
            "status": overall_status,
            "message": "External services check completed",
            "details": {
                "services": results,
                "total_checked": len(services_to_check),
                "healthy_count": len(
                    [r for r in results if r.get("status") == "healthy"]
                ),
            },
            "timestamp": timezone.now().isoformat(),
        }

    def check_application_health(self) -> Dict:
        """Check application-specific health metrics"""
        try:
            issues = []
            status = "healthy"

            # Check if DEBUG is enabled in production
            if getattr(settings, "DEBUG", False):
                issues.append("DEBUG mode is enabled")
                status = "warning"

            # Check if secret key is default
            secret_key = getattr(settings, "SECRET_KEY", "")
            if not secret_key or len(secret_key) < 50:
                issues.append("Weak or missing SECRET_KEY")
                status = "warning"

            # Check allowed hosts
            allowed_hosts = getattr(settings, "ALLOWED_HOSTS", [])
            if "*" in allowed_hosts:
                issues.append("ALLOWED_HOSTS contains wildcard")
                status = "warning"

            # Check static files
            try:
                from django.contrib.staticfiles.storage import staticfiles_storage

                test_file = "css/custom.min.css"
                if staticfiles_storage.exists(test_file):
                    static_files_ok = True
                else:
                    static_files_ok = False
                    issues.append("Static files not collected")
                    status = "warning"
            except Exception:
                static_files_ok = False
                issues.append("Static files check failed")
                status = "warning"

            return {
                "status": status,
                "message": (
                    "Application healthy"
                    if status == "healthy"
                    else "Application has configuration issues"
                ),
                "details": {
                    "debug_mode": getattr(settings, "DEBUG", False),
                    "secret_key_length": len(secret_key),
                    "allowed_hosts_count": len(allowed_hosts),
                    "static_files_ok": static_files_ok,
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Application health check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def check_security_status(self) -> Dict:
        """Check security configuration"""
        try:
            issues = []
            status = "healthy"

            # Check HTTPS settings
            if not getattr(settings, "SECURE_SSL_REDIRECT", False):
                issues.append("SECURE_SSL_REDIRECT not enabled")
                status = "warning"

            if not getattr(settings, "SECURE_HSTS_SECONDS", 0):
                issues.append("HSTS not configured")
                status = "warning"

            # Check cookie security
            if not getattr(settings, "SESSION_COOKIE_SECURE", False):
                issues.append("Session cookies not secure")
                status = "warning"

            if not getattr(settings, "CSRF_COOKIE_SECURE", False):
                issues.append("CSRF cookies not secure")
                status = "warning"

            return {
                "status": status,
                "message": (
                    "Security configuration healthy"
                    if status == "healthy"
                    else "Security configuration has issues"
                ),
                "details": {
                    "ssl_redirect": getattr(settings, "SECURE_SSL_REDIRECT", False),
                    "hsts_seconds": getattr(settings, "SECURE_HSTS_SECONDS", 0),
                    "secure_cookies": getattr(settings, "SESSION_COOKIE_SECURE", False),
                    "csrf_secure": getattr(settings, "CSRF_COOKIE_SECURE", False),
                    "issues": issues,
                },
                "timestamp": timezone.now().isoformat(),
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Security check failed: {str(e)}",
                "timestamp": timezone.now().isoformat(),
            }

    def _store_check_history(self, results: Dict):
        """Store check results in cache for history tracking"""
        try:
            history_key = f"health_check_history_{datetime.now().strftime('%Y%m%d')}"

            # Get existing history
            daily_history = cache.get(history_key, [])

            # Add new result
            daily_history.append(
                {
                    "timestamp": results["timestamp"],
                    "overall_status": results["overall_status"],
                    "summary": results["summary"],
                }
            )

            # Keep only last 24 hours (assuming checks every 5 minutes = 288 checks/day)
            if len(daily_history) > 288:
                daily_history = daily_history[-288:]

            # Store back in cache
            cache.set(history_key, daily_history, 86400)  # 24 hours

        except Exception as e:
            logger.error(f"Failed to store health check history: {e}")

    def _send_health_alerts(self, results: Dict):  # noqa: C901
        """Send alerts for health issues"""
        try:
            current_time = time.time()
            alert_key = f"health_alert_{results['overall_status']}"

            # Check cooldown
            if alert_key in self.alert_cooldown:
                if current_time - self.alert_cooldown[alert_key] < self.alert_threshold:
                    return  # Still in cooldown

            # Update cooldown
            self.alert_cooldown[alert_key] = current_time

            # Prepare alert message
            failed_checks = []
            warning_checks = []

            for check_name, check_result in results["checks"].items():
                if check_result["status"] == "error":
                    failed_checks.append(
                        f"FAIL {check_name}: {check_result.get('message', 'Failed')}"
                    )
                elif check_result["status"] == "warning":
                    warning_checks.append(
                        f"WARN {check_name}: {check_result.get('message', 'Warning')}"
                    )

            alert_message = f"""
Health Check Alert - {results['overall_status'].upper()}

Timestamp: {results['timestamp']}

Summary:
- Total Checks: {results['summary']['total_checks']}
- Passed: {results['summary']['passed']}
- Warnings: {results['summary']['warnings']}
- Failed: {results['summary']['failed']}

Failed Checks:
{chr(10).join(failed_checks) if failed_checks else 'None'}

Warning Checks:
{chr(10).join(warning_checks) if warning_checks else 'None'}
            """

            logger.warning(f"Health Check Alert: {alert_message}")

            # Send email if configured
            if hasattr(settings, "HEALTH_CHECK_EMAIL"):
                try:
                    send_mail(
                        subject=f'Health Check Alert - {results["overall_status"].upper()}',
                        message=alert_message,
                        from_email=settings.DEFAULT_FROM_EMAIL,
                        recipient_list=[settings.HEALTH_CHECK_EMAIL],
                        fail_silently=True,
                    )
                except Exception:
                    pass  # Don't fail health checks if email fails

        except Exception as e:
            logger.error(f"Failed to send health alert: {e}")

    def send_alert(
        self, check_name: str, status: str, message: str, details: Dict = None
    ) -> bool:
        """
        Public method to send custom alerts for specific health checks

        Args:
            check_name: Name of the health check
            status: Status (healthy, warning, error)
            message: Alert message
            details: Optional additional details

        Returns:
            bool: True if alert sent successfully, False otherwise
        """
        try:
            # Check if alerts are enabled for this check
            alert_config = self.alert_configs.get(check_name)
            if not alert_config or not alert_config.enabled:
                return False

            current_time = time.time()
            alert_key = f"custom_alert_{check_name}_{status}"

            # Check cooldown
            cooldown_seconds = alert_config.cooldown_minutes * 60
            if alert_key in self.alert_cooldown:
                if current_time - self.alert_cooldown[alert_key] < cooldown_seconds:
                    return False  # Still in cooldown

            # Update cooldown
            self.alert_cooldown[alert_key] = current_time

            # Prepare alert message
            alert_message = f"""
Custom Health Check Alert - {status.upper()}

Check: {check_name}
Status: {status}
Message: {message}
Timestamp: {timezone.now().isoformat()}

Details: {json.dumps(details, indent=2) if details else 'None'}
            """

            # Log the alert
            logger.warning(f"Custom Health Alert [{check_name}]: {alert_message}")

            # Console output
            print(f"CUSTOM ALERT [{check_name}]: {message}")

            # Send email if enabled for this check
            if (
                alert_config.email_enabled
                and hasattr(settings, "EMAIL_HOST")
                and settings.EMAIL_HOST
            ):
                try:
                    send_mail(
                        subject=f"Custom Health Alert - {check_name} - {status.upper()}",
                        message=alert_message,
                        from_email=getattr(
                            settings, "DEFAULT_FROM_EMAIL", "noreply@example.com"
                        ),
                        recipient_list=getattr(
                            settings, "ADMIN_EMAIL_LIST", ["admin@example.com"]
                        ),
                        fail_silently=False,
                    )
                except Exception as e:
                    logger.error(f"Failed to send custom email alert: {e}")

            return True

        except Exception as e:
            logger.error(f"Failed to send custom alert for {check_name}: {e}")
            return False

    def get_uptime_stats(self) -> Dict:
        """Get uptime statistics"""
        try:
            # Get today's history
            today_key = f"health_check_history_{datetime.now().strftime('%Y%m%d')}"
            today_history = cache.get(today_key, [])

            if not today_history:
                return {"status": "no_data", "message": "No uptime data available"}

            total_checks = len(today_history)
            healthy_checks = len(
                [h for h in today_history if h["overall_status"] == "healthy"]
            )
            warning_checks = len(
                [h for h in today_history if h["overall_status"] == "warning"]
            )
            unhealthy_checks = len(
                [h for h in today_history if h["overall_status"] == "unhealthy"]
            )

            uptime_percentage = (
                (healthy_checks / total_checks * 100) if total_checks > 0 else 0
            )

            return {
                "status": "healthy",
                "uptime_percentage": round(uptime_percentage, 2),
                "total_checks_today": total_checks,
                "healthy_checks": healthy_checks,
                "warning_checks": warning_checks,
                "unhealthy_checks": unhealthy_checks,
                "last_check": today_history[-1]["timestamp"] if today_history else None,
            }

        except Exception as e:
            return {
                "status": "error",
                "message": f"Failed to get uptime stats: {str(e)}",
            }


# Global health check instance
health_checker = HealthCheckSystem()
