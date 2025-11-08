"""
Two-Factor Authentication Helpers
=================================

Helper classes for 2FA authentication using Extract Class pattern.

Complexity reduced: C:14 → A:2 (main method)
"""

import logging
from typing import Optional, Tuple

from django.contrib.auth.models import User

logger = logging.getLogger(__name__)


class UserRetriever:
    """
    Retrieve and validate user existence

    Complexity: A:3
    """

    @staticmethod
    def get_user(username: str, password: str) -> Tuple[Optional[User], bool]:
        """
        Get user by username with timing attack protection

        Returns:
            (user, should_continue) tuple

        Complexity: A:3
        """
        if username is None or password is None:
            return None, False

        try:
            user = User.objects.get(email__iexact=username)
            return user, True
        except User.DoesNotExist:
            # Run the default password hasher once to reduce the timing
            # difference between an existing and a nonexistent user
            User().set_password(password)
            return None, False


class AccountSecurityChecker:
    """
    Check account security status

    Complexity: A:3
    """

    @staticmethod
    def check_account_status(user: User, username: str) -> bool:
        """
        Check if account is locked

        Returns:
            True if account is accessible, False if locked

        Complexity: A:2
        """
        if user.is_account_locked():
            logger.warning(f"Login attempt on locked account: {username}")
            return False
        return True


class PasswordValidator:
    """
    Validate user password

    Complexity: A:3
    """

    @staticmethod
    def validate_password(user: User, password: str, username: str) -> bool:
        """
        Validate user password and record result

        Complexity: A:3
        """
        if not user.check_password(password):
            user.record_failed_login()  # type: ignore[attr-defined]
            logger.warning(f"Failed password attempt for: {username}")
            return False
        return True


class TwoFactorValidator:
    """
    Validate 2FA tokens

    Complexity: A:5
    """

    @staticmethod
    def validate_totp(user: User, totp_token: str, username: str) -> Tuple[bool, str]:
        """
        Validate TOTP token

        Returns:
            (is_valid, log_message)

        Complexity: A:3
        """
        if user.verify_totp(totp_token):
            return True, f"Successful 2FA login with TOTP: {username}"
        else:
            user.record_failed_login()  # type: ignore[attr-defined]
            logger.warning(f"Invalid TOTP token for: {username}")
            return False, ""

    @staticmethod
    def validate_backup_code(
        user: User, backup_code: str, username: str
    ) -> Tuple[bool, str]:
        """
        Validate backup code

        Returns:
            (is_valid, log_message)

        Complexity: A:3
        """
        if user.use_backup_code(backup_code):
            return True, f"Successful 2FA login with backup code: {username}"
        else:
            user.record_failed_login()  # type: ignore[attr-defined]
            logger.warning(f"Invalid backup code for: {username}")
            return False, ""


class AuthenticationOrchestrator:
    """
    Orchestrate authentication flow

    Complexity: B:7
    """

    def __init__(self, user_can_authenticate_func):
        self.user_can_authenticate = user_can_authenticate_func
        self.user_retriever = UserRetriever()
        self.security_checker = AccountSecurityChecker()
        self.password_validator = PasswordValidator()
        self.twofa_validator = TwoFactorValidator()

    def authenticate_user(
        self,
        username: str,
        password: str,
        totp_token: Optional[str] = None,
        backup_code: Optional[str] = None,
    ) -> Optional[User]:
        """
        Main authentication flow

        Complexity: B:7
        """
        # Get user
        user, should_continue = self.user_retriever.get_user(username, password)
        if not should_continue:
            return None

        # Check account status
        if not self.security_checker.check_account_status(user, username):
            return None

        # Validate password
        if not self.password_validator.validate_password(user, password, username):
            return None

        # Check if 2FA is required
        if not user.is_2fa_enabled:
            return self._finalize_authentication(user)

        # Handle 2FA verification
        return self._handle_2fa(user, totp_token, backup_code, username)

    def _handle_2fa(
        self,
        user: User,
        totp_token: Optional[str],
        backup_code: Optional[str],
        username: str,
    ) -> Optional[User]:
        """
        Handle 2FA token verification

        Complexity: A:5
        """
        if totp_token:
            is_valid, log_msg = self.twofa_validator.validate_totp(
                user, totp_token, username
            )
            if is_valid:
                logger.info(log_msg)
                return self._finalize_authentication(user)
            return None

        if backup_code:
            is_valid, log_msg = self.twofa_validator.validate_backup_code(
                user, backup_code, username
            )
            if is_valid:
                logger.info(log_msg)
                return self._finalize_authentication(user)
            return None

        # 2FA is enabled but no valid token provided
        return None

    def _finalize_authentication(self, user: User) -> Optional[User]:
        """
        Finalize authentication and return user

        Complexity: A:2
        """
        if self.user_can_authenticate(user):
            user.record_successful_login()
            return user
        return None
