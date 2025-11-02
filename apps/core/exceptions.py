"""Custom exceptions for the application

This module defines custom exception classes for better error handling
and more specific error messages across the application.
"""

__all__ = [
    "AppBaseException",
    "ValidationError",
    "NotFoundError",
    "PermissionDeniedError",
    "AuthenticationError",
    "ConfigurationError",
    "ExternalServiceError",
]


class AppBaseException(Exception):
    """Base exception for all application-specific exceptions

    All custom exceptions should inherit from this class.
    Provides a consistent interface for error handling.
    """

    def __init__(self, message: str, code: str = None, details: dict = None):
        """Initialize exception

        Args:
            message: Human-readable error message
            code: Optional error code for API responses
            details: Optional additional error details
        """
        self.message = message
        self.code = code or self.__class__.__name__
        self.details = details or {}
        super().__init__(self.message)

    def to_dict(self) -> dict:
        """Convert exception to dictionary for API responses

        Returns:
            dict: Exception details as dictionary
        """
        return {
            "error": self.code,
            "message": self.message,
            "details": self.details,
        }


class ValidationError(AppBaseException):
    """Exception raised when data validation fails

    Use this when user input or data doesn't meet validation requirements.

    Examples:
        >>> raise ValidationError("Invalid email format", details={"field": "email"})
    """

    pass


class NotFoundError(AppBaseException):
    """Exception raised when a resource is not found

    Use this instead of Django's Http404 for API endpoints.

    Examples:
        >>> raise NotFoundError("Post not found", details={"post_id": 123})
    """

    pass


class PermissionDeniedError(AppBaseException):
    """Exception raised when user lacks required permissions

    Use this for authorization failures.

    Examples:
        >>> raise PermissionDeniedError("You don't have permission to edit this post")
    """

    pass


class AuthenticationError(AppBaseException):
    """Exception raised when authentication fails

    Use this for login failures, invalid tokens, etc.

    Examples:
        >>> raise AuthenticationError("Invalid credentials")
    """

    pass


class ConfigurationError(AppBaseException):
    """Exception raised when configuration is invalid or missing

    Use this for missing environment variables, invalid settings, etc.

    Examples:
        >>> raise ConfigurationError("REDIS_URL not configured")
    """

    pass


class ExternalServiceError(AppBaseException):
    """Exception raised when external service call fails

    Use this for third-party API failures, timeouts, etc.

    Examples:
        >>> raise ExternalServiceError(
        ...     "Spotify API timeout",
        ...     details={"service": "spotify", "timeout": 30}
        ... )
    """

    pass
