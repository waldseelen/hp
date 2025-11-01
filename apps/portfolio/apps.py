from django.apps import AppConfig


class PortfolioConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.portfolio"

    def ready(self):
        # Import signals if any
        pass


class MainConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.main"

    def ready(self):
        pass
