#!/usr/bin/env python
"""
Template validation script to run before starting the Django server.
This helps catch template errors early before they cause runtime issues.
"""

import os
import sys
import django
from django.core.management import call_command
from django.core.management.base import CommandError

def setup_django():
    """Set up Django environment"""
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings')
    django.setup()

def validate_templates():
    """Validate all templates"""
    try:
        call_command('validate_templates')
        print("✓ All templates validated successfully!")
        return True
    except CommandError as e:
        print(f"✗ Template validation failed: {e}")
        return False
    except Exception as e:
        print(f"✗ Unexpected error during validation: {e}")
        return False

if __name__ == "__main__":
    print("Validating Django templates...")
    setup_django()
    
    if not validate_templates():
        print("\nTemplate validation failed. Please fix the errors before running the server.")
        sys.exit(1)
    
    print("Template validation passed! You can now run the server safely.")