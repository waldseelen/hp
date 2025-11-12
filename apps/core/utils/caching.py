"""Caching utilities for cache key generation and management

This module provides centralized caching functions used across the application.
"""

import hashlib
import json
from typing import Any, Optional

from django.core.cache import cache

__all__ = [
    "generate_cache_key",
    "cache_get_or_set",
    "invalidate_cache_pattern",
    "get_model_cache_key",
]


def generate_cache_key(*args, prefix: str = "", **kwargs) -> str:
    """Generate a consistent cache key from arguments

    Args:
        *args: Positional arguments to include in key
        prefix: Optional prefix for the key
        **kwargs: Keyword arguments to include in key

    Returns:
        str: Generated cache key

    Examples:
        >>> generate_cache_key("user", 123, prefix="profile")
        'profile:user:123'
        >>> generate_cache_key(user_id=123, action="view")
        'user_id=123:action=view'
    """
    parts = []

    if prefix:
        parts.append(prefix)

    # Add positional args
    parts.extend(str(arg) for arg in args)

    # Add keyword args (sorted for consistency)
    for key in sorted(kwargs.keys()):
        parts.append(f"{key}={kwargs[key]}")

    # Join parts and hash if too long
    key = ":".join(parts)

    if len(key) > 200:  # Django cache key limit is 250
        # Hash long keys to keep them short
        key_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
        return f"{prefix}:{key_hash}" if prefix else key_hash

    return key


def cache_get_or_set(
    key: str,
    default_callable: callable,
    timeout: Optional[int] = None,
) -> Any:
    """Get value from cache or set it using callable

    Args:
        key: Cache key
        default_callable: Function to call if key not in cache
        timeout: Cache timeout in seconds (None = default timeout)

    Returns:
        Any: Cached value or result of default_callable

    Examples:
        >>> def expensive_operation():
        ...     return "result"
        >>> value = cache_get_or_set("my_key", expensive_operation, timeout=300)
    """
    value = cache.get(key)

    if value is None:
        value = default_callable()
        cache.set(key, value, timeout=timeout)

    return value


def invalidate_cache_pattern(pattern: str) -> int:
    """Invalidate all cache keys matching a pattern

    Args:
        pattern: Pattern to match cache keys (supports wildcards)

    Returns:
        int: Number of keys invalidated

    Note:
        This requires a cache backend that supports key iteration
        (e.g., Redis). Won't work with memcached.

    Examples:
        >>> invalidate_cache_pattern("user:*")
        5  # Invalidated 5 keys
    """
    try:
        # This works with Redis backend
        from django.conf import settings
        from django.core.cache import caches

        cache_backend = caches[settings.CACHES.get("default", {}).get("BACKEND", "")]

        if hasattr(cache_backend, "keys"):
            keys = cache_backend.keys(pattern)
            if keys:
                cache_backend.delete_many(keys)
                return len(keys)

        return 0
    except Exception:
        # Fallback: can't iterate keys with this backend
        return 0


def get_model_cache_key(
    model_name: str,
    instance_id: Optional[int] = None,
    action: str = "detail",
) -> str:
    """Generate a cache key for a model instance or queryset

    Args:
        model_name: Name of the model (e.g., "Post", "Tool")
        instance_id: Optional instance ID for specific object caching
        action: Action being cached (e.g., "detail", "list", "count")

    Returns:
        str: Generated cache key

    Examples:
        >>> get_model_cache_key("Post", 123, "detail")
        'model:Post:123:detail'
        >>> get_model_cache_key("Post", action="list")
        'model:Post:list'
    """
    parts = ["model", model_name]

    if instance_id is not None:
        parts.append(str(instance_id))

    parts.append(action)

    return ":".join(parts)
