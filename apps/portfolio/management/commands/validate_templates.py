import glob
import os

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError
from django.template import Template, TemplateSyntaxError


class Command(BaseCommand):
    help = "Validate all Django templates for syntax errors"

    def add_arguments(self, parser):
        parser.add_argument(
            "--fix-common",
            action="store_true",
            help="Show suggestions for common template errors",
        )

    def handle(self, *args, **options):  # noqa: C901
        errors_found = 0
        templates_checked = 0

        # Get all template directories
        template_dirs = []
        for template_setting in settings.TEMPLATES:
            if "DIRS" in template_setting:
                template_dirs.extend(template_setting["DIRS"])

        # Add default template directories from installed apps
        for app in settings.INSTALLED_APPS:
            try:
                app_templates = os.path.join(
                    settings.BASE_DIR, app.replace(".", "/"), "templates"
                )
                if os.path.exists(app_templates):
                    template_dirs.append(app_templates)
            except Exception:
                # Skip apps without templates
                pass

        # Check templates directory
        main_templates = os.path.join(settings.BASE_DIR, "templates")
        if os.path.exists(main_templates):
            template_dirs.append(main_templates)

        self.stdout.write(
            self.style.SUCCESS(f"Checking templates in directories: {template_dirs}")
        )

        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                continue

            # Find all .html files
            pattern = os.path.join(template_dir, "**", "*.html")
            template_files = glob.glob(pattern, recursive=True)

            for template_file in template_files:
                templates_checked += 1
                try:
                    with open(template_file, "r", encoding="utf-8") as f:
                        template_content = f.read()

                    # Try to compile the template
                    Template(template_content)
                    self.stdout.write(
                        f"[OK] {os.path.relpath(template_file, settings.BASE_DIR)}"
                    )

                except TemplateSyntaxError as e:
                    errors_found += 1
                    rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                    self.stdout.write(self.style.ERROR(f"[ERROR] {rel_path}: {e}"))

                    if options["fix_common"]:
                        self.suggest_fixes(str(e), template_content)

                except Exception as e:
                    errors_found += 1
                    rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                    self.stdout.write(
                        self.style.ERROR(f"[ERROR] {rel_path}: Unexpected error - {e}")
                    )

        # Summary
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(f"Templates checked: {templates_checked}")

        if errors_found == 0:
            self.stdout.write(self.style.SUCCESS("[SUCCESS] All templates are valid!"))
        else:
            self.stdout.write(
                self.style.ERROR(f"[FAIL] Found {errors_found} template errors")
            )
            raise CommandError(f"Template validation failed with {errors_found} errors")

    def suggest_fixes(self, error_msg, template_content):
        """Suggest fixes for common template errors"""
        suggestions = []

        if "Invalid filter" in error_msg:
            if "mul" in error_msg:
                suggestions.append(
                    "Add {% load math_filters %} at the top of your template"
                )
                suggestions.append("Or replace |mul: with manual calculation")
            elif "div" in error_msg:
                suggestions.append(
                    "Add {% load math_filters %} at the top of your template"
                )
            else:
                suggestions.append("Check if you need to load custom template tags")

        elif "Invalid block tag" in error_msg:
            suggestions.append("Check if the template tag is properly registered")
            suggestions.append("Ensure the app containing the tag is in INSTALLED_APPS")

        elif "Unclosed tag" in error_msg:
            suggestions.append("Check for missing {% end... %} tags")
            suggestions.append(
                "Verify all opening tags have corresponding closing tags"
            )

        if suggestions:
            self.stdout.write(self.style.WARNING("  Suggestions:"))
            for suggestion in suggestions:
                self.stdout.write(f"    - {suggestion}")
