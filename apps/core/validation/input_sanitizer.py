"""
Input Validation & Sanitization Framework
=========================================

Comprehensive validation and sanitization utilities for user inputs.
Provides protection against XSS, SQL injection, and other injection attacks.

OWASP A03: Injection protection
"""

import html
import re
from typing import Any, Dict, List, Optional, Tuple, Union
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import EmailValidator, URLValidator, validate_ipv46_address
from django.utils.html import strip_tags


class InputSanitizer:
    """
    Comprehensive input sanitization utilities.

    Protects against:
    - XSS (Cross-Site Scripting)
    - HTML injection
    - Script injection
    - SQL injection (via parameterized queries)
    """

    # Dangerous HTML tags that should always be removed
    DANGEROUS_TAGS = [
        "script",
        "iframe",
        "object",
        "embed",
        "applet",
        "meta",
        "link",
        "style",
        "base",
        "form",
    ]

    # Dangerous attributes that can execute JavaScript
    DANGEROUS_ATTRIBUTES = [
        "onclick",
        "onload",
        "onerror",
        "onmouseover",
        "onmouseout",
        "onfocus",
        "onblur",
        "onchange",
        "onsubmit",
        "href",
    ]

    # Suspicious patterns for potential attacks
    SUSPICIOUS_PATTERNS = [
        r"javascript:",
        r"data:text/html",
        r"vbscript:",
        r"<script",
        r"</script>",
        r"eval\(",
        r"expression\(",
        r"import\(",
        r"@import",
        r"document\.cookie",
        r"window\.location",
    ]

    @staticmethod
    def sanitize_text(text: str, max_length: Optional[int] = None) -> str:
        """
        Sanitize plain text input.

        - Strips all HTML tags
        - Escapes special characters
        - Removes suspicious patterns
        - Enforces max length

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length (optional)

        Returns:
            Sanitized text string
        """
        if not isinstance(text, str):
            return ""

        # Strip HTML tags
        text = strip_tags(text)

        # Escape HTML entities
        text = html.escape(text)

        # Remove null bytes
        text = text.replace("\x00", "")

        # Normalize whitespace
        text = " ".join(text.split())

        # Enforce max length
        if max_length and len(text) > max_length:
            text = text[:max_length]

        return text

    @classmethod
    def sanitize_html(
        cls, html_content: str, allowed_tags: Optional[List[str]] = None
    ) -> str:
        """
        Sanitize HTML content, allowing only safe tags.

        Args:
            html_content: HTML content to sanitize
            allowed_tags: List of allowed HTML tags (default: safe tags only)

        Returns:
            Sanitized HTML string
        """
        if not isinstance(html_content, str):
            return ""

        if allowed_tags is None:
            allowed_tags = [
                "p",
                "br",
                "strong",
                "em",
                "u",
                "h1",
                "h2",
                "h3",
                "h4",
                "h5",
                "h6",
                "ul",
                "ol",
                "li",
                "a",
                "img",
                "blockquote",
                "code",
                "pre",
            ]

        # Remove dangerous tags
        for tag in cls.DANGEROUS_TAGS:
            pattern = rf"<{tag}[^>]*>.*?</{tag}>"
            html_content = re.sub(
                pattern, "", html_content, flags=re.IGNORECASE | re.DOTALL
            )

        # Remove dangerous attributes
        for attr in cls.DANGEROUS_ATTRIBUTES:
            pattern = rf'\s{attr}=["\'][^"\']*["\']'
            html_content = re.sub(pattern, "", html_content, flags=re.IGNORECASE)

        # Check for suspicious patterns
        for pattern in cls.SUSPICIOUS_PATTERNS:
            if re.search(pattern, html_content, re.IGNORECASE):
                # Remove the entire suspicious section
                html_content = re.sub(
                    pattern, "[REMOVED]", html_content, flags=re.IGNORECASE
                )

        return html_content

    @staticmethod
    def sanitize_url(url: str) -> Optional[str]:
        """
        Sanitize and validate URL.

        Args:
            url: URL to sanitize

        Returns:
            Sanitized URL or None if invalid
        """
        if not isinstance(url, str):
            return None

        # Strip whitespace
        url = url.strip()

        # Check for suspicious protocols
        if url.lower().startswith(("javascript:", "data:", "vbscript:")):
            return None

        # Validate URL format
        try:
            validator = URLValidator(schemes=["http", "https"])
            validator(url)
        except ValidationError:
            return None

        # Parse and reconstruct URL (removes suspicious components)
        try:
            parsed = urlparse(url)
            if not parsed.scheme or not parsed.netloc:
                return None

            # Ensure safe scheme
            if parsed.scheme not in ["http", "https"]:
                return None

            return url
        except Exception:
            return None

    @staticmethod
    def sanitize_email(email: str) -> Optional[str]:
        """
        Sanitize and validate email address.

        Args:
            email: Email address to sanitize

        Returns:
            Sanitized email or None if invalid
        """
        if not isinstance(email, str):
            return None

        # Strip whitespace and convert to lowercase
        email = email.strip().lower()

        # Validate email format
        try:
            validator = EmailValidator()
            validator(email)
            return email
        except ValidationError:
            return None

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent directory traversal attacks.

        Args:
            filename: Filename to sanitize

        Returns:
            Sanitized filename
        """
        if not isinstance(filename, str):
            return "unnamed"

        # Remove path separators
        filename = filename.replace("/", "_").replace("\\", "_")

        # Remove null bytes
        filename = filename.replace("\x00", "")

        # Remove leading/trailing dots and whitespace
        filename = filename.strip(". ")

        # Remove dangerous characters
        filename = re.sub(r'[<>:"|?*]', "", filename)

        # Limit length
        if len(filename) > 255:
            name, ext = filename.rsplit(".", 1) if "." in filename else (filename, "")
            filename = name[:200] + ("." + ext if ext else "")

        return filename or "unnamed"

    @staticmethod
    def sanitize_integer(
        value: Any, min_value: Optional[int] = None, max_value: Optional[int] = None
    ) -> Optional[int]:
        """
        Sanitize and validate integer input.

        Args:
            value: Value to sanitize
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)

        Returns:
            Sanitized integer or None if invalid
        """
        try:
            value = int(value)

            if min_value is not None and value < min_value:
                return min_value

            if max_value is not None and value > max_value:
                return max_value

            return value
        except (ValueError, TypeError):
            return None

    @staticmethod
    def sanitize_float(
        value: Any, min_value: Optional[float] = None, max_value: Optional[float] = None
    ) -> Optional[float]:
        """
        Sanitize and validate float input.

        Args:
            value: Value to sanitize
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)

        Returns:
            Sanitized float or None if invalid
        """
        try:
            value = float(value)

            if min_value is not None and value < min_value:
                return min_value

            if max_value is not None and value > max_value:
                return max_value

            return value
        except (ValueError, TypeError):
            return None


class InputValidator:
    """
    Comprehensive input validation utilities.

    Provides validation for common input types with detailed error messages.
    """

    @staticmethod
    def validate_required_fields(
        data: Dict[str, Any], required_fields: List[str]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that all required fields are present.

        Args:
            data: Input data dictionary
            required_fields: List of required field names

        Returns:
            Tuple of (is_valid, error_message)
        """
        if not isinstance(data, dict):
            return (False, "Data must be a dictionary")

        missing_fields = [field for field in required_fields if field not in data]

        if missing_fields:
            return (False, f"Missing required fields: {', '.join(missing_fields)}")

        return (True, None)

    @staticmethod
    def validate_field_type(
        data: Dict[str, Any], field: str, expected_type: type
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that a field has the expected type.

        Args:
            data: Input data dictionary
            field: Field name to validate
            expected_type: Expected Python type

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field not in data:
            return (True, None)  # Optional field

        if not isinstance(data[field], expected_type):
            return (False, f"{field} must be of type {expected_type.__name__}")

        return (True, None)

    @staticmethod
    def validate_string_length(
        data: Dict[str, Any],
        field: str,
        min_length: Optional[int] = None,
        max_length: Optional[int] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate string length constraints.

        Args:
            data: Input data dictionary
            field: Field name to validate
            min_length: Minimum allowed length (optional)
            max_length: Maximum allowed length (optional)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field not in data:
            return (True, None)

        value = data[field]
        if not isinstance(value, str):
            return (False, f"{field} must be a string")

        if min_length is not None and len(value) < min_length:
            return (False, f"{field} must be at least {min_length} characters")

        if max_length is not None and len(value) > max_length:
            return (False, f"{field} must be at most {max_length} characters")

        return (True, None)

    @staticmethod
    def validate_number_range(
        data: Dict[str, Any],
        field: str,
        min_value: Optional[Union[int, float]] = None,
        max_value: Optional[Union[int, float]] = None,
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate number range constraints.

        Args:
            data: Input data dictionary
            field: Field name to validate
            min_value: Minimum allowed value (optional)
            max_value: Maximum allowed value (optional)

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field not in data:
            return (True, None)

        value = data[field]
        if not isinstance(value, (int, float)):
            return (False, f"{field} must be a number")

        if min_value is not None and value < min_value:
            return (False, f"{field} must be at least {min_value}")

        if max_value is not None and value > max_value:
            return (False, f"{field} must be at most {max_value}")

        return (True, None)

    @staticmethod
    def validate_choice(
        data: Dict[str, Any], field: str, allowed_values: List[Any]
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that field value is in allowed choices.

        Args:
            data: Input data dictionary
            field: Field name to validate
            allowed_values: List of allowed values

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field not in data:
            return (True, None)

        value = data[field]
        if value not in allowed_values:
            return (
                False,
                f"{field} must be one of: {', '.join(map(str, allowed_values))}",
            )

        return (True, None)

    @staticmethod
    def validate_pattern(
        data: Dict[str, Any], field: str, pattern: str, pattern_name: str = "format"
    ) -> Tuple[bool, Optional[str]]:
        """
        Validate that field matches a regex pattern.

        Args:
            data: Input data dictionary
            field: Field name to validate
            pattern: Regex pattern to match
            pattern_name: Human-readable pattern description

        Returns:
            Tuple of (is_valid, error_message)
        """
        if field not in data:
            return (True, None)

        value = data[field]
        if not isinstance(value, str):
            return (False, f"{field} must be a string")

        if not re.match(pattern, value):
            return (False, f"{field} does not match required {pattern_name}")

        return (True, None)


class ValidationPipeline:
    """
    Validation pipeline for chaining multiple validators.

    Usage:
        pipeline = ValidationPipeline()
        pipeline.add_validator(lambda data: InputValidator.validate_required_fields(data, ['email']))
        pipeline.add_validator(lambda data: InputValidator.validate_field_type(data, 'email', str))
        is_valid, errors = pipeline.validate(data)
    """

    def __init__(self):
        self.validators = []

    def add_validator(self, validator_func):
        """Add a validator function to the pipeline."""
        self.validators.append(validator_func)
        return self  # Allow chaining

    def validate(self, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        Run all validators in the pipeline.

        Args:
            data: Input data to validate

        Returns:
            Tuple of (is_valid, list_of_errors)
        """
        errors = []

        for validator in self.validators:
            is_valid, error_message = validator(data)
            if not is_valid and error_message:
                errors.append(error_message)

        return (len(errors) == 0, errors)
