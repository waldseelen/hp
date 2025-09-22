"""
Custom Authentication Backends
=============================

Enhanced authentication with 2FA support and security features.
"""

from django.contrib.auth.backends import ModelBackend
from django.contrib.auth import get_user_model
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
User = get_user_model()


class TwoFactorAuthBackend(ModelBackend):
    """
    Custom authentication backend with 2FA support and security features
    """

    def authenticate(self, request, username=None, password=None, totp_token=None, backup_code=None, **kwargs):
        """
        Authenticate user with optional 2FA verification

        Args:
            request: HTTP request
            username: User's email
            password: User's password
            totp_token: TOTP token for 2FA
            backup_code: Backup recovery code

        Returns:
            User instance if authentication successful, None otherwise
        """
        if username is None or password is None:
            return None

        try:
            # Get user by email (username field)
            user = User.objects.get(email__iexact=username)
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None

        # Check if account is locked
        if user.is_account_locked():
            logger.warning(f"Login attempt on locked account: {username}")
            return None

        # Verify password
        if not user.check_password(password):
            user.record_failed_login()
            logger.warning(f"Failed password attempt for: {username}")
            return None

        # If 2FA is not enabled, proceed with normal authentication
        if not user.is_2fa_enabled:
            if self.user_can_authenticate(user):
                user.record_successful_login()
                return user
            return None

        # 2FA is enabled - verify TOTP token or backup code
        if totp_token:
            if user.verify_totp(totp_token):
                if self.user_can_authenticate(user):
                    user.record_successful_login()
                    logger.info(f"Successful 2FA login with TOTP: {username}")
                    return user
            else:
                user.record_failed_login()
                logger.warning(f"Invalid TOTP token for: {username}")
                return None

        elif backup_code:
            if user.use_backup_code(backup_code):
                if self.user_can_authenticate(user):
                    user.record_successful_login()
                    logger.info(f"Successful 2FA login with backup code: {username}")
                    return user
            else:
                user.record_failed_login()
                logger.warning(f"Invalid backup code for: {username}")
                return None

        # 2FA is enabled but no valid token provided
        return None

    def get_user(self, user_id):
        """Get user by ID"""
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return None
        return user if self.user_can_authenticate(user) else None


class SessionTrackingMixin:
    """
    Mixin for tracking user sessions
    """

    def create_session(self, request, user):
        """Create or update user session tracking"""
        from apps.main.models import UserSession

        session_key = request.session.session_key
        if not session_key:
            request.session.create()
            session_key = request.session.session_key

        # Get client IP
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            ip_address = x_forwarded_for.split(',')[0].strip()
        else:
            ip_address = request.META.get('REMOTE_ADDR', '127.0.0.1')

        user_agent = request.META.get('HTTP_USER_AGENT', '')

        # Create or update session
        session, created = UserSession.objects.get_or_create(
            session_key=session_key,
            defaults={
                'user': user,
                'ip_address': ip_address,
                'user_agent': user_agent,
                'last_activity': timezone.now(),
            }
        )

        if not created:
            # Update existing session
            session.last_activity = timezone.now()
            session.is_active = True
            session.save(update_fields=['last_activity', 'is_active'])

        return session

    def deactivate_session(self, session_key):
        """Deactivate a session"""
        from apps.main.models import UserSession

        try:
            session = UserSession.objects.get(session_key=session_key)
            session.deactivate()
        except UserSession.DoesNotExist:
            pass


class SecureAuthBackend(TwoFactorAuthBackend, SessionTrackingMixin):
    """
    Complete secure authentication backend with 2FA and session tracking
    """

    def authenticate(self, request, **kwargs):
        """Enhanced authenticate with session tracking"""
        user = super().authenticate(request, **kwargs)

        if user and request:
            # Create session tracking
            self.create_session(request, user)

            # Log successful authentication
            logger.info(f"Successful authentication: {user.email} from {request.META.get('REMOTE_ADDR', 'unknown')}")

        return user


def get_client_ip(request):
    """Get client IP address from request"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


def get_device_info(request):
    """Extract device information from request"""
    user_agent = request.META.get('HTTP_USER_AGENT', '')

    # Simple device detection
    if 'Mobile' in user_agent or 'Android' in user_agent:
        device_type = 'Mobile'
    elif 'Tablet' in user_agent or 'iPad' in user_agent:
        device_type = 'Tablet'
    else:
        device_type = 'Desktop'

    # Browser detection
    if 'Chrome' in user_agent:
        browser = 'Chrome'
    elif 'Firefox' in user_agent:
        browser = 'Firefox'
    elif 'Safari' in user_agent:
        browser = 'Safari'
    elif 'Edge' in user_agent:
        browser = 'Edge'
    else:
        browser = 'Unknown'

    return {
        'device_type': device_type,
        'browser': browser,
        'user_agent': user_agent
    }