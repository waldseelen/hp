"""
JWT Authentication Backend for API Security
===========================================

Implements JSON Web Token authentication with:
- Access tokens (15 minutes)
- Refresh tokens (7 days) with rotation
- Token blacklist on logout
- Secure token validation
"""

import logging
from datetime import timedelta
from typing import Any, Dict, Optional

from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils.translation import gettext_lazy as _

from rest_framework import authentication, exceptions
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework_simplejwt.tokens import AccessToken, RefreshToken

User = get_user_model()
logger = logging.getLogger(__name__)


class CustomJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication with additional security checks
    """

    def authenticate(self, request):
        """
        Authenticate request with JWT token
        """
        header = self.get_header(request)
        if header is None:
            return None

        raw_token = self.get_raw_token(header)
        if raw_token is None:
            return None

        try:
            validated_token = self.get_validated_token(raw_token)
            user = self.get_user(validated_token)

            # Additional security checks
            if not user.is_active:
                raise exceptions.AuthenticationFailed(_("User account is disabled."))

            # Check if token is blacklisted
            if self._is_token_blacklisted(validated_token):
                raise exceptions.AuthenticationFailed(_("Token has been revoked."))

            # Log successful authentication
            logger.info(
                f"JWT authentication successful for user {user.username} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            return (user, validated_token)

        except TokenError as e:
            logger.warning(
                f"JWT authentication failed: {e} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )
            raise exceptions.AuthenticationFailed(_("Invalid or expired token."))

    def _is_token_blacklisted(self, token) -> bool:
        """
        Check if token is in blacklist
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            jti = token.get("jti")
            if jti:
                return BlacklistedToken.objects.filter(token__jti=jti).exists()
        except Exception:  # nosec B110 - Token blacklist optional, graceful degradation
            # Token blacklist not configured - skip check
            pass

        return False


class JWTTokenManager:
    """
    Manager for JWT token operations
    """

    @staticmethod
    def create_tokens_for_user(user) -> Dict[str, str]:
        """
        Create access and refresh tokens for user
        """
        refresh = RefreshToken.for_user(user)

        # Add custom claims
        refresh["username"] = user.username
        refresh["email"] = user.email
        refresh["is_staff"] = user.is_staff

        return {
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "access_expires_in": int(
                settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
            ),
            "refresh_expires_in": int(
                settings.SIMPLE_JWT["REFRESH_TOKEN_LIFETIME"].total_seconds()
            ),
        }

    @staticmethod
    def refresh_access_token(refresh_token: str) -> Dict[str, str]:
        """
        Refresh access token using refresh token

        With token rotation, the refresh token is also rotated
        """
        try:
            refresh = RefreshToken(refresh_token)

            # Rotate refresh token if configured
            if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False):
                refresh.set_jti()
                refresh.set_exp()

            return {
                "access": str(refresh.access_token),
                "refresh": (
                    str(refresh)
                    if settings.SIMPLE_JWT.get("ROTATE_REFRESH_TOKENS", False)
                    else refresh_token
                ),
                "access_expires_in": int(
                    settings.SIMPLE_JWT["ACCESS_TOKEN_LIFETIME"].total_seconds()
                ),
            }

        except TokenError as e:
            logger.warning(f"Token refresh failed: {e}")
            raise exceptions.AuthenticationFailed(
                _("Invalid or expired refresh token.")
            )

    @staticmethod
    def blacklist_token(refresh_token: str) -> bool:
        """
        Blacklist refresh token (logout)
        """
        try:
            from rest_framework_simplejwt.token_blacklist.models import (
                BlacklistedToken,
                OutstandingToken,
            )

            token = RefreshToken(refresh_token)
            jti = token.get("jti")

            if jti:
                outstanding_token = OutstandingToken.objects.filter(jti=jti).first()

                if outstanding_token:
                    BlacklistedToken.objects.get_or_create(token=outstanding_token)
                    logger.info(f"Token {jti} blacklisted successfully")
                    return True

        except Exception as e:
            logger.error(f"Token blacklist failed: {e}")
            return False

        return False

    @staticmethod
    def validate_token(
        token: str, token_type: str = "access"
    ) -> Dict[str, Any]:  # nosec B107 - Token type identifier, not a password
        """
        Validate token and return payload
        """
        try:
            if token_type == "access":  # nosec B105 - Token type string, not a password
                validated_token = AccessToken(token)
            else:
                validated_token = RefreshToken(token)

            return dict(validated_token.payload)

        except TokenError as e:
            logger.warning(f"Token validation failed: {e}")
            raise exceptions.AuthenticationFailed(_("Invalid or expired token."))


class APIKeyAuthentication(authentication.BaseAuthentication):
    """
    API Key authentication for server-to-server communication
    """

    keyword = "Api-Key"

    def authenticate(self, request):
        """
        Authenticate using API key from header
        """
        api_key = request.META.get("HTTP_X_API_KEY") or request.GET.get("api_key")

        if not api_key:
            return None

        try:
            from apps.core.models.api_key import APIKey

            # Validate API key
            api_key_obj = APIKey.objects.get_from_key(api_key)

            if not api_key_obj:
                raise exceptions.AuthenticationFailed(_("Invalid API key"))

            if not api_key_obj.is_active:
                raise exceptions.AuthenticationFailed(_("API key is disabled"))

            if api_key_obj.is_expired:
                raise exceptions.AuthenticationFailed(_("API key has expired"))

            # Check rate limits
            if not api_key_obj.check_rate_limit():
                raise exceptions.Throttled(detail=_("API key rate limit exceeded"))

            # Update usage stats
            api_key_obj.record_usage(
                endpoint=request.path,
                ip_address=request.META.get("REMOTE_ADDR", "unknown"),
            )

            logger.info(
                f"API key authentication successful for {api_key_obj.name} "
                f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
            )

            return (api_key_obj.user, api_key_obj)

        except APIKey.DoesNotExist:
            raise exceptions.AuthenticationFailed(_("Invalid API key"))
        except Exception as e:
            logger.error(f"API key authentication error: {e}")
            raise exceptions.AuthenticationFailed(_("Authentication failed"))


# JWT Settings Configuration (add to settings.py)
JWT_SETTINGS = {
    "ACCESS_TOKEN_LIFETIME": timedelta(minutes=15),
    "REFRESH_TOKEN_LIFETIME": timedelta(days=7),
    "ROTATE_REFRESH_TOKENS": True,
    "BLACKLIST_AFTER_ROTATION": True,
    "UPDATE_LAST_LOGIN": True,
    "ALGORITHM": "HS256",
    "SIGNING_KEY": settings.SECRET_KEY,
    "VERIFYING_KEY": None,
    "AUDIENCE": None,
    "ISSUER": None,
    "AUTH_HEADER_TYPES": ("Bearer",),
    "AUTH_HEADER_NAME": "HTTP_AUTHORIZATION",
    "USER_ID_FIELD": "id",
    "USER_ID_CLAIM": "user_id",
    "AUTH_TOKEN_CLASSES": ("rest_framework_simplejwt.tokens.AccessToken",),
    "TOKEN_TYPE_CLAIM": "token_type",
    "JTI_CLAIM": "jti",
    "SLIDING_TOKEN_REFRESH_EXP_CLAIM": "refresh_exp",
    "SLIDING_TOKEN_LIFETIME": timedelta(minutes=5),
    "SLIDING_TOKEN_REFRESH_LIFETIME": timedelta(days=1),
}
