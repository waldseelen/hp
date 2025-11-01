#!/usr/bin/env python
import os

import django

# Django setup
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")
django.setup()

from main.models import Admin

try:
    admin_user = Admin.objects.get(email="admin@portfolio.com")
    # Get password from environment variable
    new_password = os.environ.get("ADMIN_PASSWORD")
    if not new_password:
        print("❌ Error: ADMIN_PASSWORD environment variable not set")
        print("Set it using: export ADMIN_PASSWORD='your-password'")
        exit(1)

    admin_user.set_password(new_password)
    admin_user.save()
    print("Admin password successfully reset!")
    print("Email: admin@portfolio.com")
except Admin.DoesNotExist:
    print("Admin user not found")
except Exception as e:
    print(f"Error: {e}")
