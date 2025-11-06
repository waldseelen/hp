"""Date and time utilities

This module provides centralized date/time functions used across the application.
"""

from datetime import datetime, timedelta
from typing import Optional

from django.utils import timezone

__all__ = [
    "get_current_datetime",
    "get_current_date",
    "days_between",
    "hours_between",
    "is_past",
    "is_future",
    "add_days",
    "add_hours",
    "start_of_day",
    "end_of_day",
    "humanize_timedelta",
]


def get_current_datetime() -> datetime:
    """Get current datetime in the configured timezone

    Returns:
        datetime: Current datetime with timezone

    Examples:
        >>> now = get_current_datetime()
        >>> now.tzinfo is not None
        True
    """
    return timezone.now()


def get_current_date():
    """Get current date in the configured timezone

    Returns:
        date: Current date

    Examples:
        >>> today = get_current_date()
    """
    return timezone.now().date()


def days_between(date1: datetime, date2: datetime) -> int:
    """Calculate number of days between two dates

    Args:
        date1: First date
        date2: Second date

    Returns:
        int: Number of days between dates (can be negative)

    Examples:
        >>> days_between(datetime(2024, 1, 1), datetime(2024, 1, 10))
        9
    """
    if not date1 or not date2:
        return 0

    delta = date2 - date1
    return delta.days


def hours_between(dt1: datetime, dt2: datetime) -> float:
    """Calculate number of hours between two datetimes

    Args:
        dt1: First datetime
        dt2: Second datetime

    Returns:
        float: Number of hours between datetimes (can be negative)

    Examples:
        >>> hours_between(datetime(2024, 1, 1, 10), datetime(2024, 1, 1, 15))
        5.0
    """
    if not dt1 or not dt2:
        return 0.0

    delta = dt2 - dt1
    return delta.total_seconds() / 3600


def is_past(dt: datetime) -> bool:
    """Check if a datetime is in the past

    Args:
        dt: Datetime to check

    Returns:
        bool: True if datetime is in the past, False otherwise

    Examples:
        >>> is_past(datetime(2020, 1, 1))
        True
    """
    if not dt:
        return False

    return dt < timezone.now()


def is_future(dt: datetime) -> bool:
    """Check if a datetime is in the future

    Args:
        dt: Datetime to check

    Returns:
        bool: True if datetime is in the future, False otherwise

    Examples:
        >>> is_future(datetime(2099, 1, 1))
        True
    """
    if not dt:
        return False

    return dt > timezone.now()


def add_days(dt: datetime, days: int) -> datetime:
    """Add days to a datetime

    Args:
        dt: Base datetime
        days: Number of days to add (can be negative)

    Returns:
        datetime: New datetime with days added

    Examples:
        >>> add_days(datetime(2024, 1, 1), 7)
        datetime(2024, 1, 8, 0, 0)
    """
    if not dt:
        return timezone.now()

    return dt + timedelta(days=days)


def add_hours(dt: datetime, hours: int) -> datetime:
    """Add hours to a datetime

    Args:
        dt: Base datetime
        hours: Number of hours to add (can be negative)

    Returns:
        datetime: New datetime with hours added

    Examples:
        >>> add_hours(datetime(2024, 1, 1, 10), 5)
        datetime(2024, 1, 1, 15, 0)
    """
    if not dt:
        return timezone.now()

    return dt + timedelta(hours=hours)


def start_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get start of day (midnight) for a datetime

    Args:
        dt: Datetime to process (default: current datetime)

    Returns:
        datetime: Datetime at start of day (00:00:00)

    Examples:
        >>> start_of_day(datetime(2024, 1, 15, 14, 30))
        datetime(2024, 1, 15, 0, 0)
    """
    if not dt:
        dt = timezone.now()

    return dt.replace(hour=0, minute=0, second=0, microsecond=0)


def end_of_day(dt: Optional[datetime] = None) -> datetime:
    """Get end of day (23:59:59) for a datetime

    Args:
        dt: Datetime to process (default: current datetime)

    Returns:
        datetime: Datetime at end of day (23:59:59)

    Examples:
        >>> end_of_day(datetime(2024, 1, 15, 14, 30))
        datetime(2024, 1, 15, 23, 59, 59, 999999)
    """
    if not dt:
        dt = timezone.now()

    return dt.replace(hour=23, minute=59, second=59, microsecond=999999)


def humanize_timedelta(td: timedelta) -> str:
    """Convert timedelta to human-readable string

    Args:
        td: Timedelta to humanize

    Returns:
        str: Human-readable representation (e.g., "2 days", "3 hours")

    Examples:
        >>> humanize_timedelta(timedelta(days=2))
        '2 days'
        >>> humanize_timedelta(timedelta(hours=3))
        '3 hours'
        >>> humanize_timedelta(timedelta(minutes=45))
        '45 minutes'
    """
    if not td:
        return "0 minutes"

    total_seconds = int(td.total_seconds())

    if total_seconds < 0:
        return "0 minutes"

    days = total_seconds // 86400
    hours = (total_seconds % 86400) // 3600
    minutes = (total_seconds % 3600) // 60

    if days > 0:
        return f"{days} day{'s' if days != 1 else ''}"
    elif hours > 0:
        return f"{hours} hour{'s' if hours != 1 else ''}"
    elif minutes > 0:
        return f"{minutes} minute{'s' if minutes != 1 else ''}"
    else:
        return "less than a minute"
