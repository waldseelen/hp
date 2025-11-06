"""
Input Validation and Sanitization Utilities
==========================================

Comprehensive validation and sanitization functions for user inputs.
Provides protection against XSS, injection attacks, and malicious content.
"""

import mimetypes
import os
import re
from typing import Any, Dict, List

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator
from django.utils.html import strip_tags

# Optional import for file type detection
try:
    import magic

    MAGIC_AVAILABLE = True
except ImportError:
    MAGIC_AVAILABLE = False


class InputSanitizer:
    """Comprehensive input sanitization utilities"""

    @staticmethod
    def sanitize_text(
        text: str, max_length: int = 1000, allow_html: bool = False
    ) -> str:
        """
        Sanitize text input with comprehensive filtering

        Args:
            text: Input text to sanitize
            max_length: Maximum allowed length
            allow_html: Whether to allow basic HTML tags

        Returns:
            Sanitized text string
        """
        if not isinstance(text, str):
            text = str(text)

        # Remove null bytes and control characters
        text = text.replace("\x00", "").replace("\r", "")

        # Strip HTML if not allowed
        if not allow_html:
            text = strip_tags(text)
        else:
            # Allow only safe HTML tags
            pass
            # This is a simplified implementation - in production use bleach library
            import html

            text = html.escape(text)

        # Normalize whitespace
        text = re.sub(r"\s+", " ", text).strip()

        # Truncate if too long
        if len(text) > max_length:
            text = text[:max_length].rstrip() + "..."

        return text

    @staticmethod
    def sanitize_filename(filename: str) -> str:
        """
        Sanitize filename to prevent path traversal and other attacks

        Args:
            filename: Original filename

        Returns:
            Sanitized filename
        """
        if not filename:
            return "unnamed_file"

        # Remove path components
        filename = os.path.basename(filename)

        # Remove dangerous characters
        filename = re.sub(r"[^\w\s.-]", "", filename)

        # Remove leading dots and spaces
        filename = filename.lstrip(". ")

        # Ensure not empty
        if not filename:
            filename = "unnamed_file"

        # Limit length
        if len(filename) > 100:
            name, ext = os.path.splitext(filename)
            filename = name[:95] + ext

        return filename

    @staticmethod
    def validate_and_sanitize_url(url: str) -> str:
        """
        Validate and sanitize URL input

        Args:
            url: URL to validate

        Returns:
            Sanitized URL

        Raises:
            ValidationError: If URL is invalid or malicious
        """
        if not url:
            raise ValidationError("URL is required")

        # Basic sanitization
        url = url.strip()

        # Check for dangerous protocols
        dangerous_protocols = ["javascript:", "data:", "vbscript:", "file:", "ftp:"]
        for protocol in dangerous_protocols:
            if url.lower().startswith(protocol):
                raise ValidationError(f"Protocol {protocol} is not allowed")

        # Ensure HTTPS for external URLs
        if not url.startswith(("http://", "https://", "/")):
            url = "https://" + url

        # Validate URL format
        validator = URLValidator()
        try:
            validator(url)
        except ValidationError:
            raise ValidationError("Invalid URL format")

        return url


