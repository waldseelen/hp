"""
GDPR Compliance Middleware
==========================

Middleware for GDPR (General Data Protection Regulation) compliance:
- Cookie consent tracking
- Data collection logging
- Privacy preferences management
- User consent validation

GDPR Articles Covered:
- Article 6: Lawfulness of processing (consent)
- Article 7: Conditions for consent
- Article 13: Information to be provided (transparency)
- Article 15: Right of access
- Article 17: Right to erasure
- Article 20: Right to data portability
- Article 21: Right to object
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger(__name__)


class CookieConsentMiddleware(MiddlewareMixin):
    """
    Track and enforce cookie consent per GDPR Article 7.

    Features:
    - Cookie consent detection
    - Consent level tracking (necessary, functional, analytics, marketing)
    - Automatic cookie blocking for non-consented categories
    - Consent banner display logic
    - Consent expiry (13 months per GDPR guidelines)

    Cookie Categories:
    - necessary: Essential cookies (always allowed)
    - functional: Preference cookies
    - analytics: Performance/analytics cookies
    - marketing: Advertising/tracking cookies
    """

    CONSENT_COOKIE_NAME = "gdpr_consent"
    CONSENT_VERSION = "1.0"
    CONSENT_EXPIRY_DAYS = 365  # 13 months = ~395 days, using 365 for simplicity

    COOKIE_CATEGORIES = {
        "necessary": {
            "required": True,
            "description": "Essential cookies for website functionality",
            "cookies": ["sessionid", "csrftoken", "gdpr_consent"],
        },
        "functional": {
            "required": False,
            "description": "Cookies for enhanced functionality and personalization",
            "cookies": ["language", "theme", "timezone"],
        },
        "analytics": {
            "required": False,
            "description": "Cookies for website analytics and performance",
            "cookies": ["_ga", "_gid", "_gat", "analytics_session"],
        },
        "marketing": {
            "required": False,
            "description": "Cookies for advertising and marketing",
            "cookies": ["_fbp", "_gcl_au", "marketing_id"],
        },
    }

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        logger.info("CookieConsentMiddleware initialized")

    def process_request(self, request: HttpRequest) -> None:
        """Check and validate cookie consent."""
        consent_data = self._get_consent_data(request)

        # Attach consent data to request
        request.gdpr_consent = consent_data
        request.needs_consent_banner = self._needs_consent_banner(consent_data)

        # Log consent status
        if consent_data:
            logger.debug(f"Cookie consent found: {consent_data.get('categories', {})}")
        else:
            logger.debug("No cookie consent found")

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Filter cookies based on consent."""
        consent_data = getattr(request, "gdpr_consent", None)

        if not consent_data:
            # No consent - only allow necessary cookies
            self._filter_cookies(response, ["necessary"])
        else:
            # Filter based on consented categories
            allowed_categories = [
                cat
                for cat, consented in consent_data.get("categories", {}).items()
                if consented
            ]
            self._filter_cookies(response, allowed_categories)

        return response

    def _get_consent_data(self, request: HttpRequest) -> Optional[Dict[str, Any]]:
        """Get and validate consent data from cookie."""
        consent_cookie = request.COOKIES.get(self.CONSENT_COOKIE_NAME)

        if not consent_cookie:
            return None

        try:
            consent_data = json.loads(consent_cookie)

            # Validate consent data structure
            if not isinstance(consent_data, dict):
                return None

            # Check version
            if consent_data.get("version") != self.CONSENT_VERSION:
                return None

            # Check expiry
            timestamp = consent_data.get("timestamp")
            if not timestamp:
                return None

            consent_date = datetime.fromisoformat(timestamp)
            expiry_date = consent_date + timedelta(days=self.CONSENT_EXPIRY_DAYS)

            if datetime.now() > expiry_date:
                logger.info("Cookie consent expired")
                return None

            return consent_data

        except (json.JSONDecodeError, ValueError) as e:
            logger.warning(f"Invalid consent cookie: {e}")
            return None

    def _needs_consent_banner(self, consent_data: Optional[Dict]) -> bool:
        """Check if consent banner should be shown."""
        return consent_data is None

    def _filter_cookies(self, response: HttpResponse, allowed_categories: list) -> None:
        """Remove cookies that are not in allowed categories."""
        # Get all allowed cookie names
        allowed_cookies = set()
        for category in allowed_categories:
            if category in self.COOKIE_CATEGORIES:
                allowed_cookies.update(self.COOKIE_CATEGORIES[category]["cookies"])

        # Check response cookies
        if hasattr(response, "cookies"):
            cookies_to_delete = []

            for cookie_name in response.cookies.keys():
                # Check if cookie is in allowed list
                is_allowed = False

                # Check exact match
                if cookie_name in allowed_cookies:
                    is_allowed = True

                # Check prefix match (e.g., _ga*)
                for allowed_name in allowed_cookies:
                    if allowed_name.endswith("*") and cookie_name.startswith(
                        allowed_name[:-1]
                    ):
                        is_allowed = True
                        break

                if not is_allowed:
                    cookies_to_delete.append(cookie_name)

            # Delete non-allowed cookies
            for cookie_name in cookies_to_delete:
                response.delete_cookie(cookie_name)
                logger.debug(f"Filtered cookie: {cookie_name}")


