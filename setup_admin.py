#!/usr/bin/env python
"""
Setup admin user for Django admin panel
"""
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from apps.main.models import Admin

# Delete existing admin if exists
Admin.objects.filter(email="admin@portfolio.com").delete()

# Create new admin with simple credentials
admin = Admin.objects.create_superuser(
    email="admin@portfolio.com", username="admin", name="Admin User", password="admin"
)

print(f"✅ Admin user created successfully!")
print(f"📧 Email: admin@portfolio.com")
print(f"🔐 Password: admin")
print(f"👤 Username: admin")
print(f"\n⚠️  TEST CREDENTIALS - Change in production!")
