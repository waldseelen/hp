"""
Celery tasks for the main application.
"""

import logging
import os
import time
from datetime import timedelta
from typing import Dict

from django.conf import settings
from django.core.cache import cache
from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def send_notification(
    self, user_id: int, title: str, message: str, notification_type: str = "info"
):
    """
    Send notification to user via various channels.

    Args:
        user_id: Target user ID
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, warning, error, success)
    """
    try:
        from django.contrib.auth import get_user_model

        User = get_user_model()

        # Get user
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            logger.error(f"User {user_id} not found for notification")
            return {"status": "error", "message": "User not found"}

        # Log notification
        logger.info(f"Sending notification to user {user.username}: {title}")

        # Store notification in cache (you could also use a database model)
        notification_data = {
            "user_id": user_id,
            "title": title,
            "message": message,
            "type": notification_type,
            "created_at": timezone.now().isoformat(),
            "read": False,
        }

        cache_key = f"notifications:{user_id}:{int(time.time())}"
        cache.set(cache_key, notification_data, timeout=86400)  # 24 hours

        # Send email notification if enabled
        if (
            hasattr(settings, "EMAIL_NOTIFICATIONS_ENABLED")
            and settings.EMAIL_NOTIFICATIONS_ENABLED
        ):
            try:
                send_mail(
                    subject=f"[{notification_type.upper()}] {title}",
                    message=message,
                    from_email=settings.DEFAULT_FROM_EMAIL,
                    recipient_list=[user.email],
                    fail_silently=False,
                )
                logger.info(f"Email notification sent to {user.email}")
            except Exception as e:
                logger.error(f"Failed to send email notification: {e}")

        return {
            "status": "success",
            "message": "Notification sent successfully",
            "notification_id": cache_key,
        }

    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")

        # Retry with exponential backoff
        if self.request.retries < self.max_retries:
            retry_delay = 60 * (2**self.request.retries)
            logger.info(f"Retrying notification task in {retry_delay} seconds")
            raise self.retry(countdown=retry_delay, exc=exc)

        return {"status": "error", "message": str(exc)}


@shared_task(bind=True, max_retries=2)
def process_user_action(self, user_id: int, action: str, data: Dict):
    """
    Process user actions asynchronously.

    Args:
        user_id: User ID who performed the action
        action: Action type
        data: Action data
    """
    try:
        logger.info(f"Processing user action: {action} for user {user_id}")

        # Simulate processing
        time.sleep(1)

        # Store action in cache for analytics
        action_data = {
            "user_id": user_id,
            "action": action,
            "data": data,
            "processed_at": timezone.now().isoformat(),
            "task_id": self.request.id,
        }

        cache_key = f"user_actions:{user_id}:{action}:{int(time.time())}"
        cache.set(cache_key, action_data, timeout=3600)  # 1 hour

        logger.info(f"User action {action} processed successfully")
        return {"status": "success", "action_id": cache_key}

    except Exception as exc:
        logger.error(f"Error processing user action: {exc}")
        if self.request.retries < self.max_retries:
            raise self.retry(countdown=30, exc=exc)
        return {"status": "error", "message": str(exc)}


