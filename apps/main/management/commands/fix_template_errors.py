from django.core.management import call_command
from django.core.management.base import BaseCommand


class Command(BaseCommand):
    help = "Fix template errors automatically as specified in fix all.yml"

    def add_arguments(self, parser):
        parser.add_argument(
            "--auto",
            action="store_true",
            help="Enable automatic fixes",
        )

    def handle(self, *args, **options):
        """Fix template errors automatically"""
        self.stdout.write(self.style.SUCCESS("Running template error fixes..."))

        try:
            # Run template validation with auto-fix
            call_command("validate_templates", "--auto-fix", "--strict")
            self.stdout.write(
                self.style.SUCCESS("Template fixes completed successfully")
            )

        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Template fixes failed: {e}"))
            return

        self.stdout.write(self.style.SUCCESS("All template errors have been fixed"))
