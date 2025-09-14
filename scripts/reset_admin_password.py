#!/usr/bin/env python
import os
import django

# Django setup
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'portfolio_site.settings')
django.setup()

from apps.main.models import Admin

try:
    admin_user = Admin.objects.get(email='admin@portfolio.com')
    admin_user.set_password('admin123')  # Simple password for development
    admin_user.save()
    print("Admin password successfully reset!")
    print("Email: admin@portfolio.com")
    print("Password: admin123")
except Admin.DoesNotExist:
    print("Admin user not found")
except Exception as e:
    print(f"Error: {e}")