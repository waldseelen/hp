"""Model helper utilities for common model operations

This module provides reusable functions for common model operations like
unique slug generation, auto-setting timestamps, etc.
"""

from typing import Any, Optional

from django.db import models
from django.utils import timezone
from django.utils.text import slugify

__all__ = [
    "generate_unique_slug",
    "auto_set_published_at",
    "calculate_reading_time",
]


def generate_unique_slug(
    instance: models.Model,
    title_field: str = "title",
    slug_field: str = "slug",
    max_length: int = 250,
) -> str:
    """Generate a unique slug for a model instance

    Args:
        instance: Model instance to generate slug for
        title_field: Name of the field containing the title (default: "title")
        slug_field: Name of the slug field (default: "slug")
        max_length: Maximum slug length (default: 250)

    Returns:
        str: Unique slug string

    Examples:
        >>> class Post(models.Model):
        ...     title = models.CharField(max_length=200)
        ...     slug = models.SlugField(unique=True)
        ...
        ...     def save(self, *args, **kwargs):
        ...         if not self.slug:
        ...             self.slug = generate_unique_slug(self)
        ...         super().save(*args, **kwargs)

    Note:
        This function checks for existing slugs and appends a counter if needed.
        Example: "my-post" -> "my-post-1" -> "my-post-2" etc.
    """
    # Get the title value
    title = getattr(instance, title_field, "")
    if not title:
        raise ValueError(f"Instance must have a non-empty {title_field} field")

    # Generate base slug
    base_slug = slugify(title)
    if not base_slug:
        raise ValueError(f"Could not generate slug from {title_field}: {title}")

    # Truncate to max length, leaving room for counter
    base_slug = base_slug[: max_length - 10]  # Reserve 10 chars for counter

    # Get the model class
    model_class = instance.__class__

    # Check if slug is already set and is still unique
    current_slug = getattr(instance, slug_field, None)
    if current_slug:
        # Check if current slug is still valid
        queryset = model_class.objects.filter(**{slug_field: current_slug})
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)
        if not queryset.exists():
            return current_slug

    # Generate unique slug
    slug = base_slug
    counter = 1

    while True:
        # Check if slug exists
        queryset = model_class.objects.filter(**{slug_field: slug})
        if instance.pk:
            queryset = queryset.exclude(pk=instance.pk)

        if not queryset.exists():
            return slug

        # Increment counter and try again
        slug = f"{base_slug}-{counter}"
        counter += 1

        # Safety check to prevent infinite loop
        if counter > 10000:
            # Append timestamp as fallback
            import time

            timestamp = int(time.time())
            return f"{base_slug}-{timestamp}"


def auto_set_published_at(
    instance: models.Model,
    status_field: str = "status",
    published_status: str = "published",
    published_at_field: str = "published_at",
) -> None:
    """Automatically set published_at timestamp when status changes to published

    Args:
        instance: Model instance to update
        status_field: Name of the status field (default: "status")
        published_status: Status value that indicates published (default: "published")
        published_at_field: Name of the published_at field (default: "published_at")

    Examples:
        >>> class Post(models.Model):
        ...     status = models.CharField(max_length=20)
        ...     published_at = models.DateTimeField(null=True, blank=True)
        ...
        ...     def save(self, *args, **kwargs):
        ...         auto_set_published_at(self)
        ...         super().save(*args, **kwargs)

    Note:
        - Sets published_at to current time if status is published and published_at is None
        - Clears published_at if status is not published
    """
    status = getattr(instance, status_field, None)
    published_at = getattr(instance, published_at_field, None)

    if status == published_status and not published_at:
        # Set published_at to now
        setattr(instance, published_at_field, timezone.now())
    elif status != published_status and published_at:
        # Clear published_at if no longer published
        setattr(instance, published_at_field, None)


def calculate_reading_time(
    content: str,
    words_per_minute: int = 200,
) -> int:
    """Calculate estimated reading time for content

    Args:
        content: Text content to calculate reading time for
        words_per_minute: Average reading speed (default: 200)

    Returns:
        int: Estimated reading time in minutes (minimum 1)

    Examples:
        >>> content = "This is a sample text with many words..."
        >>> calculate_reading_time(content)
        5

    Note:
        Uses a simple word count divided by reading speed.
        Minimum return value is 1 minute.
    """
    if not content:
        return 0

    word_count = len(content.split())
    reading_time = word_count // words_per_minute

    return max(1, reading_time)
