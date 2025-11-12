"""
Cache utility functions for intelligent cache invalidation.
Manages cache keys, invalidation strategies, and fallback data.
"""

import hashlib
import logging
from typing import Any, Dict, List, Optional

from django.core.cache import cache
from django.utils import timezone

logger = logging.getLogger(__name__)

# Cache key patterns and prefixes
CACHE_KEYS = {
    "home_page": "home_page_data_{hash}_{hour}",
    "personal_page": "personal_page_data",
    "music_page": "music_page_data",
    "useful_page": "useful_page_data",
    "portfolio_stats": "portfolio_statistics",
    "ai_tools_cache": "ai_tools_{category}",
    "cybersecurity_cache": "cybersecurity_{type}",
    "blog_posts": "blog_posts_{filter}",
    "tools_cache": "tools_{category}",
    "model_data": "{app}_{model}_{id}",
}

# Cache timeout constants (in seconds)
CACHE_TIMEOUTS = {
    "short": 300,  # 5 minutes
    "medium": 900,  # 15 minutes
    "long": 3600,  # 1 hour
    "daily": 86400,  # 24 hours
    "weekly": 604800,  # 7 days
}


class CacheManager:
    """
    Centralized cache management with invalidation tracking and fallback support.
    """

    def __init__(self):
        self.invalidation_log = {}
        self.related_keys = {}

    def get_cache_key(self, pattern: str, **kwargs) -> str:
        """
        Generate a cache key from a pattern with variable substitution.

        Args:
            pattern: Cache key pattern from CACHE_KEYS
            **kwargs: Variables to substitute in pattern

        Returns:
            Generated cache key
        """
        try:
            key_template = CACHE_KEYS.get(pattern, pattern)

            # Handle hash-based keys
            if "{hash}" in key_template:
                hash_value = kwargs.pop("hash", "")
                key_template = key_template.replace("{hash}", str(hash_value))

            # Handle hour-based keys
            if "{hour}" in key_template:
                hour = kwargs.pop("hour", timezone.now().hour)
                key_template = key_template.replace("{hour}", str(hour))

            # Replace remaining placeholders
            return key_template.format(**kwargs)
        except (KeyError, TypeError) as e:
            logger.error(f"Error generating cache key: {e}")
            return pattern

    def set_cache(
        self,
        key: str,
        value: Any,
        timeout: str = "medium",
        related_keys: Optional[List[str]] = None,
    ) -> None:
        """
        Set cache with optional related keys for batch invalidation.

        Args:
            key: Cache key
            value: Value to cache
            timeout: Timeout type ('short', 'medium', 'long', 'daily', 'weekly')
            related_keys: List of related cache keys for invalidation tracking
        """
        try:
            timeout_seconds = CACHE_TIMEOUTS.get(timeout, CACHE_TIMEOUTS["medium"])
            cache.set(key, value, timeout_seconds)

            # Track related keys
            if related_keys:
                self.related_keys[key] = related_keys

            logger.debug(f"Cache set: {key} with timeout: {timeout_seconds}s")
        except Exception as e:
            logger.error(f"Error setting cache: {e}")

    def get_cache(self, key: str, fallback: Any = None) -> Any:
        """
        Get cache value with fallback support.

        Args:
            key: Cache key
            fallback: Fallback value if cache miss

        Returns:
            Cached value or fallback
        """
        try:
            value = cache.get(key)
            if value is None:
                logger.debug(f"Cache miss: {key}")
                return fallback
            logger.debug(f"Cache hit: {key}")
            return value
        except Exception as e:
            logger.error(f"Error getting cache: {e}")
            return fallback

    def invalidate_cache(self, key: str) -> None:
        """
        Invalidate a specific cache key and related keys.

        Args:
            key: Cache key to invalidate
        """
        try:
            cache.delete(key)

            # Invalidate related keys
            related = self.related_keys.get(key, [])
            for related_key in related:
                cache.delete(related_key)

            # Log invalidation
            self.invalidation_log[key] = timezone.now().isoformat()
            logger.info(f"Cache invalidated: {key} and {len(related)} related keys")
        except Exception as e:
            logger.error(f"Error invalidating cache: {e}")

    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate multiple cache keys matching a pattern.

        Args:
            pattern: Pattern to match (e.g., 'home_page_*')

        Returns:
            Number of keys invalidated
        """
        try:
            # Try to get all cache keys using cache.keys() if available
            try:
                keys = cache.keys(pattern)
                cache.delete_many(keys)
                logger.info(
                    f"Cache invalidated: {len(keys)} keys matching pattern '{pattern}'"
                )
                return len(keys)
            except (AttributeError, TypeError):
                # Fall back for cache backends that don't support keys() (e.g., LocMemCache)
                logger.debug(
                    f"Cache backend doesn't support pattern matching, skipping pattern '{pattern}'"
                )
                return 0
        except Exception as e:
            logger.error(f"Error invalidating cache pattern: {e}")
            return 0

    def invalidate_by_model(
        self, app: str, model: str, instance_id: Optional[int] = None
    ) -> None:
        """
        Invalidate cache keys related to a specific model.

        Args:
            app: App label
            model: Model name
            instance_id: Specific instance ID (None to invalidate all)
        """
        try:
            if instance_id:
                key = f"{app}_{model}_{instance_id}"
                cache.delete(key)
            else:
                pattern = f"{app}_{model}_*"
                self.invalidate_pattern(pattern)

            logger.info(
                f"Cache invalidated by model: {app}.{model}"
                + (f" instance {instance_id}" if instance_id else "")
            )
        except Exception as e:
            logger.error(f"Error invalidating cache by model: {e}")


# Global cache manager instance
cache_manager = CacheManager()


def cache_result(timeout: str = "medium", key_prefix: Optional[str] = None):
    """
    Decorator to cache function results automatically.

    Args:
        timeout: Cache timeout type
        key_prefix: Custom cache key prefix

    Returns:
        Decorated function with caching
    """

    def decorator(func):
        def wrapper(*args, **kwargs):
            # Generate cache key
            key_parts = [key_prefix or func.__name__]

            # Add arguments to cache key
            for arg in args:
                if isinstance(arg, (str, int)):
                    key_parts.append(str(arg))

            for k, v in sorted(kwargs.items()):
                if isinstance(v, (str, int)):
                    key_parts.append(f"{k}_{v}")

            cache_key = "_".join(key_parts)

            # Try to get from cache
            cached = cache_manager.get_cache(cache_key)
            if cached is not None:
                return cached

            # Execute function
            result = func(*args, **kwargs)

            # Cache result
            cache_manager.set_cache(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def cache_queryset_medium(func):
    """
    Decorator for caching queryset results with medium timeout (15 minutes).
    """
    return cache_result(timeout="medium")(func)


def cache_long(func):
    """
    Decorator for caching results with long timeout (1 hour).
    """
    return cache_result(timeout="long")(func)


def cache_page_data(timeout: str = "medium"):
    """
    Decorator specifically for caching page view data.
    """
    return cache_result(timeout=timeout)


class ModelCacheManager:
    """
    Advanced cache management for Django models with automatic invalidation.
    """

    def __init__(self):
        self.model_cache_keys = {}

    def register_model_cache(self, model, cache_keys: List[str]) -> None:
        """
        Register cache keys that depend on a specific model.

        Args:
            model: Django model class
            cache_keys: List of cache keys to invalidate when model changes
        """
        model_key = f"{model._meta.app_label}.{model._meta.model_name}"
        self.model_cache_keys[model_key] = cache_keys
        logger.info(f"Registered cache keys for model: {model_key}")

    def invalidate_on_save(self, sender, instance, created, **kwargs) -> None:
        """
        Signal handler to invalidate cache when model is saved.

        Args:
            sender: Model class
            instance: Model instance
            created: Whether instance was created
        """
        try:
            model_key = f"{sender._meta.app_label}.{sender._meta.model_name}"
            cache_keys = self.model_cache_keys.get(model_key, [])

            for cache_key in cache_keys:
                cache_manager.invalidate_cache(cache_key)

            action = "created" if created else "updated"
            logger.info(
                f"Cache invalidated on {action}: {model_key} (id: {instance.id})"
            )
        except Exception as e:
            logger.error(f"Error invalidating cache on save: {e}")

    def invalidate_on_delete(self, sender, instance, **kwargs) -> None:
        """
        Signal handler to invalidate cache when model is deleted.

        Args:
            sender: Model class
            instance: Model instance
        """
        try:
            model_key = f"{sender._meta.app_label}.{sender._meta.model_name}"
            cache_keys = self.model_cache_keys.get(model_key, [])

            for cache_key in cache_keys:
                cache_manager.invalidate_cache(cache_key)

            logger.info(f"Cache invalidated on delete: {model_key} (id: {instance.id})")
        except Exception as e:
            logger.error(f"Error invalidating cache on delete: {e}")


# Global model cache manager
model_cache_manager = ModelCacheManager()


def create_cache_invalidation_key(app: str, model: str, keys: List[str]) -> str:
    """
    Create a cache invalidation key for tracking model-cache relationships.

    Args:
        app: App label
        model: Model name
        keys: List of cache keys

    Returns:
        Invalidation key
    """
    content = f"{app}_{model}_{'_'.join(keys)}"
    return hashlib.md5(content.encode(), usedforsecurity=False).hexdigest()


def get_fallback_data(key: str) -> Optional[Dict[str, Any]]:
    """
    Get fallback data when cache is unavailable.

    Args:
        key: Cache key

    Returns:
        Fallback data dictionary
    """
    fallback_data = {
        "home_page_data": {
            "personal_info": [],
            "social_links": [],
            "recent_posts": [],
            "featured_projects": [],
            "featured_ai_tools": [],
            "urgent_security": [],
            "portfolio_stats": {},
            "current_activity": None,
            "latest_skills": [],
        },
        "personal_page_data": {"personal_info": [], "social_links": []},
        "music_page_data": {
            "playlists": [],
            "featured_playlists": [],
            "current_track": None,
        },
        "useful_page_data": {"resources_by_category": {}, "featured_resources": []},
    }

    # Match key pattern or return generic fallback
    for fallback_key, fallback_value in fallback_data.items():
        if fallback_key in key:
            return fallback_value

    return {}
