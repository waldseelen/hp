"""
Comprehensive caching system with Redis support, query caching, and invalidation strategies.
"""

import hashlib
import json
import logging
from functools import wraps
from typing import Any, Dict, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.db.models import QuerySet
from django.template.loader import render_to_string
from django.utils import timezone

logger = logging.getLogger(__name__)


class CacheManager:
    """Advanced cache manager with Redis support and monitoring."""

    def __init__(self):
        self.cache = cache
        self.stats = CacheStats()
        self.default_timeout = getattr(
            settings, "CACHE_DEFAULT_TIMEOUT", 300
        )  # 5 minutes

    def get(self, key: str, default=None, version=None) -> Any:
        """Get value from cache with statistics tracking."""
        try:
            value = self.cache.get(key, default, version=version)
            if value is not None:
                self.stats.record_hit(key)
                logger.debug(f"Cache HIT for key: {key}")
                return value
            else:
                self.stats.record_miss(key)
                logger.debug(f"Cache MISS for key: {key}")
                return default
        except Exception as e:
            logger.error(f"Cache GET error for key {key}: {e}")
            self.stats.record_error(key, str(e))
            return default

    def set(
        self, key: str, value: Any, timeout: Optional[int] = None, version=None
    ) -> bool:
        """Set value in cache with error handling."""
        try:
            timeout = timeout or self.default_timeout
            result = self.cache.set(key, value, timeout, version=version)
            if result:
                self.stats.record_set(key, timeout)
                logger.debug(f"Cache SET for key: {key} (timeout: {timeout}s)")
            return result
        except Exception as e:
            logger.error(f"Cache SET error for key {key}: {e}")
            self.stats.record_error(key, str(e))
            return False

    def delete(self, key: str, version=None) -> bool:
        """Delete key from cache."""
        try:
            result = self.cache.delete(key, version=version)
            if result:
                self.stats.record_delete(key)
                logger.debug(f"Cache DELETE for key: {key}")
            return result
        except Exception as e:
            logger.error(f"Cache DELETE error for key {key}: {e}")
            return False

    def delete_pattern(self, pattern: str) -> int:
        """Delete all keys matching pattern (Redis only)."""
        try:
            if hasattr(self.cache, "delete_pattern"):
                count = self.cache.delete_pattern(pattern)
                logger.info(f"Cache DELETE_PATTERN: {pattern} ({count} keys deleted)")
                return count
            else:
                # Fallback for non-Redis backends
                logger.warning("delete_pattern not supported by cache backend")
                return 0
        except Exception as e:
            logger.error(f"Cache DELETE_PATTERN error for pattern {pattern}: {e}")
            return 0

    def get_many(self, keys: List[str], version=None) -> Dict[str, Any]:
        """Get multiple keys from cache."""
        try:
            result = self.cache.get_many(keys, version=version)
            for key in keys:
                if key in result:
                    self.stats.record_hit(key)
                else:
                    self.stats.record_miss(key)
            logger.debug(f"Cache GET_MANY: {len(result)}/{len(keys)} hits")
            return result
        except Exception as e:
            logger.error(f"Cache GET_MANY error: {e}")
            return {}

    def set_many(
        self, data: Dict[str, Any], timeout: Optional[int] = None, version=None
    ) -> bool:
        """Set multiple keys in cache."""
        try:
            timeout = timeout or self.default_timeout
            result = self.cache.set_many(data, timeout, version=version)
            for key in data.keys():
                self.stats.record_set(key, timeout)
            logger.debug(f"Cache SET_MANY: {len(data)} keys")
            return result
        except Exception as e:
            logger.error(f"Cache SET_MANY error: {e}")
            return False

    def clear(self) -> bool:
        """Clear entire cache."""
        try:
            result = self.cache.clear()
            logger.info("Cache CLEAR: All keys deleted")
            self.stats.reset()
            return result
        except Exception as e:
            logger.error(f"Cache CLEAR error: {e}")
            return False

    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self.stats.get_stats()


