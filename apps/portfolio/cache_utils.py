"""
Cache utility functions and decorators for optimized performance
"""

import hashlib
import json
from functools import wraps
from typing import Any, Callable, Dict, List

from django.contrib.auth.models import AnonymousUser
from django.core.cache import cache
from django.db.models import QuerySet


class CacheManager:
    """Centralized cache management with automatic invalidation"""

    # Cache timeouts (in seconds)
    TIMEOUTS = {
        "short": 300,  # 5 minutes
        "medium": 1800,  # 30 minutes
        "long": 3600,  # 1 hour
        "very_long": 86400,  # 1 day
    }

    # Cache key prefixes
    PREFIXES = {
        "blog_posts": "blog:posts",
        "tools": "tools:data",
        "personal_info": "main:personal",
        "social_links": "main:social",
        "ai_tools": "main:ai_tools",
        "performance": "perf:metrics",
        "api_response": "api:response",
        "template_fragment": "template:fragment",
    }

    @classmethod
    def make_key(cls, prefix: str, *args, **kwargs) -> str:
        """Generate cache key with prefix"""
        key_parts = [str(arg) for arg in args]

        # Add kwargs as sorted string
        if kwargs:
            kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
            key_parts.append(
                hashlib.md5(kwargs_str.encode(), usedforsecurity=False).hexdigest()[:8]
            )

        key = ":".join([prefix] + key_parts)
        return key[:250]  # Memcached key limit

    @classmethod
    def get_or_set(cls, key: str, callable_func: Callable, timeout: int = None) -> Any:
        """Get from cache or set if not exists"""
        if timeout is None:
            timeout = cls.TIMEOUTS["medium"]

        cached_value = cache.get(key)
        if cached_value is not None:
            return cached_value

        # Call function and cache result
        value = callable_func()
        cache.set(key, value, timeout)
        return value

    @classmethod
    def invalidate_pattern(cls, pattern: str):
        """Invalidate cache keys matching pattern"""
        # Note: This requires Redis backend for pattern matching
        try:
            from django_redis import get_redis_connection

            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(f"*{pattern}*")
            if keys:
                redis_conn.delete(*keys)
        except ImportError:
            # Fallback for non-Redis backends
            pass

    @classmethod
    def warm_cache(cls, cache_funcs: List[Dict]):
        """Warm up cache with frequently accessed data"""
        for func_config in cache_funcs:
            try:
                func = func_config["func"]
                key = func_config["key"]
                timeout = func_config.get("timeout", cls.TIMEOUTS["long"])

                # Only warm if not already cached
                if cache.get(key) is None:
                    value = func()
                    cache.set(key, value, timeout)
            except Exception as e:
                # Log error but don't break warming process
                print(f"Cache warming error for {key}: {e}")


def cache_result(
    timeout: int = None, key_prefix: str = "default", vary_on: List[str] = None
):
    """
    Decorator to cache function results

    Args:
        timeout: Cache timeout in seconds
        key_prefix: Prefix for cache key
        vary_on: List of argument names to include in cache key
    """

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Build cache key
            key_parts = [key_prefix, func.__name__]

            # Add specified args to key
            if vary_on:
                for param_name in vary_on:
                    if param_name in kwargs:
                        key_parts.append(f"{param_name}:{kwargs[param_name]}")

            cache_key = CacheManager.make_key("func", *key_parts)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_timeout = timeout or CacheManager.TIMEOUTS["medium"]
            cache.set(cache_key, result, cache_timeout)

            return result

        return wrapper

    return decorator


