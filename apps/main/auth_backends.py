"""
Restricted authentication backend for admin-only access.

- Allows login only for a single configured admin email
  using a securely hashed password from environment.
- Ensures session-based authentication remains intact.
"""

from typing import Optional

from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model
from django.contrib.auth.hashers import check_password
from django.utils import timezone
from decouple import config


User = get_user_model()


class RestrictedAdminBackend(BaseBackend):
    """Authenticate only the configured admin account.

    Environment variables:
      - ALLOWED_ADMIN_EMAIL
      - ALLOWED_ADMIN_PASSWORD_HASH (Django-compatible hash)
    """

    def authenticate(
        self,
        request,
        username: Optional[str] = None,
        password: Optional[str] = None,
        **kwargs,
    ):
        if not username or not password:
            return None

        allowed_email = config("ALLOWED_ADMIN_EMAIL", default="").strip()
        allowed_hash = config("ALLOWED_ADMIN_PASSWORD_HASH", default="").strip()

        # Hard stop if not configured
        if not allowed_email or not allowed_hash:
            return None

        # Only allow the configured email (case-insensitive)
        if username.lower() != allowed_email.lower():
            return None

        # Verify password using the stored hash
        if not check_password(password, allowed_hash):
            return None

        # Ensure user exists (create if missing) and has proper flags
        defaults = {
            "email": allowed_email,
            "username": allowed_email.split("@")[0][:150],
            "is_active": True,
            "is_staff": True,
            "is_superuser": True,
            "last_login": timezone.now(),
        }
        # Add optional 'name' if model supports it
        try:
            field_names = {f.name for f in User._meta.get_fields()}
        except Exception:
            field_names = set()
        if "name" in field_names:
            defaults["name"] = allowed_email.split("@")[0]

        user, created = User.objects.get_or_create(
            email__iexact=allowed_email,
            defaults=defaults,
        )

        update_fields: list[str] = []

        if created:
            # Ensure the database record cannot be used for password auth
            user.set_unusable_password()
            update_fields.append("password")
        else:
            canonical_username = defaults["username"]
            if user.username != canonical_username:
                user.username = canonical_username
                update_fields.append("username")
            if user.email != allowed_email:
                user.email = allowed_email
                update_fields.append("email")

        for flag in ("is_active", "is_staff", "is_superuser"):
            if not getattr(user, flag):
                setattr(user, flag, True)
                update_fields.append(flag)

        if not created and user.has_usable_password():
            user.set_unusable_password()
            update_fields.append("password")

        if update_fields:
            # dict preserves order since Python 3.7; ensures unique field names
            unique_fields = list(dict.fromkeys(update_fields))
            user.save(update_fields=unique_fields)

        return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None


# Backwards-compatibility helpers for any code importing from apps.main.auth_backends
def get_client_ip(request):
    x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
    if x_forwarded_for:
        return x_forwarded_for.split(",")[0].strip()
    return request.META.get("REMOTE_ADDR", "127.0.0.1")


def get_device_info(request):
    ua = request.META.get("HTTP_USER_AGENT", "")
    if "Mobile" in ua or "Android" in ua:
        device_type = "Mobile"
    elif "Tablet" in ua or "iPad" in ua:
        device_type = "Tablet"
    else:
        device_type = "Desktop"

    if "Chrome" in ua:
        browser = "Chrome"
    elif "Firefox" in ua:
        browser = "Firefox"
    elif "Safari" in ua:
        browser = "Safari"
    elif "Edge" in ua:
        browser = "Edge"
    else:
        browser = "Unknown"

    return {"device_type": device_type, "browser": browser, "user_agent": ua}