class CacheStats:
    """Cache statistics tracker."""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.sets = 0
        self.deletes = 0
        self.errors = 0
        self.error_log = []
        self.start_time = timezone.now()

    def record_hit(self, key: str):
        """Record cache hit."""
        self.hits += 1

    def record_miss(self, key: str):
        """Record cache miss."""
        self.misses += 1

    def record_set(self, key: str, timeout: int):
        """Record cache set operation."""
        self.sets += 1

    def record_delete(self, key: str):
        """Record cache delete operation."""
        self.deletes += 1

    def record_error(self, key: str, error: str):
        """Record cache error."""
        self.errors += 1
        self.error_log.append(
            {"key": key, "error": error, "timestamp": timezone.now().isoformat()}
        )
        # Keep only last 100 errors
        if len(self.error_log) > 100:
            self.error_log = self.error_log[-100:]

    def get_stats(self) -> Dict[str, Any]:
        """Get comprehensive statistics."""
        total_operations = self.hits + self.misses
        hit_ratio = (self.hits / total_operations * 100) if total_operations > 0 else 0
        uptime = timezone.now() - self.start_time

        return {
            "hits": self.hits,
            "misses": self.misses,
            "sets": self.sets,
            "deletes": self.deletes,
            "errors": self.errors,
            "hit_ratio": round(hit_ratio, 2),
            "total_operations": total_operations,
            "uptime_seconds": uptime.total_seconds(),
            "recent_errors": self.error_log[-10:] if self.error_log else [],
        }

    def reset(self):
        """Reset all statistics."""
        self.__init__()


# Global cache manager instance
cache_manager = CacheManager()


def cache_key_generator(prefix: str, *args, **kwargs) -> str:
    """Generate consistent cache keys."""
    key_parts = [prefix]

    # Add positional arguments
    for arg in args:
        if hasattr(arg, "pk"):
            key_parts.append(f"{arg.__class__.__name__}_{arg.pk}")
        else:
            key_parts.append(str(arg))

    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if hasattr(v, "pk"):
            key_parts.append(f"{k}_{v.__class__.__name__}_{v.pk}")
        else:
            key_parts.append(f"{k}_{v}")

    # Create hash for very long keys
    key = "_".join(key_parts)
    if len(key) > 200:  # Most cache backends have key length limits
        key_hash = hashlib.md5(key.encode(), usedforsecurity=False).hexdigest()
        key = f"{prefix}_{key_hash}"

    return key


