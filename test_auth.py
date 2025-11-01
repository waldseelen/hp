#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings.simple")
django.setup()

from django.contrib.auth import authenticate

from decouple import config

email = "bugraakin01@gmail.com"
password = "9CXb8|)\u00a3Y=o3@0AdV_M{P&="

print("=" * 60)
print("AUTHENTICATION TEST")
print("=" * 60)
print(f"Email: {email}")
print(f"Password: {password[:10]}...")
print(f"\n.env ALLOWED_ADMIN_EMAIL: {config('ALLOWED_ADMIN_EMAIL', default='NOT SET')}")
print(
    f".env ALLOWED_ADMIN_PASSWORD_HASH: {config('ALLOWED_ADMIN_PASSWORD_HASH', default='NOT SET')[:50]}..."
)

print("\n" + "=" * 60)
print("Attempting authentication...")
print("=" * 60)

user = authenticate(username=email, password=password)

if user:
    print(f"✅ SUCCESS! User authenticated: {user.email}")
    print(f"   - is_staff: {user.is_staff}")
    print(f"   - is_superuser: {user.is_superuser}")
    print(f"   - is_active: {user.is_active}")
else:
    print("❌ FAILED! Authentication returned None")
    print("\nTroubleshooting:")
    print("1. Check if backend is configured correctly")
    print("2. Verify password hash in .env matches")
    print("3. Check if email matches exactly (case-insensitive)")

print("=" * 60)
