#!/usr/bin/env python3
import os
import sys

import django

# Setup Django environment
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
django.setup()

from main.models import PersonalInfo


def update_personal_info():
    # Delete existing data
    PersonalInfo.objects.all().delete()

    # Personal Information Data
    personal_data = [
        {"key": "full_name", "value": "Bugra AKIN", "type": "text", "order": 1},
        {
            "key": "official_name",
            "value": "MUHAMMED BUGRA AKIN",
            "type": "text",
            "order": 2,
        },
        {"key": "email", "value": "bugraakin01@gmail.com", "type": "text", "order": 3},
        {"key": "phone", "value": "+90 (555) 123 45 67", "type": "text", "order": 4},
        {"key": "location", "value": "Ankara, Turkiye", "type": "text", "order": 5},
        {"key": "postal_code", "value": "06350, Ankara", "type": "text", "order": 6},
        {
            "key": "title",
            "value": "EEE | Embedded Systems | Linux | AI | Cloud | Cybersecurity",
            "type": "text",
            "order": 7,
        },
        {
            "key": "bio",
            "value": "Gaziantep Universitesi nde Elektrik-Elektronik Muhendisligi ogrencisi; veri analizi, problem cozme ve Windows hizmetleri alanlarinda deneyim; universitede Bilgi Islem Sorumlusu olarak pratik tecrube.",
            "type": "text",
            "order": 8,
        },
        {
            "key": "university",
            "value": "Gaziantep Universitesi",
            "type": "text",
            "order": 9,
        },
        {
            "key": "degree",
            "value": "Elektrik-Elektronik Muhendisligi (I.O) - Lisans",
            "type": "text",
            "order": 10,
        },
        {
            "key": "student_status",
            "value": "Aktif (E-Devletten kayit yapan)",
            "type": "text",
            "order": 11,
        },
        {"key": "total_credits", "value": "75", "type": "text", "order": 12},
        {"key": "total_ects", "value": "98", "type": "text", "order": 13},
        {"key": "student_number", "value": "190115011098", "type": "text", "order": 14},
    ]

    for data in personal_data:
        PersonalInfo.objects.create(
            key=data["key"],
            value=data["value"],
            type=data["type"],
            order=data["order"],
            is_visible=True,
        )

    print(f"Updated {len(personal_data)} personal information records")


if __name__ == "__main__":
    update_personal_info()