class FileTypeValidator:
    """File type validation and security checks"""

    ALLOWED_IMAGE_TYPES = {
        "image/jpeg": [".jpg", ".jpeg"],
        "image/png": [".png"],
        "image/gif": [".gif"],
        "image/webp": [".webp"],
        "image/svg+xml": [".svg"],
    }

    ALLOWED_DOCUMENT_TYPES = {
        "application/pdf": [".pdf"],
        "text/plain": [".txt"],
        "application/msword": [".doc"],
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document": [
            ".docx"
        ],
    }

    MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB

    @classmethod
    def validate_file_type(
        cls, file, allowed_types: Dict[str, List[str]] = None
    ) -> bool:
        """
        Validate file type using both extension and MIME type

        Args:
            file: Uploaded file object
            allowed_types: Dictionary of allowed MIME types and extensions

        Returns:
            True if file type is valid

        Raises:
            ValidationError: If file type is not allowed
        """
        if allowed_types is None:
            allowed_types = {**cls.ALLOWED_IMAGE_TYPES, **cls.ALLOWED_DOCUMENT_TYPES}

        # Check file size
        if hasattr(file, "size") and file.size > cls.MAX_FILE_SIZE:
            raise ValidationError(
                f"File size too large. Maximum allowed: {cls.MAX_FILE_SIZE // (1024 * 1024)}MB"
            )

        # Get file extension
        filename = getattr(file, "name", "")
        if not filename:
            raise ValidationError("Filename is required")

        _, ext = os.path.splitext(filename.lower())

        # Check MIME type
        try:
            # Try to read MIME type from file content if magic is available
            if MAGIC_AVAILABLE and hasattr(file, "read"):
                file.seek(0)
                file_content = file.read(1024)  # Read first 1KB
                file.seek(0)  # Reset file pointer

                mime_type = magic.from_buffer(file_content, mime=True)
            else:
                # Fallback to filename-based detection
                mime_type, _ = mimetypes.guess_type(filename)
        except (ImportError, AttributeError, Exception):
            # If magic library fails or is not available, use mimetypes
            mime_type, _ = mimetypes.guess_type(filename)

        # Validate MIME type and extension
        if mime_type not in allowed_types:
            raise ValidationError(f"File type {mime_type} is not allowed")

        if ext not in allowed_types[mime_type]:
            raise ValidationError(
                f"File extension {ext} does not match MIME type {mime_type}"
            )

        return True

    @classmethod
    def validate_image_file(cls, file) -> bool:
        """Validate image file specifically"""
        return cls.validate_file_type(file, cls.ALLOWED_IMAGE_TYPES)

    @classmethod
    def validate_document_file(cls, file) -> bool:
        """Validate document file specifically"""
        return cls.validate_file_type(file, cls.ALLOWED_DOCUMENT_TYPES)


class SecureFileValidator:
    """Advanced file security validation"""

    DANGEROUS_EXTENSIONS = [
        ".exe",
        ".bat",
        ".cmd",
        ".com",
        ".pif",
        ".scr",
        ".vbs",
        ".js",
        ".jar",
        ".php",
        ".asp",
        ".jsp",
        ".py",
        ".pl",
        ".sh",
        ".ps1",
    ]

    @staticmethod
    def scan_for_malicious_content(file) -> bool:
        """
        Scan file for potentially malicious content

        Args:
            file: File object to scan

        Returns:
            True if file appears safe

        Raises:
            ValidationError: If malicious content is detected
        """
        if not hasattr(file, "read"):
            return True

        try:
            file.seek(0)
            content = file.read(8192)  # Read first 8KB
            file.seek(0)  # Reset file pointer

            # Convert to string for analysis
            try:
                content_str = content.decode("utf-8", errors="ignore")
            except (AttributeError, UnicodeDecodeError):
                content_str = str(content)

            # Check for dangerous patterns
            dangerous_patterns = [
                r"<script[^>]*>",
                r"javascript:",
                r"vbscript:",
                r"onload\s*=",
                r"onerror\s*=",
                r"eval\s*\(",
                r"document\.write",
                r"innerHTML\s*=",
                r"<iframe[^>]*>",
                r"<object[^>]*>",
                r"<embed[^>]*>",
            ]

            for pattern in dangerous_patterns:
                if re.search(pattern, content_str, re.IGNORECASE):
                    raise ValidationError("File contains potentially malicious content")

            return True

        except Exception as e:
            if isinstance(e, ValidationError):
                raise
            # If we can't read the file, err on the side of caution
            raise ValidationError("Unable to validate file security")

    @classmethod
    def validate_file_security(cls, file) -> bool:
        """
        Comprehensive file security validation

        Args:
            file: File object to validate

        Returns:
            True if file passes all security checks
        """
        filename = getattr(file, "name", "")

        # Check for dangerous extensions
        _, ext = os.path.splitext(filename.lower())
        if ext in cls.DANGEROUS_EXTENSIONS:
            raise ValidationError(
                f"File extension {ext} is not allowed for security reasons"
            )

        # Scan content for malicious patterns
        cls.scan_for_malicious_content(file)

        return True


