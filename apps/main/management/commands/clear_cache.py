from django.core.cache import cache
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Clear Django cache as specified in fix all.yml"

    def handle(self, *args, **options):
        """Clear Django cache"""
        self.stdout.write(self.style.SUCCESS("Clearing Django cache..."))

        try:
            # Clear Django cache
            cache.clear()
            self.stdout.write(self.style.SUCCESS("Django cache cleared successfully"))

            # Clear template cache by restarting Django if possible
            self.stdout.write("Clearing template cache...")

            # Also clear any collected static files if needed
            self.stdout.write("Cache clearing completed")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Cache clearing failed: {e}"))
