from django.core.management.base import BaseCommand

from apps.playground.models import CodeTemplate, ProgrammingLanguage


class Command(BaseCommand):
    help = "Setup initial playground data with languages and templates"

    def handle(self, *args, **options):
        self.stdout.write("Setting up CodePlay playground...")

        # Create programming languages
        languages = [
            {
                "name": "Python",
                "icon": "PY",
                "tagline": "AI Programming",
                "extension": "py",
                "order": 1,
            },
            {
                "name": "JavaScript",
                "icon": "JS",
                "tagline": "Web Development",
                "extension": "js",
                "order": 2,
            },
            {
                "name": "C",
                "icon": "C",
                "tagline": "System Programming",
                "extension": "c",
                "order": 3,
            },
            {
                "name": "C++",
                "icon": "C++",
                "tagline": "Game Development",
                "extension": "cpp",
                "order": 4,
            },
            {
                "name": "C#",
                "icon": "C#",
                "tagline": "Enterprise Apps",
                "extension": "cs",
                "order": 5,
            },
        ]

        for lang_data in languages:
            language, created = ProgrammingLanguage.objects.get_or_create(
                name=lang_data["name"], defaults=lang_data
            )
            if created:
                self.stdout.write(f'Created language: {lang_data["name"]}')

        # Create simple templates
        python = ProgrammingLanguage.objects.get(name="Python")
        js = ProgrammingLanguage.objects.get(name="JavaScript")

        templates = [
            {
                "name": "Hello World Python",
                "description": "Basic Python program",
                "language": python,
                "emoji": "[PY]",
                "is_featured": True,
                "code": 'print("Hello, CodePlay!")\nprint("Welcome to Python programming!")',
            },
            {
                "name": "Hello World JavaScript",
                "description": "Basic JavaScript program",
                "language": js,
                "emoji": "[JS]",
                "is_featured": True,
                "code": 'console.log("Hello, CodePlay!");\nconsole.log("Welcome to JavaScript programming!");',
            },
        ]

        for template_data in templates:
            template, created = CodeTemplate.objects.get_or_create(
                name=template_data["name"], defaults=template_data
            )
            if created:
                self.stdout.write(f'Created template: {template_data["name"]}')

        self.stdout.write(self.style.SUCCESS("Setup completed!"))
