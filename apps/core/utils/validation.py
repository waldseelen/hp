"""Validation utilities for input validation and sanitization

This module provides centralized validation functions used across the application.
"""

import re
from typing import Any, List, Optional, Union
from urllib.parse import urlparse

from django.core.exceptions import ValidationError
from django.core.validators import URLValidator, validate_email

__all__ = [
    "validate_url_format",
    "validate_email_format",
    "sanitize_html",
    "validate_phone_number",
    "validate_tags",
    "is_valid_slug",
    "validate_json_structure",
]


def validate_url_format(url: str) -> bool:
    """Validate URL format

    Args:
        url: URL string to validate

    Returns:
        bool: True if valid URL format, False otherwise

    Examples:
        >>> validate_url_format("https://example.com")
        True
        >>> validate_url_format("not-a-url")
        False
    """
    if not url:
        return False

    validator = URLValidator(schemes=["http", "https"])
    try:
        validator(url)
        return True
    except ValidationError:
        return False


def validate_email_format(email: str) -> bool:
    """Validate email format

    Args:
        email: Email string to validate

    Returns:
        bool: True if valid email format, False otherwise

    Examples:
        >>> validate_email_format("user@example.com")
        True
        >>> validate_email_format("not-an-email")
        False
    """
    if not email:
        return False

    try:
        validate_email(email)
        return True
    except ValidationError:
        return False


def sanitize_html(text: str, allowed_tags: Optional[List[str]] = None) -> str:
    """Sanitize HTML by removing/escaping dangerous tags

    Args:
        text: HTML text to sanitize
        allowed_tags: List of allowed HTML tags (default: None = strip all)

    Returns:
        str: Sanitized HTML text

    Note:
        This is a basic implementation. For production, use bleach or similar.

    Examples:
        >>> sanitize_html("<script>alert('xss')</script>Hello")
        'Hello'
        >>> sanitize_html("<p>Hello</p>", allowed_tags=['p'])
        '<p>Hello</p>'
    """
    if not text:
        return ""

    if allowed_tags is None:
        # Strip all HTML tags
        return re.sub(r"<[^>]+>", "", text)

    # Remove non-allowed tags
    pattern = r"<(?!\s*/?(?:" + "|".join(allowed_tags) + r")\b)[^>]*>"
    return re.sub(pattern, "", text)


def validate_phone_number(phone: str, country_code: str = "US") -> bool:
    """Validate phone number format

    Args:
        phone: Phone number string to validate
        country_code: Country code for validation (default: US)

    Returns:
        bool: True if valid phone format, False otherwise

    Note:
        Basic validation only. For production, use phonenumbers library.

    Examples:
        >>> validate_phone_number("+1-555-123-4567")
        True
        >>> validate_phone_number("123")
        False
    """
    if not phone:
        return False

    # Remove common formatting characters
    cleaned = re.sub(r"[\s\-\(\)\+]", "", phone)

    # Check if remaining chars are digits
    if not cleaned.isdigit():
        return False

    # Check length (10-15 digits is reasonable for most countries)
    return 10 <= len(cleaned) <= 15


def validate_tags(
    tags: Union[List[str], str],
    max_tags: int = 10,
    max_length: int = 50,
) -> tuple[bool, str]:
    """Validate tags list or comma-separated string

    Args:
        tags: List of tags or comma-separated string
        max_tags: Maximum number of tags allowed
        max_length: Maximum length per tag

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_tags(["python", "django"])
        (True, "")
        >>> validate_tags("python,django,react")
        (True, "")
        >>> validate_tags(["a" * 100])
        (False, "Tag exceeds maximum length of 50 characters")
    """
    if not tags:
        return (True, "")

    # Convert string to list
    if isinstance(tags, str):
        tags = [tag.strip() for tag in tags.split(",") if tag.strip()]

    # Check if tags is a list
    if not isinstance(tags, list):
        return (False, "Tags must be a list or comma-separated string")

    # Check number of tags
    if len(tags) > max_tags:
        return (False, f"Maximum {max_tags} tags allowed")

    # Validate each tag
    for tag in tags:
        if not isinstance(tag, str):
            return (False, "Each tag must be a string")

        if not tag.strip():
            return (False, "Empty tags are not allowed")

        if len(tag) > max_length:
            return (False, f"Tag exceeds maximum length of {max_length} characters")

    return (True, "")


def is_valid_slug(slug: str) -> bool:
    """Check if string is a valid slug

    Args:
        slug: String to validate as slug

    Returns:
        bool: True if valid slug format, False otherwise

    Examples:
        >>> is_valid_slug("my-blog-post")
        True
        >>> is_valid_slug("My Blog Post")
        False
        >>> is_valid_slug("post_123")
        True
    """
    if not slug:
        return False

    # Slug should contain only lowercase letters, numbers, hyphens, and underscores
    pattern = r"^[a-z0-9]+(?:-[a-z0-9]+)*$"
    return bool(re.match(pattern, slug))


def validate_json_structure(
    data: Any,
    required_keys: Optional[List[str]] = None,
) -> tuple[bool, str]:
    """Validate JSON structure against required keys

    Args:
        data: JSON data (dict) to validate
        required_keys: List of required keys in the JSON

    Returns:
        tuple: (is_valid, error_message)

    Examples:
        >>> validate_json_structure({"name": "John"}, required_keys=["name"])
        (True, "")
        >>> validate_json_structure({"age": 30}, required_keys=["name"])
        (False, "Missing required key: name")
    """
    if not isinstance(data, dict):
        return (False, "Data must be a dictionary")

    if required_keys:
        missing_keys = [key for key in required_keys if key not in data]
        if missing_keys:
            return (False, f"Missing required key: {missing_keys[0]}")

    return (True, "")
