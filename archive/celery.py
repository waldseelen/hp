"""
Celery configuration for portfolio_site project.
"""

import os

from django.conf import settings

from celery import Celery
from kombu import Queue

# Set the default Django settings module for the 'celery' program.
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings.development")

app = Celery("portfolio_site")

# Using a string here means the worker doesn't have to serialize
# the configuration object to child processes.
# - namespace='CELERY' means all celery-related configuration keys
#   should have a `CELERY_` prefix.
app.config_from_object("django.conf:settings", namespace="CELERY")

# Load task modules from all registered Django apps.
app.autodiscover_tasks()

# Configure Celery
app.conf.update(
    # Task routing
    task_routes={
        # High priority tasks
        "apps.main.tasks.send_notification": {"queue": "high_priority"},
        "apps.main.tasks.process_user_action": {"queue": "high_priority"},
        # Normal priority tasks
        "apps.main.tasks.update_analytics": {"queue": "default"},
        "apps.main.tasks.cleanup_temp_files": {"queue": "default"},
        # Low priority tasks
        "apps.main.tasks.generate_reports": {"queue": "low_priority"},
        "apps.main.tasks.backup_data": {"queue": "low_priority"},
    },
    # Queue configuration
    task_queues=(
        Queue("high_priority", routing_key="high_priority"),
        Queue("default", routing_key="default"),
        Queue("low_priority", routing_key="low_priority"),
    ),
    task_default_queue="default",
    task_default_exchange_type="direct",
    task_default_routing_key="default",
    # Task execution
    task_always_eager=False,  # Set to True for synchronous execution in tests
    task_eager_propagates=True,
    task_ignore_result=False,
    task_store_eager_result=True,
    # Task retry configuration
    task_retry_jitter=True,
    task_retry_jitter_max=60,
    task_retry_delay=60,
    task_max_retries=3,
    # Worker configuration
    worker_concurrency=4,
    worker_prefetch_multiplier=1,
    worker_max_tasks_per_child=1000,
    worker_disable_rate_limits=False,
    # Task time limits
    task_soft_time_limit=60,  # 1 minute soft limit
    task_time_limit=120,  # 2 minute hard limit
    # Result backend configuration
    result_expires=3600,  # 1 hour
    result_compression="gzip",
    # Monitoring
    worker_send_task_events=True,
    task_send_sent_event=True,
    # Security
    task_serializer="json",
    result_serializer="json",
    accept_content=["json"],
    timezone="UTC",
    enable_utc=True,
    # Beat configuration (for periodic tasks)
    beat_schedule={
        "cleanup-temp-files": {
            "task": "apps.main.tasks.cleanup_temp_files",
            "schedule": 3600.0,  # Every hour
        },
        "update-analytics": {
            "task": "apps.main.tasks.update_analytics",
            "schedule": 300.0,  # Every 5 minutes
        },
        "health-check": {
            "task": "apps.main.tasks.health_check",
            "schedule": 60.0,  # Every minute
        },
        "generate-daily-reports": {
            "task": "apps.main.tasks.generate_daily_reports",
            "schedule": 86400.0,  # Every day
        },
    },
)


@app.task(bind=True)
def debug_task(self):
    """Debug task for testing Celery configuration."""
    print(f"Request: {self.request!r}")
    return "Debug task completed"


# Configure logging
@app.task(bind=True)
def log_task_info(self, message):
    """Log task information."""
    print(f"Task {self.request.id}: {message}")
    return f"Logged: {message}"