class DataCollectionLoggingMiddleware(MiddlewareMixin):
    """
    Log data collection activities for GDPR compliance (Article 30).

    Features:
    - Log all data collection events
    - Track data processing activities
    - User consent tracking
    - Data retention period tracking
    - Anonymization support

    GDPR Requirements:
    - Records of processing activities (Article 30)
    - Lawfulness of processing (Article 6)
    - Transparency (Article 13, 14)
    """

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response

        # Sensitive endpoints that collect personal data
        self.data_collection_endpoints = getattr(
            settings,
            "GDPR_DATA_COLLECTION_ENDPOINTS",
            [
                "/api/contact/",
                "/api/newsletter/",
                "/api/analytics/",
                "/accounts/register/",
                "/accounts/profile/",
            ],
        )

        logger.info("DataCollectionLoggingMiddleware initialized")

    def process_request(self, request: HttpRequest) -> None:
        """Log data collection activities."""
        # Check if this endpoint collects data
        if not self._is_data_collection_endpoint(request.path):
            return

        # Check if user has consented
        consent_data = getattr(request, "gdpr_consent", None)
        has_consent = self._has_required_consent(request, consent_data)

        # Log data collection event
        self._log_data_collection(request, has_consent)

    def _is_data_collection_endpoint(self, path: str) -> bool:
        """Check if endpoint collects personal data."""
        for endpoint in self.data_collection_endpoints:
            if path.startswith(endpoint):
                return True
        return False

    def _has_required_consent(
        self, request: HttpRequest, consent_data: Optional[Dict]
    ) -> bool:
        """Check if user has given required consent for data collection."""
        if not consent_data:
            return False

        # For analytics endpoints, require analytics consent
        if "/analytics/" in request.path:
            return consent_data.get("categories", {}).get("analytics", False)

        # For marketing endpoints, require marketing consent
        if "/newsletter/" in request.path or "/marketing/" in request.path:
            return consent_data.get("categories", {}).get("marketing", False)

        # For other data collection, functional consent is enough
        return consent_data.get("categories", {}).get("functional", False)

    def _log_data_collection(self, request: HttpRequest, has_consent: bool) -> None:
        """Log data collection event."""
        log_data = {
            "timestamp": datetime.now().isoformat(),
            "path": request.path,
            "method": request.method,
            "user": str(request.user) if request.user.is_authenticated else "anonymous",
            "ip_address": self._get_client_ip(request),
            "has_consent": has_consent,
            "consent_data": getattr(request, "gdpr_consent", None),
        }

        logger.info(f"Data collection event: {json.dumps(log_data)}")

        # Optionally store in database for audit trail
        # DataCollectionLog.objects.create(**log_data)

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address."""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class PrivacyPreferencesMiddleware(MiddlewareMixin):
    """
    Manage user privacy preferences across the application.

    Features:
    - Load user privacy preferences
    - Apply preferences to responses
    - Cache preferences for performance
    - Track preference changes

    Privacy Preferences:
    - data_retention_period: How long to keep user data
    - allow_profiling: Allow user profiling/tracking
    - allow_third_party: Allow third-party data sharing
    - communication_preferences: Email/SMS preferences
    """

    CACHE_KEY_PREFIX = "gdpr_prefs"
    CACHE_TIMEOUT = 3600  # 1 hour

    def __init__(self, get_response):
        super().__init__(get_response)
        self.get_response = get_response
        logger.info("PrivacyPreferencesMiddleware initialized")

    def process_request(self, request: HttpRequest) -> None:
        """Load user privacy preferences."""
        if not request.user.is_authenticated:
            request.privacy_preferences = self._get_default_preferences()
            return

        # Try cache first
        cache_key = f"{self.CACHE_KEY_PREFIX}_{request.user.id}"
        preferences = cache.get(cache_key)

        if preferences is None:
            # Load from database
            preferences = self._load_user_preferences(request.user)

            # Cache for performance
            cache.set(cache_key, preferences, self.CACHE_TIMEOUT)

        request.privacy_preferences = preferences

    def _get_default_preferences(self) -> Dict[str, Any]:
        """Get default privacy preferences for anonymous users."""
        return {
            "data_retention_period": 30,  # days
            "allow_profiling": False,
            "allow_third_party": False,
            "allow_analytics": False,
            "communication_preferences": {
                "email": False,
                "sms": False,
                "push": False,
            },
        }

    def _load_user_preferences(self, user) -> Dict[str, Any]:
        """Load user privacy preferences from database."""
        try:
            from apps.core.models import PrivacyPreferences

            prefs = PrivacyPreferences.objects.filter(user=user).first()

            if prefs:
                return {
                    "data_retention_period": prefs.data_retention_period,
                    "allow_profiling": prefs.allow_profiling,
                    "allow_third_party": prefs.allow_third_party,
                    "allow_analytics": prefs.allow_analytics,
                    "communication_preferences": prefs.communication_preferences,
                }
        except Exception as e:
            logger.error(f"Failed to load privacy preferences: {e}")

        return self._get_default_preferences()


# Helper functions


def get_consent_categories(request: HttpRequest) -> Dict[str, bool]:
    """
    Get user's consent categories.

    Usage:
        consent = get_consent_categories(request)
        if consent.get('analytics'):
            # Track analytics
    """
    consent_data = getattr(request, "gdpr_consent", None)
    if not consent_data:
        return {"necessary": True}  # Only necessary allowed without consent

    return consent_data.get("categories", {"necessary": True})


def has_consent_for(request: HttpRequest, category: str) -> bool:
    """
    Check if user has consented to a specific category.

    Usage:
        if has_consent_for(request, 'analytics'):
            # Track analytics
    """
    consent = get_consent_categories(request)
    return consent.get(category, False)


def set_consent_cookie(
    response: HttpResponse,
    categories: Dict[str, bool],
    version: str = CookieConsentMiddleware.CONSENT_VERSION,
) -> None:
    """
    Set consent cookie with user's preferences.

    Usage:
        set_consent_cookie(response, {
            'necessary': True,
            'functional': True,
            'analytics': False,
            'marketing': False,
        })
    """
    consent_data = {
        "version": version,
        "timestamp": datetime.now().isoformat(),
        "categories": categories,
    }

    response.set_cookie(
        CookieConsentMiddleware.CONSENT_COOKIE_NAME,
        json.dumps(consent_data),
        max_age=CookieConsentMiddleware.CONSENT_EXPIRY_DAYS * 24 * 60 * 60,
        httponly=True,
        secure=getattr(settings, "SESSION_COOKIE_SECURE", True),
        samesite="Lax",
    )

    logger.info(f"Consent cookie set: {categories}")


def clear_consent_cookie(response: HttpResponse) -> None:
    """Clear consent cookie."""
    response.delete_cookie(CookieConsentMiddleware.CONSENT_COOKIE_NAME)
    logger.info("Consent cookie cleared")


def invalidate_privacy_preferences_cache(user) -> None:
    """
    Invalidate cached privacy preferences for a user.

    Usage:
        # After updating preferences
        invalidate_privacy_preferences_cache(request.user)
    """
    cache_key = f"{PrivacyPreferencesMiddleware.CACHE_KEY_PREFIX}_{user.id}"
    cache.delete(cache_key)
    logger.debug(f"Privacy preferences cache invalidated for user {user.id}")