def cached_query(timeout: int = 300, key_prefix: str = "query"):
    """Decorator for caching QuerySet results."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache_key_generator(key_prefix, func.__name__, *args, **kwargs)

            # Try to get from cache
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Execute function and cache result
            result = func(*args, **kwargs)

            # Convert QuerySet to list for caching
            if isinstance(result, QuerySet):
                result = list(result)

            cache_manager.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def cached_function(timeout: int = 300, key_prefix: str = "func"):
    """General function caching decorator."""

    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            cache_key = cache_key_generator(key_prefix, func.__name__, *args, **kwargs)

            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            result = func(*args, **kwargs)
            cache_manager.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


def cached_template(timeout: int = 600, key_prefix: str = "template"):
    """Cache rendered template fragments."""

    def decorator(func):
        @wraps(func)
        def wrapper(
            template_name: str, context: Dict = None, request=None, *args, **kwargs
        ):
            # Create cache key from template name and context
            context_hash = hashlib.md5(
                json.dumps(context or {}, sort_keys=True, default=str).encode(),
                usedforsecurity=False,
            ).hexdigest()[:8]

            cache_key = cache_key_generator(key_prefix, template_name, context_hash)

            # Try cache first
            result = cache_manager.get(cache_key)
            if result is not None:
                return result

            # Render template
            result = render_to_string(template_name, context, request)
            cache_manager.set(cache_key, result, timeout)
            return result

        return wrapper

    return decorator


class QueryCache:
    """Advanced query caching with automatic invalidation."""

    @staticmethod
    def get_model_cache_key(model_class: type, operation: str, **filters) -> str:
        """Generate cache key for model operations."""
        model_name = f"{model_class._meta.app_label}_{model_class._meta.model_name}"
        filter_hash = hashlib.md5(
            json.dumps(filters, sort_keys=True, default=str).encode(),
            usedforsecurity=False,
        ).hexdigest()[:8]
        return f"model_{model_name}_{operation}_{filter_hash}"

    @staticmethod
    def cache_queryset(
        queryset: QuerySet, timeout: int = 300, key_suffix: str = ""
    ) -> List:
        """Cache QuerySet results with model-based invalidation."""
        model_class = queryset.model
        query_hash = hashlib.md5(
            str(queryset.query).encode(), usedforsecurity=False
        ).hexdigest()[:8]
        cache_key = f"queryset_{model_class._meta.label_lower}_{query_hash}{key_suffix}"

        # Try cache
        result = cache_manager.get(cache_key)
        if result is not None:
            return result

        # Execute and cache
        result = list(queryset)
        cache_manager.set(cache_key, result, timeout)

        # Track for invalidation
        CacheInvalidator.track_model_cache(model_class, cache_key)

        return result

    @staticmethod
    def invalidate_model_cache(model_class: type, instance_id: Optional[int] = None):
        """Invalidate all cached queries for a model."""
        pattern = f"queryset_{model_class._meta.label_lower}_*"
        cache_manager.delete_pattern(pattern)

        # Also invalidate related model caches
        CacheInvalidator.invalidate_related_caches(model_class, instance_id)


class CacheInvalidator:
    """Handles automatic cache invalidation based on model changes."""

    _model_cache_tracking = {}

    @classmethod
    def track_model_cache(cls, model_class: type, cache_key: str):
        """Track cache keys for a model."""
        model_key = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
        if model_key not in cls._model_cache_tracking:
            cls._model_cache_tracking[model_key] = set()
        cls._model_cache_tracking[model_key].add(cache_key)

    @classmethod
    def invalidate_related_caches(
        cls, model_class: type, instance_id: Optional[int] = None
    ):
        """Invalidate caches for related models."""
        model_name = model_class._meta.model_name.lower()

        # Define related model invalidation rules
        invalidation_rules = {
            "post": ["blogpost", "personalinfo"],  # Blog posts affect other content
            "personalinfo": ["sociallink"],  # Personal info changes affect social links
            "sociallink": ["personalinfo"],  # Social links affect personal info
            "contactmessage": [],  # Contact messages don't affect other models
        }

        # Invalidate related model caches
        for related_model in invalidation_rules.get(model_name, []):
            pattern = f"queryset_*{related_model}*"
            cache_manager.delete_pattern(pattern)

    @classmethod
    def clear_model_tracking(cls, model_class: type):
        """Clear tracking for a model."""
        model_key = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
        if model_key in cls._model_cache_tracking:
            del cls._model_cache_tracking[model_key]


# Cache warming utilities
class CacheWarmer:
    """Utilities for warming up caches."""

    @staticmethod
    def warm_blog_caches():
        """Warm up blog-related caches."""
        from apps.blog.models import Post

        # Warm published posts
        posts = QueryCache.cache_queryset(
            Post.objects.filter(status="published").select_related("author")[:10],
            timeout=600,
            key_suffix="_published",
        )

        # Warm popular posts
        QueryCache.cache_queryset(
            Post.objects.filter(status="published").order_by("-view_count")[:5],
            timeout=600,
            key_suffix="_popular",
        )

        return len(posts)

    @staticmethod
    def warm_main_caches():
        """Warm up main app caches."""
        from apps.main.models import AITool, PersonalInfo, SocialLink

        count = 0

        # Personal info
        personal_info = QueryCache.cache_queryset(
            PersonalInfo.objects.filter(is_visible=True).order_by("order"),
            timeout=1800,  # 30 minutes
            key_suffix="_visible",
        )
        count += len(personal_info)

        # Social links
        social_links = QueryCache.cache_queryset(
            SocialLink.objects.filter(is_visible=True).order_by("order"),
            timeout=1800,
            key_suffix="_visible",
        )
        count += len(social_links)

        # Featured AI tools
        ai_tools = QueryCache.cache_queryset(
            AITool.objects.filter(is_featured=True, is_visible=True),
            timeout=600,
            key_suffix="_featured",
        )
        count += len(ai_tools)

        return count

    @staticmethod
    def warm_all_caches():
        """Warm up all application caches."""
        blog_count = CacheWarmer.warm_blog_caches()
        main_count = CacheWarmer.warm_main_caches()

        logger.info(f"Cache warming completed: {blog_count + main_count} items cached")
        return blog_count + main_count


# API Response Caching
class APIResponseCache:
    """Cache API responses with proper invalidation."""

    @staticmethod
    def cache_api_response(
        view_name: str, response_data: Any, timeout: int = 300, **kwargs
    ):
        """Cache API response data."""
        cache_key = cache_key_generator("api", view_name, **kwargs)
        cache_manager.set(cache_key, response_data, timeout)
        return cache_key

    @staticmethod
    def get_cached_api_response(view_name: str, **kwargs):
        """Get cached API response."""
        cache_key = cache_key_generator("api", view_name, **kwargs)
        return cache_manager.get(cache_key)

    @staticmethod
    def invalidate_api_cache(view_name: str = None, pattern: str = None):
        """Invalidate API caches."""
        if pattern:
            cache_manager.delete_pattern(f"api_{pattern}*")
        elif view_name:
            cache_manager.delete_pattern(f"api_{view_name}*")
        else:
            cache_manager.delete_pattern("api_*")


# Template fragment caching
def cache_template_fragment(
    fragment_name: str, vary_on: List[str] = None, timeout: int = 600
):
    """Cache template fragments with versioning."""

    def get_cache_key():
        key_parts = [fragment_name]
        if vary_on:
            key_parts.extend(vary_on)
        return cache_key_generator("template_fragment", *key_parts)

    def get_fragment():
        cache_key = get_cache_key()
        return cache_manager.get(cache_key)

    def set_fragment(content: str):
        cache_key = get_cache_key()
        cache_manager.set(cache_key, content, timeout)

    return get_fragment, set_fragment
