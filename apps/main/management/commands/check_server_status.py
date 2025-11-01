from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Check server status as specified in fix all.yml"

    def handle(self, *args, **options):
        """Check Django server status"""
        self.stdout.write(self.style.SUCCESS("Checking Django server status..."))

        try:
            # Use the manage_server command with --status
            call_command("manage_server", "--status")

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Server status check failed: {e}"))
