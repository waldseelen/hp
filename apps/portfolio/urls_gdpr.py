"""
GDPR Compliance URL Configuration
================================

URL patterns for GDPR/KVKK compliance features including:
- Cookie consent management
- Data export functionality
- Account deletion requests
- Privacy policy and cookie policy
- Privacy dashboard
"""

from django.urls import path

from apps.main.views import gdpr_views

app_name = "gdpr"

urlpatterns = [
    # Cookie Consent Management
    path("cookie-consent/", gdpr_views.cookie_consent, name="cookie_consent"),
    path(
        "cookie-consent/status/",
        gdpr_views.cookie_consent_status,
        name="cookie_consent_status",
    ),
    # Data Export
    path("data-export/", gdpr_views.request_data_export, name="data_export"),
    # Account Deletion
    path(
        "account-deletion/",
        gdpr_views.request_account_deletion,
        name="account_deletion",
    ),
    # Privacy Dashboard (requires login)
    path("privacy-dashboard/", gdpr_views.privacy_dashboard, name="privacy_dashboard"),
    # Static Pages
    path("privacy-policy/", gdpr_views.privacy_policy, name="privacy_policy"),
    path("cookie-policy/", gdpr_views.cookie_policy, name="cookie_policy"),
]
