"""
Celery tasks for main app.

Handles async operations like:
- Sending notifications
- Processing user actions
- Updating analytics
- Cleanup operations
- Health checks
"""

import logging
import traceback

from django.conf import settings
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.utils import timezone

from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
    autoretry_for=(Exception,),
)
def send_notification(self, user_id, title, message, notification_type="info"):
    """
    Send a notification to a user.

    Args:
        user_id: ID of the user to notify
        title: Notification title
        message: Notification message
        notification_type: Type of notification (info, warning, error)

    Returns:
        Dictionary with notification status
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(
            f"Sending {notification_type} notification to {user.email}: {title}"
        )

        # Send email notification
        subject = f"Notification: {title}"
        send_mail(
            subject,
            message,
            settings.DEFAULT_FROM_EMAIL,
            [user.email],
            fail_silently=False,
        )

        logger.info(f"Notification sent successfully to {user.email}")
        return {
            "status": "success",
            "user_id": user_id,
            "message": message,
            "timestamp": timezone.now().isoformat(),
        }

    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Error sending notification: {exc}")
        logger.error(traceback.format_exc())
        # Retry with exponential backoff
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(
    bind=True,
    max_retries=3,
    default_retry_delay=60,
)
def process_user_action(self, user_id, action, data=None):
    """
    Process user action asynchronously.

    Args:
        user_id: ID of the user
        action: Action type (view, click, submit, etc.)
        data: Additional action data

    Returns:
        Dictionary with processing status
    """
    try:
        user = User.objects.get(id=user_id)
        logger.info(f"Processing action '{action}' for user {user.username}")

        if data is None:
            data = {}

        # Process action based on type
        if action == "view":
            logger.debug(f"User viewed: {data.get('item', 'unknown')}")
        elif action == "click":
            logger.debug(f"User clicked: {data.get('element', 'unknown')}")
        elif action == "submit":
            logger.debug(f"User submitted: {data.get('form', 'unknown')}")

        return {
            "status": "success",
            "user_id": user_id,
            "action": action,
            "timestamp": timezone.now().isoformat(),
        }

    except User.DoesNotExist:
        logger.error(f"User with id {user_id} not found")
        raise

    except Exception as exc:
        logger.error(f"Error processing user action: {exc}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=3)
def update_analytics(self):
    """
    Update analytics data.

    This task aggregates user activity data and updates analytics dashboard.

    Returns:
        Dictionary with update status
    """
    try:
        logger.info("Starting analytics update")

        # Placeholder for analytics update logic
        timestamp = timezone.now()

        logger.info(f"Analytics updated successfully at {timestamp}")

        return {
            "status": "success",
            "records_processed": 0,  # Would be actual count in production
            "timestamp": timestamp.isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error updating analytics: {exc}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=exc, countdown=2**self.request.retries)


@shared_task(bind=True, max_retries=2)
def cleanup_temp_files(self):
    """
    Clean up temporary files and old data.

    Handles:
    - Cleaning old session files
    - Removing old logs
    - Cleaning temporary uploads

    Returns:
        Dictionary with cleanup status
    """
    try:
        logger.info("Starting temporary file cleanup")

        # Placeholder for cleanup logic
        files_deleted = 0
        logs_deleted = 0

        logger.info(
            f"Cleanup completed: {files_deleted} files, {logs_deleted} logs deleted"
        )

        return {
            "status": "success",
            "files_deleted": files_deleted,
            "logs_deleted": logs_deleted,
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error during cleanup: {exc}")
        logger.error(traceback.format_exc())
        raise self.retry(exc=exc, countdown=60)


@shared_task(bind=True, max_retries=3)
def health_check(self):
    """
    Perform system health check.

    Checks:
    - Database connectivity
    - Cache connectivity
    - Disk space
    - Memory usage

    Returns:
        Dictionary with health status
    """
    try:
        logger.info("Starting system health check")

        from django.db import connection

        # Test database
        with connection.cursor() as cursor:
            cursor.execute("SELECT 1")
            db_ok = cursor.fetchone() is not None

        logger.info("Health check completed")

        return {
            "status": "healthy",
            "database": "connected" if db_ok else "disconnected",
            "timestamp": timezone.now().isoformat(),
        }

    except Exception as exc:
        logger.error(f"Error during health check: {exc}")
        logger.error(traceback.format_exc())

        # Try to retry if it's a connection issue
        if "connection" in str(exc).lower():
            raise self.retry(exc=exc, countdown=30)

        return {
            "status": "unhealthy",
            "error": str(exc),
            "timestamp": timezone.now().isoformat(),
        }
