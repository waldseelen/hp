"""
Core app configuration.
Registers cache invalidation signals on app startup.
"""

from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.core"
    verbose_name = "Core"

    def ready(self):
        """Import signal handlers when Django starts."""
        try:
            import apps.core.cache_signals  # noqa: F401
        except ImportError:
            pass
