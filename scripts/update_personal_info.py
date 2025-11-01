#!/usr/bin/env python3
"""
Script to update personal information in Django database
Run with: python manage.py shell < update_personal_info.py
"""
import os
import sys

import django

# Setup Django
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "portfolio_site.settings")
sys.path.append(os.path.dirname(os.path.abspath(__file__)))
django.setup()

from apps.main.models import PersonalInfo


def update_personal_info():
    """Update personal information based on Buğra AKIN's details"""

    # Personal Information Data
    personal_data = [
        {"key": "full_name", "value": "Buğra AKIN", "type": "text", "order": 1},
        {
            "key": "official_name",
            "value": "MUHAMMED BUĞRA AKIN",
            "type": "text",
            "order": 2,
        },
        {"key": "email", "value": "bugraakin01@gmail.com", "type": "text", "order": 3},
        {"key": "phone", "value": "+90 (555) 123 45 67", "type": "text", "order": 4},
        {"key": "location", "value": "Ankara, Türkiye", "type": "text", "order": 5},
        {"key": "postal_code", "value": "06350, Ankara", "type": "text", "order": 6},
        {
            "key": "title",
            "value": "EEE | Embedded Systems | Linux | AI | Cloud | Cybersecurity",
            "type": "text",
            "order": 7,
        },
        {
            "key": "bio",
            "value": "Gaziantep Üniversitesi'nde Elektrik-Elektronik Mühendisliği öğrencisi; veri analizi, problem çözme ve Windows hizmetleri alanlarında deneyim; üniversitede Bilgi İşlem Sorumlusu olarak pratik tecrübe.",
            "type": "text",
            "order": 8,
        },
        {
            "key": "university",
            "value": "Gaziantep Üniversitesi",
            "type": "text",
            "order": 9,
        },
        {
            "key": "degree",
            "value": "Elektrik-Elektronik Mühendisliği (İ.Ö) — Lisans",
            "type": "text",
            "order": 10,
        },
        {
            "key": "student_status",
            "value": "Aktif (E-Devletten kayıt yapan)",
            "type": "text",
            "order": 11,
        },
        {"key": "total_credits", "value": "75", "type": "text", "order": 12},
        {"key": "total_ects", "value": "98", "type": "text", "order": 13},
        {"key": "student_number", "value": "190115011098", "type": "text", "order": 14},
        {
            "key": "certifications",
            "value": """[
    {
        "name": "Veri Bilimi Zirvesi",
        "date": "26.09.2023",
        "certificate_no": "q8ZpimWZpP"
    },
    {
        "name": "Kişiselleştirilmiş GPT'ler (Çevrim içi)",
        "date": "22.07.2025",
        "certificate_no": "EoPfJbEE4P"
    },
    {
        "name": "Üretken Yapay Zeka ile Büyük Dil Modelleri (LLM) Atölyesi",
        "date": "28.07.2025–08.08.2025",
        "duration": "60 saat",
        "certificate_no": "4BW7Tj70"
    },
    {
        "name": "Siber Güvenliğe Giriş (Çevrim içi)",
        "date": "02.08.2025",
        "certificate_no": "dx1hlAXXVO"
    }
]""",
            "type": "json",
            "order": 15,
        },
    ]

    # Update or create personal information
    updated_count = 0
    created_count = 0

    for data in personal_data:
        obj, created = PersonalInfo.objects.update_or_create(
            key=data["key"],
            defaults={
                "value": data["value"],
                "type": data["type"],
                "order": data["order"],
                "is_visible": True,
            },
        )

        if created:
            created_count += 1
            print(f"✓ Created: {data['key']}")
        else:
            updated_count += 1
            print(f"✓ Updated: {data['key']}")

    print(f"\n📊 Summary:")
    print(f"   - Created: {created_count} records")
    print(f"   - Updated: {updated_count} records")
    print(f"   - Total: {created_count + updated_count} records processed")
    print("\n🎉 Personal information updated successfully!")


if __name__ == "__main__":
    update_personal_info()
