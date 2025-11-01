"""
Management command to test Celery setup and task execution.
"""

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.main.tasks import (
    cleanup_temp_files,
    health_check,
    process_user_action,
    send_notification,
    update_analytics,
)


class Command(BaseCommand):
    help = "Test Celery task execution and monitoring"

    def add_arguments(self, parser):
        parser.add_argument(
            "--task",
            type=str,
            choices=[
                "all",
                "notification",
                "user_action",
                "analytics",
                "cleanup",
                "health",
            ],
            default="all",
            help="Which task to test (default: all)",
        )

    def handle(self, *args, **options):
        task_type = options["task"]

        self.stdout.write(self.style.SUCCESS("Testing Celery task execution..."))

        if task_type in ["all", "notification"]:
            self.test_notification_task()

        if task_type in ["all", "user_action"]:
            self.test_user_action_task()

        if task_type in ["all", "analytics"]:
            self.test_analytics_task()

        if task_type in ["all", "cleanup"]:
            self.test_cleanup_task()

        if task_type in ["all", "health"]:
            self.test_health_task()

        self.stdout.write(self.style.SUCCESS("Celery task testing completed!"))

    def test_notification_task(self):
        """Test notification task."""
        self.stdout.write("Testing notification task...")

        try:
            # Test async execution
            result = send_notification.delay(
                user_id=1,
                title="Test Notification",
                message="This is a test notification from Celery",
                notification_type="info",
            )

            self.stdout.write(f"Task ID: {result.task_id}")
            self.stdout.write("Waiting for result...")

            # Wait for result with timeout
            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Notification task completed: {task_result}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Notification task failed: {e}"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Error testing notification task: {e}")
            )

    def test_user_action_task(self):
        """Test user action processing task."""
        self.stdout.write("Testing user action task...")

        try:
            result = process_user_action.delay(
                user_id=1,
                action="test_action",
                data={"test": "data", "timestamp": timezone.now().isoformat()},
            )

            self.stdout.write(f"Task ID: {result.task_id}")

            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ User action task completed: {task_result}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ User action task failed: {e}"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Error testing user action task: {e}")
            )

    def test_analytics_task(self):
        """Test analytics update task."""
        self.stdout.write("Testing analytics task...")

        try:
            result = update_analytics.delay()

            self.stdout.write(f"Task ID: {result.task_id}")

            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Analytics task completed: {task_result}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Analytics task failed: {e}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error testing analytics task: {e}"))

    def test_cleanup_task(self):
        """Test cleanup task."""
        self.stdout.write("Testing cleanup task...")

        try:
            result = cleanup_temp_files.delay()

            self.stdout.write(f"Task ID: {result.task_id}")

            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Cleanup task completed: {task_result}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Cleanup task failed: {e}"))

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error testing cleanup task: {e}"))

    def test_health_task(self):
        """Test health check task."""
        self.stdout.write("Testing health check task...")

        try:
            result = health_check.delay()

            self.stdout.write(f"Task ID: {result.task_id}")

            try:
                task_result = result.get(timeout=30)
                self.stdout.write(
                    self.style.SUCCESS(f"✓ Health check task completed: {task_result}")
                )
            except Exception as e:
                self.stdout.write(self.style.ERROR(f"✗ Health check task failed: {e}"))

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f"✗ Error testing health check task: {e}")
            )

    def test_retry_logic(self):
        """Test task retry logic by creating a failing task."""
        self.stdout.write("Testing retry logic...")

        try:
            # This would be a task designed to fail and test retry
            result = send_notification.delay(
                user_id=999999,  # Non-existent user to trigger retry
                title="Test Retry",
                message="This should trigger retry logic",
                notification_type="info",
            )

            self.stdout.write(f"Retry test task ID: {result.task_id}")

            try:
                task_result = result.get(timeout=60)  # Longer timeout for retries
                self.stdout.write(
                    self.style.WARNING(f"Retry task result: {task_result}")
                )
            except Exception as e:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"✓ Retry logic working - task failed as expected: {e}"
                    )
                )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"✗ Error testing retry logic: {e}"))