def _check_required_field(field, value, rules):
    """Check if required field is present."""
    if rules.get("required", False) and value is None:
        raise ValidationError(f"Field {field} is required")


def _validate_field_type(field, value, rules):
    """Validate and convert field type."""
    expected_type = rules.get("type", str)
    if not isinstance(value, expected_type):
        try:
            return expected_type(value)
        except (ValueError, TypeError):
            raise ValidationError(
                f"Field {field} must be of type {expected_type.__name__}"
            )
    return value


def _validate_string_field(field, value, rules):
    """Validate string length and sanitize."""
    if not isinstance(value, str):
        return value

    min_length = rules.get("min_length", 0)
    max_length = rules.get("max_length", 1000)

    if len(value) < min_length:
        raise ValidationError(f"Field {field} must be at least {min_length} characters")

    if len(value) > max_length:
        raise ValidationError(f"Field {field} must be at most {max_length} characters")

    return InputSanitizer.sanitize_text(value, max_length)


def _validate_number_field(field, value, rules):
    """Validate number range."""
    if not isinstance(value, (int, float)):
        return value

    min_value = rules.get("min_value")
    max_value = rules.get("max_value")

    if min_value is not None and value < min_value:
        raise ValidationError(f"Field {field} must be at least {min_value}")

    if max_value is not None and value > max_value:
        raise ValidationError(f"Field {field} must be at most {max_value}")

    return value


def _validate_pattern_field(field, value, rules):
    """Validate string pattern match."""
    pattern = rules.get("pattern")
    if pattern and isinstance(value, str):
        if not re.match(pattern, value):
            raise ValidationError(f"Field {field} does not match required pattern")
    return value


def validate_json_input(data: Dict[str, Any], schema: Dict[str, Any]) -> Dict[str, Any]:
    """
    Validate JSON input against a schema.

    Refactored to reduce complexity: C:18 → C:5
    Uses dedicated validators for type, string, number, pattern.

    Args:
        data: Input data to validate
        schema: Validation schema

    Returns:
        Validated and sanitized data

    Raises:
        ValidationError: If validation fails
    """
    validated_data = {}

    for field, rules in schema.items():
        value = data.get(field)

        _check_required_field(field, value, rules)

        if value is not None:
            value = _validate_field_type(field, value, rules)
            value = _validate_string_field(field, value, rules)
            value = _validate_number_field(field, value, rules)
            value = _validate_pattern_field(field, value, rules)

            validated_data[field] = value

    return validated_data


# Common validation schemas for API endpoints
API_SCHEMAS = {
    "performance_metric": {
        "metric_type": {
            "required": True,
            "type": str,
            "max_length": 50,
            "pattern": r"^(lcp|fid|cls|fcp|ttfb|inp|navigation|resource|memory|custom|core_web_vitals|page_load|response_time)$",
        },
        "value": {"required": True, "type": float, "min_value": 0, "max_value": 100000},
        "url": {"required": False, "type": str, "max_length": 500},
        "device_type": {
            "required": False,
            "type": str,
            "max_length": 20,
            "pattern": r"^(mobile|desktop|tablet)$",
        },
        "connection_type": {
            "required": False,
            "type": str,
            "max_length": 20,
            "pattern": r"^(4g|3g|2g|slow-2g|wifi|ethernet|unknown)$",
        },
        "additional_data": {"required": False, "type": dict},
    },
    "push_subscription": {
        "endpoint": {"required": True, "type": str, "max_length": 500},
        "keys": {"required": False, "type": dict},
    },
    "error_log": {
        "message": {"required": True, "type": str, "max_length": 1000},
        "level": {
            "required": False,
            "type": str,
            "max_length": 20,
            "pattern": r"^(critical|error|warning|info)$",
        },
        "url": {"required": False, "type": str, "max_length": 200},
    },
}
