"""
API Authentication Views
=======================

JWT token management endpoints:
- Token obtain (login)
- Token refresh
- Token blacklist (logout)
- API key management
"""

import logging
from typing import Any, Dict

from django.contrib.auth import authenticate
from django.utils.translation import gettext_lazy as _

from rest_framework import status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.core.auth.jwt_backend import JWTTokenManager
from apps.core.models.api_key import APIKey

logger = logging.getLogger(__name__)


@api_view(["POST"])
@permission_classes([AllowAny])
def token_obtain(request) -> Response:
    """
    Obtain JWT tokens (login)

    POST /api/v1/auth/token/
    Body: {"username": "...", "password": "..."}
    Returns: {"access": "...", "refresh": "...", "access_expires_in": 900, "refresh_expires_in": 604800}
    """
    username = request.data.get("username")
    password = request.data.get("password")

    if not username or not password:
        return Response(
            {"error": "Username and password are required"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    # Authenticate user
    user = authenticate(request, username=username, password=password)

    if user is None:
        logger.warning(
            f"Failed login attempt for username: {username} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return Response(
            {"error": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED
        )

    if not user.is_active:
        return Response(
            {"error": "User account is disabled"}, status=status.HTTP_403_FORBIDDEN
        )

    # Generate tokens
    tokens = JWTTokenManager.create_tokens_for_user(user)

    logger.info(
        f"JWT tokens issued for user {user.username} "
        f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
    )

    return Response(tokens, status=status.HTTP_200_OK)


@api_view(["POST"])
@permission_classes([AllowAny])
def token_refresh(request) -> Response:
    """
    Refresh access token using refresh token

    POST /api/v1/auth/refresh/
    Body: {"refresh": "..."}
    Returns: {"access": "...", "refresh": "..." (if rotated), "access_expires_in": 900}
    """
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    try:
        tokens = JWTTokenManager.refresh_access_token(refresh_token)
        return Response(tokens, status=status.HTTP_200_OK)

    except Exception as e:
        logger.warning(
            f"Token refresh failed: {e} "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return Response(
            {"error": "Invalid or expired refresh token"},
            status=status.HTTP_401_UNAUTHORIZED,
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def token_blacklist(request) -> Response:
    """
    Blacklist refresh token (logout)

    POST /api/v1/auth/logout/
    Body: {"refresh": "..."}
    Returns: {"message": "Successfully logged out"}
    """
    refresh_token = request.data.get("refresh")

    if not refresh_token:
        return Response(
            {"error": "Refresh token is required"}, status=status.HTTP_400_BAD_REQUEST
        )

    # Blacklist token
    success = JWTTokenManager.blacklist_token(refresh_token)

    if success:
        logger.info(
            f"User {request.user.username} logged out "
            f"from {request.META.get('REMOTE_ADDR', 'unknown')}"
        )
        return Response(
            {"message": "Successfully logged out"}, status=status.HTTP_200_OK
        )
    else:
        return Response(
            {"error": "Failed to logout"}, status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def token_verify(request) -> Response:
    """
    Verify JWT token (check if valid)

    GET /api/v1/auth/verify/
    Headers: Authorization: Bearer <access_token>
    Returns: {"valid": true, "user": {...}}
    """
    return Response(
        {
            "valid": True,
            "user": {
                "id": request.user.id,
                "username": request.user.username,
                "email": request.user.email,
                "is_staff": request.user.is_staff,
            },
        },
        status=status.HTTP_200_OK,
    )


# API Key Management Views


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def api_key_list_create(request) -> Response:
    """
    List user's API keys or create new one

    GET /api/v1/api-keys/
    Returns: [{"id": 1, "name": "...", "key_prefix": "...", ...}, ...]

    POST /api/v1/api-keys/
    Body: {"name": "My API Key", "permissions": "read", "rate_limit": 1000, "expires_days": 90}
    Returns: {"key": "sk_...", "api_key": {...}}
    WARNING: The 'key' field is shown only once!
    """
    if request.method == "GET":
        # List user's API keys
        api_keys = APIKey.objects.filter(user=request.user, is_active=True)

        data = [
            {
                "id": key.id,
                "name": key.name,
                "key_prefix": key.key_prefix,
                "permissions": key.permissions,
                "rate_limit_per_hour": key.rate_limit_per_hour,
                "created_at": key.created_at.isoformat(),
                "last_used_at": (
                    key.last_used_at.isoformat() if key.last_used_at else None
                ),
                "expires_at": key.expires_at.isoformat() if key.expires_at else None,
                "usage_count": key.usage_count,
            }
            for key in api_keys
        ]

        return Response(data, status=status.HTTP_200_OK)

    elif request.method == "POST":
        # Create new API key
        name = request.data.get("name")
        permissions = request.data.get("permissions", "read")
        rate_limit = request.data.get("rate_limit", 1000)
        expires_days = request.data.get("expires_days")

        if not name:
            return Response(
                {"error": "Name is required"}, status=status.HTTP_400_BAD_REQUEST
            )

        # Validate permissions
        if permissions not in ["read", "write", "admin"]:
            return Response(
                {"error": "Invalid permissions. Must be: read, write, or admin"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Create API key
        result = APIKey.objects.create_key(
            user=request.user,
            name=name,
            permissions=permissions,
            rate_limit=rate_limit,
            expires_days=expires_days,
        )

        logger.info(f"API key created for user {request.user.username}: {name}")

        return Response(
            {
                "key": result["key"],  # Show only once!
                "api_key": {
                    "id": result["api_key"].id,
                    "name": result["api_key"].name,
                    "key_prefix": result["api_key"].key_prefix,
                    "permissions": result["api_key"].permissions,
                    "rate_limit_per_hour": result["api_key"].rate_limit_per_hour,
                    "expires_at": (
                        result["api_key"].expires_at.isoformat()
                        if result["api_key"].expires_at
                        else None
                    ),
                },
                "warning": "Save this key securely! It will not be shown again.",
            },
            status=status.HTTP_201_CREATED,
        )


@api_view(["GET", "DELETE"])
@permission_classes([IsAuthenticated])
def api_key_detail(request, key_id: int) -> Response:
    """
    Get or revoke specific API key

    GET /api/v1/api-keys/<id>/
    Returns: {"id": 1, "name": "...", ...}

    DELETE /api/v1/api-keys/<id>/
    Returns: {"message": "API key revoked"}
    """
    try:
        api_key = APIKey.objects.get(id=key_id, user=request.user)
    except APIKey.DoesNotExist:
        return Response(
            {"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND
        )

    if request.method == "GET":
        # Get API key details
        data = {
            "id": api_key.id,
            "name": api_key.name,
            "key_prefix": api_key.key_prefix,
            "permissions": api_key.permissions,
            "is_active": api_key.is_active,
            "rate_limit_per_hour": api_key.rate_limit_per_hour,
            "created_at": api_key.created_at.isoformat(),
            "last_used_at": (
                api_key.last_used_at.isoformat() if api_key.last_used_at else None
            ),
            "expires_at": (
                api_key.expires_at.isoformat() if api_key.expires_at else None
            ),
            "usage_count": api_key.usage_count,
        }

        return Response(data, status=status.HTTP_200_OK)

    elif request.method == "DELETE":
        # Revoke API key
        api_key.revoke()

        logger.info(f"API key revoked by user {request.user.username}: {api_key.name}")

        return Response({"message": "API key revoked"}, status=status.HTTP_200_OK)


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def api_key_usage(request, key_id: int) -> Response:
    """
    Get usage statistics for API key

    GET /api/v1/api-keys/<id>/usage/
    Returns: {"total_requests": 1234, "recent_usage": [...]}
    """
    try:
        api_key = APIKey.objects.get(id=key_id, user=request.user)
    except APIKey.DoesNotExist:
        return Response(
            {"error": "API key not found"}, status=status.HTTP_404_NOT_FOUND
        )

    # Get recent usage (last 100 requests)
    recent_usage = api_key.usage_logs.order_by("-timestamp")[:100]

    data = {
        "total_requests": api_key.usage_count,
        "recent_usage": [
            {
                "endpoint": log.endpoint,
                "ip_address": log.ip_address,
                "timestamp": log.timestamp.isoformat(),
            }
            for log in recent_usage
        ],
    }

    return Response(data, status=status.HTTP_200_OK)