def cache_queryset(timeout: int = None, key_suffix: str = ""):
    """Cache Django QuerySet results"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key from function name and args
            key_parts = [func.__name__, key_suffix]
            if args:
                key_parts.extend([str(arg) for arg in args[:3]])  # Limit args
            if kwargs:
                sorted_kwargs = sorted(kwargs.items())[:5]  # Limit kwargs
                key_parts.extend([f"{k}:{v}" for k, v in sorted_kwargs])

            cache_key = CacheManager.make_key("queryset", *key_parts)

            # Check cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Execute query and cache
            result = func(*args, **kwargs)

            # Convert QuerySet to list for caching
            if isinstance(result, QuerySet):
                result = list(result)

            cache_timeout = timeout or CacheManager.TIMEOUTS["medium"]
            cache.set(cache_key, result, cache_timeout)

            return result

        return wrapper

    return decorator


def cache_page_data(page_name: str, timeout: int = None):
    """Cache page-specific data"""

    def decorator(func: Callable):
        @wraps(func)
        def wrapper(request, *args, **kwargs):
            # Create cache key based on page and user state
            user_key = (
                "anonymous"
                if isinstance(request.user, AnonymousUser)
                else str(request.user.id)
            )
            cache_key = CacheManager.make_key(
                "page", page_name, user_key, *[str(arg) for arg in args]
            )

            # Check cache
            cached_data = cache.get(cache_key)
            if cached_data is not None:
                return cached_data

            # Generate data and cache
            data = func(request, *args, **kwargs)
            cache_timeout = timeout or CacheManager.TIMEOUTS["short"]
            cache.set(cache_key, data, cache_timeout)

            return data

        return wrapper

    return decorator


class ModelCacheManager:
    """Cache manager for model instances and querysets"""

    @staticmethod
    def get_model_cache_key(
        model_class, obj_id: int = None, filter_params: dict = None
    ):
        """Generate consistent cache keys for models"""
        model_name = f"{model_class._meta.app_label}.{model_class._meta.model_name}"

        if obj_id:
            return f"model:{model_name}:obj:{obj_id}"
        elif filter_params:
            params_str = json.dumps(filter_params, sort_keys=True)
            params_hash = hashlib.md5(
                params_str.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            return f"model:{model_name}:query:{params_hash}"
        else:
            return f"model:{model_name}:all"

    @staticmethod
    def cache_model_instance(instance, timeout: int = None):
        """Cache a model instance"""
        cache_key = ModelCacheManager.get_model_cache_key(
            instance.__class__, instance.pk
        )
        cache_timeout = timeout or CacheManager.TIMEOUTS["long"]
        cache.set(cache_key, instance, cache_timeout)

    @staticmethod
    def get_cached_instance(model_class, obj_id: int):
        """Get cached model instance"""
        cache_key = ModelCacheManager.get_model_cache_key(model_class, obj_id)
        return cache.get(cache_key)

    @staticmethod
    def invalidate_model_cache(model_class, obj_id: int = None):
        """Invalidate cache for specific model"""
        if obj_id:
            cache_key = ModelCacheManager.get_model_cache_key(model_class, obj_id)
            cache.delete(cache_key)
        else:
            # Invalidate all cache for this model
            model_name = f"{model_class._meta.app_label}.{model_class._meta.model_name}"
            CacheManager.invalidate_pattern(f"model:{model_name}")


# Pre-configured cache decorators for common use cases
cache_short = cache_result(timeout=CacheManager.TIMEOUTS["short"])
cache_medium = cache_result(timeout=CacheManager.TIMEOUTS["medium"])
cache_long = cache_result(timeout=CacheManager.TIMEOUTS["long"])
cache_very_long = cache_result(timeout=CacheManager.TIMEOUTS["very_long"])

# QuerySet caching decorators
cache_queryset_short = cache_queryset(timeout=CacheManager.TIMEOUTS["short"])
cache_queryset_medium = cache_queryset(timeout=CacheManager.TIMEOUTS["medium"])
cache_queryset_long = cache_queryset(timeout=CacheManager.TIMEOUTS["long"])


class CacheMonitor:
    """Monitor cache performance and generate statistics"""

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """Get cache statistics if available"""
        from django.conf import settings  # noqa: F811

        stats = {
            "cache_backend": getattr(settings, "CACHES", {})
            .get("default", {})
            .get("BACKEND", "Unknown"),
            "cache_available": True,
            "connectivity": "OK",
        }

        try:
            # Test cache connectivity
            test_key = "cache_monitor_test"
            cache.set(test_key, "test", 1)
            if cache.get(test_key) == "test":
                stats["connectivity"] = "OK"
                cache.delete(test_key)
            else:
                stats["connectivity"] = "ERROR"

            # Try to get backend-specific stats if available
            if hasattr(cache, "_cache") and hasattr(cache._cache, "get_client"):
                try:
                    client = cache._cache.get_client()
                    if hasattr(client, "info"):
                        redis_info = client.info()
                        stats.update(
                            {
                                "redis_version": redis_info.get("redis_version"),
                                "used_memory": redis_info.get("used_memory_human"),
                                "keyspace_hits": redis_info.get("keyspace_hits", 0),
                                "keyspace_misses": redis_info.get("keyspace_misses", 0),
                            }
                        )

                        # Calculate hit ratio
                        hits = redis_info.get("keyspace_hits", 0)
                        misses = redis_info.get("keyspace_misses", 0)
                        if hits + misses > 0:
                            stats["hit_ratio"] = round(hits / (hits + misses) * 100, 2)
                except Exception:
                    # Redis not available or other error
                    pass

        except Exception as e:
            stats["connectivity"] = f"ERROR: {str(e)}"
            stats["cache_available"] = False

        return stats
