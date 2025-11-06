"""Formatting utilities for dates, numbers, and text

This module provides centralized formatting functions used across the application.
"""

from datetime import datetime
from typing import Optional

from django.utils import timezone

__all__ = [
    "format_date",
    "format_datetime",
    "format_number",
    "format_currency",
    "format_percentage",
    "truncate_text",
    "format_filesize",
]


def format_date(date: Optional[datetime], format_str: str = "%Y-%m-%d") -> str:
    """Format a date object to string

    Args:
        date: datetime object to format
        format_str: Python strftime format string (default: YYYY-MM-DD)

    Returns:
        str: Formatted date string or empty string if date is None

    Examples:
        >>> format_date(datetime(2024, 1, 15))
        '2024-01-15'
        >>> format_date(datetime(2024, 1, 15), "%d/%m/%Y")
        '15/01/2024'
    """
    if not date:
        return ""
    return date.strftime(format_str)


def format_datetime(
    dt: Optional[datetime],
    format_str: str = "%Y-%m-%d %H:%M:%S",
    use_local_timezone: bool = True,
) -> str:
    """Format a datetime object to string

    Args:
        dt: datetime object to format
        format_str: Python strftime format string
        use_local_timezone: Convert to local timezone before formatting

    Returns:
        str: Formatted datetime string or empty string if dt is None

    Examples:
        >>> format_datetime(datetime(2024, 1, 15, 14, 30))
        '2024-01-15 14:30:00'
    """
    if not dt:
        return ""

    if use_local_timezone and timezone.is_aware(dt):
        dt = timezone.localtime(dt)

    return dt.strftime(format_str)


def format_number(number: Optional[float], decimals: int = 0) -> str:
    """Format a number with thousand separators

    Args:
        number: Number to format
        decimals: Number of decimal places (default: 0)

    Returns:
        str: Formatted number string or empty string if number is None

    Examples:
        >>> format_number(1234567)
        '1,234,567'
        >>> format_number(1234.567, decimals=2)
        '1,234.57'
    """
    if number is None:
        return ""

    format_str = f"{{:,.{decimals}f}}"
    return format_str.format(number)


def format_currency(
    amount: Optional[float],
    currency: str = "$",
    decimals: int = 2,
) -> str:
    """Format a number as currency

    Args:
        amount: Amount to format
        currency: Currency symbol (default: $)
        decimals: Number of decimal places (default: 2)

    Returns:
        str: Formatted currency string or empty string if amount is None

    Examples:
        >>> format_currency(1234.56)
        '$1,234.56'
        >>> format_currency(1234.56, currency="€")
        '€1,234.56'
    """
    if amount is None:
        return ""

    formatted_number = format_number(amount, decimals=decimals)
    return f"{currency}{formatted_number}"


def format_percentage(
    value: Optional[float],
    decimals: int = 1,
    multiply_by_100: bool = False,
) -> str:
    """Format a number as percentage

    Args:
        value: Value to format
        decimals: Number of decimal places (default: 1)
        multiply_by_100: Whether to multiply value by 100 (default: False)

    Returns:
        str: Formatted percentage string or empty string if value is None

    Examples:
        >>> format_percentage(0.456, decimals=1, multiply_by_100=True)
        '45.6%'
        >>> format_percentage(45.6, decimals=0)
        '46%'
    """
    if value is None:
        return ""

    if multiply_by_100:
        value = value * 100

    format_str = f"{{:.{decimals}f}}%"
    return format_str.format(value)


def truncate_text(
    text: Optional[str],
    max_length: int = 100,
    suffix: str = "...",
) -> str:
    """Truncate text to a maximum length

    Args:
        text: Text to truncate
        max_length: Maximum length including suffix
        suffix: String to append when truncated (default: "...")

    Returns:
        str: Truncated text or empty string if text is None

    Examples:
        >>> truncate_text("This is a long text", max_length=10)
        'This is...'
        >>> truncate_text("Short", max_length=10)
        'Short'
    """
    if not text:
        return ""

    if len(text) <= max_length:
        return text

    return text[: max_length - len(suffix)] + suffix


def format_filesize(size_bytes: Optional[int]) -> str:
    """Format file size in bytes to human-readable format

    Args:
        size_bytes: File size in bytes

    Returns:
        str: Formatted file size (e.g., "1.5 MB") or empty string if size is None

    Examples:
        >>> format_filesize(1024)
        '1.0 KB'
        >>> format_filesize(1536000)
        '1.5 MB'
        >>> format_filesize(1073741824)
        '1.0 GB'
    """
    if size_bytes is None:
        return ""

    for unit in ["B", "KB", "MB", "GB", "TB"]:
        if size_bytes < 1024.0:
            return f"{size_bytes:.1f} {unit}"
        size_bytes /= 1024.0

    return f"{size_bytes:.1f} PB"
