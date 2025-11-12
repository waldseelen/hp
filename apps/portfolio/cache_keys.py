"""
Centralized Cache Key Management System
Manages all cache keys used across the application with automatic invalidation.
"""

import hashlib
import json
from typing import Any, Dict, List, Optional

from django.core.cache import cache


class CacheKeyManager:
    """
    Centralized cache key management with automatic invalidation mapping.

    This class provides:
    - Centralized cache key definitions
    - Model-to-cache key mapping for automatic invalidation
    - Pattern-based cache invalidation
    - Cache key generation utilities
    """

    # Cache key definitions organized by feature
    CACHE_KEYS = {
        # Home page related
        "home_page_data": "home:page_data",
        "home_personal_info_visible": "home:personal_info:visible",
        "home_social_links_visible": "home:social_links:visible",
        "home_recent_posts": "home:recent_posts",
        "home_featured_tools": "home:featured_tools",
        "home_featured_ai_tools": "home:featured_ai_tools",
        "home_urgent_security": "home:urgent_security",
        "home_featured_blog_categories": "home:featured_blog_categories",
        # Personal page related
        "personal_page_data": "personal:page_data",
        "personal_personal_info_all": "personal:personal_info:all",
        "personal_social_links_all": "personal:social_links:all",
        # Blog related
        "blog_published_posts": "blog:published_posts",
        "blog_popular_posts": "blog:popular_posts",
        "blog_blog_categories": "blog:categories",
        # Tools related
        "tools_visible_tools": "tools:visible_tools",
        "tools_featured_tools": "tools:featured_tools",
        "tools_tools_by_category": "tools:by_category",
        "projects_page_data": "projects:page_data",
        # Music and other pages
        "music_page_data": "music:page_data",
        "useful_page_data": "useful:page_data",
        # Template fragments
        "template.cache.personal_info_section": "template:personal_info_section",
        "template.cache.social_links_section": "template:social_links_section",
        "template.cache.recent_posts_section": "template:recent_posts_section",
        "template.cache.featured_ai_tools_section": "template:featured_ai_tools_section",
        "template.cache.urgent_security_section": "template:urgent_security_section",
        # API responses
        "api_response_personal": "api:response:personal",
        "api_response_social": "api:response:social",
        "api_response_blog": "api:response:blog",
        "api_response_tools": "api:response:tools",
    }

    # Model-to-cache key mapping for automatic invalidation
    MODEL_CACHE_MAPPING = {
        "main.PersonalInfo": [
            "home_page_data",
            "home_personal_info_visible",
            "personal_page_data",
            "personal_personal_info_all",
            "template.cache.personal_info_section",
            "api_response_personal",
        ],
        "main.SocialLink": [
            "home_page_data",
            "home_social_links_visible",
            "personal_page_data",
            "personal_social_links_all",
            "template.cache.social_links_section",
            "api_response_social",
        ],
        "blog.Post": [
            "home_page_data",
            "home_recent_posts",
            "personal_page_data",
            "blog_published_posts",
            "blog_popular_posts",
            "template.cache.recent_posts_section",
            "api_response_blog",
        ],
        "tools.Tool": [
            "home_page_data",
            "home_featured_tools",
            "tools_visible_tools",
            "tools_featured_tools",
            "tools_tools_by_category",
            "projects_page_data",
            "api_response_tools",
        ],
        "portfolio.AITool": [
            "home_page_data",
            "home_featured_ai_tools",
            "template.cache.featured_ai_tools_section",
        ],
        "portfolio.CybersecurityResource": [
            "home_page_data",
            "home_urgent_security",
            "template.cache.urgent_security_section",
        ],
        "portfolio.BlogCategory": [
            "home_page_data",
            "home_featured_blog_categories",
            "blog_blog_categories",
        ],
        "portfolio.MusicPlaylist": [
            "music_page_data",
        ],
        "portfolio.UsefulResource": [
            "useful_page_data",
        ],
    }

    # Pattern mappings for broader invalidation
    PATTERN_MAPPING = {
        "personal_info": [
            "personal_info*",
            "queryset_*personalinfo*",
            "api_*personal*",
        ],
        "social_links": ["social_links*"],
        "blog": ["blog*", "recent_posts*"],
        "tools": ["tools*", "projects*"],
        "ai_tools": ["ai_tools*"],
        "security": ["security*"],
        "blog_cat": ["blog_cat*"],
        "music": ["music*"],
        "useful": ["useful*"],
    }

    @classmethod
    def get_cache_key(cls, key_name: str, *args, **kwargs) -> str:
        """
        Get a cache key with optional parameters.

        Args:
            key_name: Name of the cache key from CACHE_KEYS
            *args: Positional arguments to append
            **kwargs: Keyword arguments to hash and append

        Returns:
            str: The complete cache key
        """
        if key_name not in cls.CACHE_KEYS:
            raise ValueError(f"Unknown cache key: {key_name}")

        base_key = cls.CACHE_KEYS[key_name]
        key_parts = [base_key]

        # Add positional arguments
        if args:
            key_parts.extend(str(arg) for arg in args)

        # Add hashed kwargs if present
        if kwargs:
            kwargs_str = json.dumps(kwargs, sort_keys=True, default=str)
            kwargs_hash = hashlib.md5(
                kwargs_str.encode(), usedforsecurity=False
            ).hexdigest()[:8]
            key_parts.append(kwargs_hash)

        return ":".join(key_parts)[:250]  # Redis key limit

    @classmethod
    def get_keys_for_model(cls, model_label: str) -> List[str]:
        """
        Get all cache keys that should be invalidated when a model changes.

        Args:
            model_label: Django model label (app.Model)

        Returns:
            List[str]: List of cache key names to invalidate
        """
        return cls.MODEL_CACHE_MAPPING.get(model_label, [])

    @classmethod
    def get_patterns_for_model(cls, model_label: str) -> List[str]:
        """
        Get cache key patterns to invalidate for a model.

        Args:
            model_label: Django model label (app.Model)

        Returns:
            List[str]: List of pattern names
        """
        # Extract model name from label (e.g., 'main.PersonalInfo' -> 'personal_info')
        model_name = model_label.split(".")[-1].lower()
        return cls.PATTERN_MAPPING.get(model_name, [])

    @classmethod
    def invalidate_model_cache(
        cls, model_label: str, instance_id: Optional[int] = None
    ) -> None:
        """
        Invalidate all cache keys associated with a model.

        Args:
            model_label: Django model label (app.Model)
            instance_id: Optional instance ID for specific invalidation
        """
        # Invalidate specific keys
        keys_to_clear = cls.get_keys_for_model(model_label)
        for key_name in keys_to_clear:
            try:
                cache_key = cls.get_cache_key(key_name)
                cache.delete(cache_key)

                # Also try instance-specific keys
                if instance_id:
                    instance_key = cls.get_cache_key(key_name, instance_id)
                    cache.delete(instance_key)
            except Exception as e:
                # Log but don't fail
                print(f"Error clearing cache key {key_name}: {e}")

        # Invalidate patterns
        patterns = cls.get_patterns_for_model(model_label)
        for pattern in patterns:
            cls.invalidate_pattern(pattern)

    @classmethod
    def invalidate_pattern(cls, pattern: str) -> None:
        """
        Invalidate cache keys matching a pattern (requires Redis).

        Args:
            pattern: Pattern to match (e.g., 'blog*')
        """
        try:
            from django_redis import get_redis_connection

            redis_conn = get_redis_connection("default")
            keys = redis_conn.keys(f"portfolio:{pattern}")
            if keys:
                redis_conn.delete(*keys)
        except ImportError:
            # Fallback for non-Redis backends - can't do pattern matching
            pass
        except Exception as e:
            print(f"Error invalidating pattern {pattern}: {e}")

    @classmethod
    def clear_all_cache(cls) -> None:
        """Clear all application cache keys."""
        for key_name in cls.CACHE_KEYS.keys():
            try:
                cache_key = cls.get_cache_key(key_name)
                cache.delete(cache_key)
            except Exception as e:
                print(f"Error clearing cache key {key_name}: {e}")

        # Clear patterns
        for patterns in cls.PATTERN_MAPPING.values():
            for pattern in patterns:
                cls.invalidate_pattern(pattern)

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get cache statistics and key information.

        Returns:
            Dict containing cache stats and key counts
        """
        return {
            "total_keys": len(cls.CACHE_KEYS),
            "total_models": len(cls.MODEL_CACHE_MAPPING),
            "total_patterns": len(cls.PATTERN_MAPPING),
            "keys_by_category": {
                "home": len(
                    [k for k in cls.CACHE_KEYS.keys() if k.startswith("home_")]
                ),
                "personal": len(
                    [k for k in cls.CACHE_KEYS.keys() if k.startswith("personal_")]
                ),
                "blog": len(
                    [k for k in cls.CACHE_KEYS.keys() if k.startswith("blog_")]
                ),
                "tools": len(
                    [k for k in cls.CACHE_KEYS.keys() if k.startswith("tools_")]
                ),
                "template": len(
                    [k for k in cls.CACHE_KEYS.keys() if k.startswith("template")]
                ),
                "api": len([k for k in cls.CACHE_KEYS.keys() if k.startswith("api_")]),
            },
        }


# Convenience functions for easy access
def get_cache_key(key_name: str, *args, **kwargs) -> str:
    """Convenience function to get cache key."""
    return CacheKeyManager.get_cache_key(key_name, *args, **kwargs)


def invalidate_model_cache(model_label: str, instance_id: Optional[int] = None) -> None:
    """Convenience function to invalidate model cache."""
    CacheKeyManager.invalidate_model_cache(model_label, instance_id)


def clear_all_cache() -> None:
    """Convenience function to clear all cache."""
    CacheKeyManager.clear_all_cache()
