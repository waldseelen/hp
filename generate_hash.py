#!/usr/bin/env python
import os

import django

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "project.settings")
django.setup()

from django.contrib.auth.hashers import make_password

# Gerçek şifre
password = "9CXb8|)\u00a3Y=o3@0AdV_M{P&="
email = "bugraakin01@gmail.com"

# Hash oluştur
hashed = make_password(password)

print("=" * 60)
print("ADMIN GİRİŞ BİLGİLERİ")
print("=" * 60)
print(f"Email: {email}")
print(f"Şifre: {password}")
print(f"\n.env dosyasına eklenecek:")
print(f"ALLOWED_ADMIN_EMAIL={email}")
print(f"ALLOWED_ADMIN_PASSWORD_HASH={hashed}")
print("=" * 60)
