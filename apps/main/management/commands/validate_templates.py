from django.core.management.base import BaseCommand, CommandError
from django.template import Template, Context, TemplateSyntaxError
from django.template.loader import get_template
from django.conf import settings
import os
import glob
import re
import logging
from datetime import datetime

class Command(BaseCommand):
    help = 'Validate all Django templates for syntax errors'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix-common',
            action='store_true',
            help='Show suggestions for common template errors',
        )
        parser.add_argument(
            '--auto-fix',
            action='store_true',
            help='Automatically fix common template errors',
        )
        parser.add_argument(
            '--strict',
            action='store_true',
            help='Run in strict mode with enhanced validation',
        )
        parser.add_argument(
            '--output-log',
            type=str,
            help='Output results to log file',
        )

    def handle(self, *args, **options):
        errors_found = 0
        templates_checked = 0
        fixes_applied = 0

        # Setup logging if requested
        if options['output_log']:
            logging.basicConfig(
                filename=options['output_log'],
                level=logging.INFO,
                format='[%(asctime)s] %(levelname)s: %(message)s'
            )
            logger = logging.getLogger(__name__)
        else:
            logger = None
        
        # Get all template directories
        template_dirs = []
        for template_setting in settings.TEMPLATES:
            if 'DIRS' in template_setting:
                template_dirs.extend(template_setting['DIRS'])
        
        # Add default template directories from installed apps
        for app in settings.INSTALLED_APPS:
            try:
                app_templates = os.path.join(settings.BASE_DIR, app.replace('.', '/'), 'templates')
                if os.path.exists(app_templates):
                    template_dirs.append(app_templates)
            except:
                pass
        
        # Check templates directory
        main_templates = os.path.join(settings.BASE_DIR, 'templates')
        if os.path.exists(main_templates):
            template_dirs.append(main_templates)
        
        self.stdout.write(self.style.SUCCESS(f'Checking templates in directories: {template_dirs}'))
        
        for template_dir in template_dirs:
            if not os.path.exists(template_dir):
                continue
                
            # Find all .html files
            pattern = os.path.join(template_dir, '**', '*.html')
            template_files = glob.glob(pattern, recursive=True)
            
            for template_file in template_files:
                templates_checked += 1
                try:
                    with open(template_file, 'r', encoding='utf-8') as f:
                        template_content = f.read()

                    # Enhanced validation in strict mode
                    if options['strict']:
                        validation_errors = self.validate_template_structure(template_content, template_file)
                        if validation_errors:
                            errors_found += len(validation_errors)
                            rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                            for error in validation_errors:
                                self.stdout.write(self.style.WARNING(f'[WARN] {rel_path}: {error}'))
                                if logger:
                                    logger.warning(f'{rel_path}: {error}')

                    # Auto-fix common errors if requested
                    if options['auto_fix']:
                        fixed_content, applied_fixes = self.auto_fix_template(template_content)
                        if applied_fixes:
                            with open(template_file, 'w', encoding='utf-8') as f:
                                f.write(fixed_content)
                            fixes_applied += len(applied_fixes)
                            rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                            self.stdout.write(self.style.SUCCESS(f'[FIXED] {rel_path}: Applied {len(applied_fixes)} fixes'))
                            for fix in applied_fixes:
                                self.stdout.write(f'    - {fix}')
                            template_content = fixed_content

                    # Try to compile the template
                    Template(template_content)
                    rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                    self.stdout.write(f'[OK] {rel_path}')
                    if logger:
                        logger.info(f'Template validation passed: {rel_path}')

                except TemplateSyntaxError as e:
                    errors_found += 1
                    rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                    self.stdout.write(
                        self.style.ERROR(f'[ERROR] {rel_path}: {e}')
                    )
                    if logger:
                        logger.error(f'{rel_path}: {e}')

                    if options['fix_common']:
                        self.suggest_fixes(str(e), template_content)

                except Exception as e:
                    errors_found += 1
                    rel_path = os.path.relpath(template_file, settings.BASE_DIR)
                    self.stdout.write(
                        self.style.ERROR(f'[ERROR] {rel_path}: Unexpected error - {e}')
                    )
                    if logger:
                        logger.error(f'{rel_path}: Unexpected error - {e}')
        
        # Summary
        self.stdout.write('\n' + '='*50)
        self.stdout.write(f'Templates checked: {templates_checked}')
        if options['auto_fix'] and fixes_applied > 0:
            self.stdout.write(f'Fixes applied: {fixes_applied}')

        if errors_found == 0:
            self.stdout.write(self.style.SUCCESS(f'[SUCCESS] All templates are valid!'))
            if logger:
                logger.info(f'Template validation completed successfully. {templates_checked} templates checked.')
        else:
            self.stdout.write(self.style.ERROR(f'[FAIL] Found {errors_found} template errors'))
            if logger:
                logger.error(f'Template validation failed with {errors_found} errors')
            raise CommandError(f'Template validation failed with {errors_found} errors')

    def suggest_fixes(self, error_msg, template_content):
        """Suggest fixes for common template errors"""
        suggestions = []
        
        if 'Invalid filter' in error_msg:
            if 'mul' in error_msg:
                suggestions.append("Add {% load math_filters %} at the top of your template")
                suggestions.append("Or replace |mul: with manual calculation")
            elif 'div' in error_msg:
                suggestions.append("Add {% load math_filters %} at the top of your template")
            else:
                suggestions.append("Check if you need to load custom template tags")
        
        elif 'Invalid block tag' in error_msg:
            suggestions.append("Check if the template tag is properly registered")
            suggestions.append("Ensure the app containing the tag is in INSTALLED_APPS")
        
        elif 'Unclosed tag' in error_msg:
            suggestions.append("Check for missing {% end... %} tags")
            suggestions.append("Verify all opening tags have corresponding closing tags")
        
        if suggestions:
            self.stdout.write(self.style.WARNING('  Suggestions:'))
            for suggestion in suggestions:
                self.stdout.write(f'    - {suggestion}')

    def validate_template_structure(self, content, template_path):
        """Enhanced template structure validation"""
        errors = []
        lines = content.split('\n')

        # Check for unclosed tags
        tag_stack = []
        for i, line in enumerate(lines, 1):
            # Find Django template tags
            tag_matches = re.findall(r'{%\s*(\w+)', line)
            end_tag_matches = re.findall(r'{%\s*end(\w+)', line)

            for tag in tag_matches:
                if tag in ['if', 'for', 'block', 'with', 'comment', 'autoescape', 'verbatim']:
                    tag_stack.append((tag, i))

            for end_tag in end_tag_matches:
                if tag_stack and tag_stack[-1][0] == end_tag:
                    tag_stack.pop()
                else:
                    errors.append(f'Line {i}: Mismatched end tag "end{end_tag}"')

        # Check for unclosed tags at end
        for tag, line_num in tag_stack:
            errors.append(f'Line {line_num}: Unclosed tag "{tag}"')

        # Check for proper template inheritance
        if '{% extends' in content:
            if not re.search(r'{%\s*extends\s+["\'][^"\']+["\']\s*%}', content.split('\n')[0]):
                first_non_empty = next((i for i, line in enumerate(lines) if line.strip()), 0)
                if first_non_empty > 0:
                    errors.append('{% extends %} should be the first line in the template')

        # Check for static file references
        if '{% static' in content and '{% load static' not in content:
            errors.append('Template uses {% static %} but missing {% load static %}')

        # Check for variable syntax issues
        invalid_variables = re.findall(r'{{[^}]*}}', content)
        for var in invalid_variables:
            if '{{' in var[2:-2] or '}}' in var[2:-2]:
                errors.append(f'Invalid nested variable syntax: {var}')

        return errors

    def auto_fix_template(self, content):
        """Auto-fix common template errors"""
        fixes_applied = []
        original_content = content

        # Fix spacing in template tags
        content = re.sub(r'{%(\w)', r'{% \1', content)
        if content != original_content:
            fixes_applied.append('Fixed template tag spacing')
            original_content = content

        content = re.sub(r'(\w)%}', r'\1 %}', content)
        if content != original_content:
            fixes_applied.append('Fixed template tag closing spacing')
            original_content = content

        # Fix spacing in variables
        content = re.sub(r'{{(\w)', r'{{ \1', content)
        if content != original_content:
            fixes_applied.append('Fixed variable opening spacing')
            original_content = content

        content = re.sub(r'(\w)}}', r'\1 }}', content)
        if content != original_content:
            fixes_applied.append('Fixed variable closing spacing')
            original_content = content

        # Fix common endblock issues
        content = re.sub(r'{%\s*endblock\s*%}', '{% endblock %}', content)
        if content != original_content:
            fixes_applied.append('Fixed endblock syntax')
            original_content = content

        # Add missing load static if static is used
        if '{% static' in content and '{% load static' not in content:
            # Find extends line or add at top
            lines = content.split('\n')
            extends_line = -1
            for i, line in enumerate(lines):
                if '{% extends' in line:
                    extends_line = i
                    break

            if extends_line >= 0:
                lines.insert(extends_line + 1, '{% load static %}')
            else:
                lines.insert(0, '{% load static %}')

            content = '\n'.join(lines)
            fixes_applied.append('Added missing {% load static %}')

        return content, fixes_applied