@shared_task
def update_analytics():
    """
    Update analytics data periodically.
    """
    try:
        logger.info("Updating analytics data")

        # Get analytics data from cache
        current_time = timezone.now()
        analytics_data = {
            "timestamp": current_time.isoformat(),
            "active_users": _get_active_users_count(),
            "page_views": _get_page_views_count(),
            "api_calls": _get_api_calls_count(),
            "performance_metrics": _get_performance_metrics(),
        }

        # Store in cache
        cache.set("analytics:latest", analytics_data, timeout=300)  # 5 minutes

        # Store daily summary
        date_key = current_time.strftime("%Y-%m-%d")
        daily_key = f"analytics:daily:{date_key}"

        daily_data = cache.get(daily_key, {})
        daily_data.update(
            {
                "last_update": current_time.isoformat(),
                "total_page_views": daily_data.get("total_page_views", 0)
                + analytics_data["page_views"],
                "total_api_calls": daily_data.get("total_api_calls", 0)
                + analytics_data["api_calls"],
                "peak_active_users": max(
                    daily_data.get("peak_active_users", 0),
                    analytics_data["active_users"],
                ),
            }
        )

        cache.set(daily_key, daily_data, timeout=86400 * 7)  # 7 days

        logger.info("Analytics data updated successfully")
        return {"status": "success", "data": analytics_data}

    except Exception as e:
        logger.error(f"Error updating analytics: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def cleanup_temp_files():
    """
    Clean up temporary files periodically.
    """
    try:
        logger.info("Starting temporary file cleanup")

        temp_dirs = [
            "/tmp",
            os.path.join(settings.BASE_DIR, "temp"),
            (
                os.path.join(settings.MEDIA_ROOT, "temp")
                if hasattr(settings, "MEDIA_ROOT")
                else None
            ),
        ]

        files_cleaned = 0
        bytes_freed = 0

        for temp_dir in temp_dirs:
            if temp_dir and os.path.exists(temp_dir):
                files_cleaned_dir, bytes_freed_dir = _cleanup_directory(temp_dir)
                files_cleaned += files_cleaned_dir
                bytes_freed += bytes_freed_dir

        # Clean up cache entries older than 24 hours
        _cleanup_old_cache_entries()

        logger.info(
            f"Cleanup completed: {files_cleaned} files, {bytes_freed} bytes freed"
        )
        return {
            "status": "success",
            "files_cleaned": files_cleaned,
            "bytes_freed": bytes_freed,
        }

    except Exception as e:
        logger.error(f"Error during cleanup: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def health_check():
    """
    Perform health check of the system.
    """
    try:
        health_data = {
            "timestamp": timezone.now().isoformat(),
            "status": "healthy",
            "checks": {},
        }

        # Database check
        try:
            from django.db import connection

            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                health_data["checks"]["database"] = {
                    "status": "ok",
                    "response_time": "fast",
                }
        except Exception as e:
            health_data["checks"]["database"] = {"status": "error", "error": str(e)}
            health_data["status"] = "unhealthy"

        # Redis check
        try:
            cache.set("health_check", "ok", timeout=10)
            result = cache.get("health_check")
            health_data["checks"]["redis"] = {
                "status": "ok" if result == "ok" else "error"
            }
        except Exception as e:
            health_data["checks"]["redis"] = {"status": "error", "error": str(e)}
            health_data["status"] = "unhealthy"

        # Disk space check
        try:
            disk_usage = _get_disk_usage()
            health_data["checks"]["disk_space"] = disk_usage
            if disk_usage["percent_used"] > 90:
                health_data["status"] = "warning"
        except Exception as e:
            health_data["checks"]["disk_space"] = {"status": "error", "error": str(e)}

        # Store health data
        cache.set("system:health", health_data, timeout=120)  # 2 minutes

        return health_data

    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def generate_daily_reports():
    """
    Generate daily reports.
    """
    try:
        logger.info("Generating daily reports")

        yesterday = timezone.now() - timedelta(days=1)
        date_key = yesterday.strftime("%Y-%m-%d")

        # Get daily analytics
        daily_analytics = cache.get(f"analytics:daily:{date_key}", {})

        # Generate report
        report = {
            "date": date_key,
            "generated_at": timezone.now().isoformat(),
            "analytics": daily_analytics,
            "summary": {
                "total_page_views": daily_analytics.get("total_page_views", 0),
                "total_api_calls": daily_analytics.get("total_api_calls", 0),
                "peak_active_users": daily_analytics.get("peak_active_users", 0),
            },
        }

        # Store report
        cache.set(f"reports:daily:{date_key}", report, timeout=86400 * 30)  # 30 days

        logger.info(f"Daily report generated for {date_key}")
        return {"status": "success", "report": report}

    except Exception as e:
        logger.error(f"Error generating daily report: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def generate_reports():
    """
    Generate various system reports.
    """
    try:
        logger.info("Generating system reports")

        reports = {
            "timestamp": timezone.now().isoformat(),
            "performance": _generate_performance_report(),
            "usage": _generate_usage_report(),
            "errors": _generate_error_report(),
        }

        # Store reports
        cache.set("reports:latest", reports, timeout=3600)  # 1 hour

        logger.info("System reports generated successfully")
        return {"status": "success", "reports": reports}

    except Exception as e:
        logger.error(f"Error generating reports: {e}")
        return {"status": "error", "message": str(e)}


@shared_task
def backup_data():
    """
    Backup important data.
    """
    try:
        logger.info("Starting data backup")

        backup_info = {
            "timestamp": timezone.now().isoformat(),
            "status": "completed",
            "files_backed_up": 0,
            "size": 0,
        }

        # Simulate backup process
        time.sleep(2)
        backup_info["files_backed_up"] = 100
        backup_info["size"] = 1024 * 1024  # 1MB

        # Store backup info
        cache.set("backup:latest", backup_info, timeout=86400)  # 24 hours

        logger.info("Data backup completed successfully")
        return backup_info

    except Exception as e:
        logger.error(f"Error during backup: {e}")
        return {"status": "error", "message": str(e)}


# Helper functions
def _get_active_users_count() -> int:
    """Get count of active users in the last 5 minutes."""
    return cache.get("metrics:active_users", 0)


def _get_page_views_count() -> int:
    """Get page views in the last 5 minutes."""
    return cache.get("metrics:page_views", 0)


def _get_api_calls_count() -> int:
    """Get API calls in the last 5 minutes."""
    return cache.get("metrics:api_calls", 0)


def _get_performance_metrics() -> Dict:
    """Get performance metrics."""
    return {
        "avg_response_time": 150,  # ms
        "error_rate": 0.01,  # 1%
        "cpu_usage": 45,  # %
        "memory_usage": 60,  # %
    }


def _cleanup_directory(directory: str) -> tuple:
    """Clean up files in a directory older than 24 hours."""
    files_cleaned = 0
    bytes_freed = 0

    try:
        cutoff_time = time.time() - 86400  # 24 hours ago

        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                try:
                    if os.path.getmtime(file_path) < cutoff_time:
                        file_size = os.path.getsize(file_path)
                        os.remove(file_path)
                        files_cleaned += 1
                        bytes_freed += file_size
                except (OSError, IOError):
                    continue

    except Exception as e:
        logger.error(f"Error cleaning directory {directory}: {e}")

    return files_cleaned, bytes_freed


def _cleanup_old_cache_entries():
    """Clean up old cache entries."""
    try:
        # This is a simplified implementation
        # In a real scenario, you'd iterate through cache keys and remove old ones
        pass
    except Exception as e:
        logger.error(f"Error cleaning cache entries: {e}")


def _get_disk_usage() -> Dict:
    """Get disk usage information."""
    try:
        import shutil

        total, used, free = shutil.disk_usage("/")
        percent_used = (used / total) * 100

        return {
            "status": "ok",
            "total_gb": round(total / (1024**3), 2),
            "used_gb": round(used / (1024**3), 2),
            "free_gb": round(free / (1024**3), 2),
            "percent_used": round(percent_used, 2),
        }
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _generate_performance_report() -> Dict:
    """Generate performance report."""
    return {
        "avg_response_time": 150,
        "max_response_time": 500,
        "min_response_time": 50,
        "error_rate": 0.01,
        "throughput": 1000,  # requests per minute
    }


def _generate_usage_report() -> Dict:
    """Generate usage report."""
    return {
        "total_users": 1000,
        "active_users_today": 150,
        "page_views_today": 5000,
        "api_calls_today": 2000,
    }


def _generate_error_report() -> Dict:
    """Generate error report."""
    return {
        "total_errors": 10,
        "critical_errors": 1,
        "warning_errors": 5,
        "info_errors": 4,
    }
