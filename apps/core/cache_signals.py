"""
Cache invalidation signals for automatic cache clearing.

This module provides signal handlers that automatically invalidate
relevant cache keys when models are saved or deleted.
"""

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blog.models import Post as BlogPost
from apps.main.models import BlogPost as MainBlogPost
from apps.main.models import PersonalInfo, SocialLink
from apps.portfolio.models import BlogPost as PortfolioBlogPost
from apps.tools.models import Tool


@receiver(post_save, sender=BlogPost)
@receiver(post_delete, sender=BlogPost)
def invalidate_blog_post_cache(sender, instance, **kwargs):
    """
    Invalidate blog post caches when a post is saved or deleted.

    Cache keys invalidated:
    - Post detail page
    - Blog list page
    - Related posts
    - Popular posts
    - Tag cloud
    """
    cache_keys = [
        f"blog_post_detail_{instance.slug}",
        f"blog_post_{instance.pk}",
        "blog_post_list",
        "blog_recent_posts",
        "blog_popular_posts",
        "blog_tag_cloud",
    ]

    # Invalidate author's posts cache
    if instance.author:
        cache_keys.append(f"blog_author_posts_{instance.author.pk}")

    # Invalidate tag-related caches
    if instance.tags:
        for tag in instance.tags:
            cache_keys.append(f"blog_tag_{tag}")

    cache.delete_many(cache_keys)


@receiver(post_save, sender=MainBlogPost)
@receiver(post_delete, sender=MainBlogPost)
def invalidate_main_blog_cache(sender, instance, **kwargs):
    """Invalidate main app blog post caches."""
    cache_keys = [
        f"main_post_detail_{instance.slug}",
        f"main_post_{instance.pk}",
        "main_post_list",
        "main_recent_posts",
    ]
    cache.delete_many(cache_keys)


@receiver(post_save, sender=PortfolioBlogPost)
@receiver(post_delete, sender=PortfolioBlogPost)
def invalidate_portfolio_blog_cache(sender, instance, **kwargs):
    """Invalidate portfolio app blog post caches."""
    cache_keys = [
        f"portfolio_post_detail_{instance.slug}",
        f"portfolio_post_{instance.pk}",
        "portfolio_post_list",
        "portfolio_recent_posts",
    ]
    cache.delete_many(cache_keys)


@receiver(post_save, sender=Tool)
@receiver(post_delete, sender=Tool)
def invalidate_tool_cache(sender, instance, **kwargs):
    """
    Invalidate tool caches when a tool is saved or deleted.

    Cache keys invalidated:
    - Tool detail page
    - Tool list page
    - Category tools
    - Featured tools
    - Similar tools
    """
    cache_keys = [
        f"tool_detail_{instance.pk}",
        f"tool_{instance.pk}",
        "tool_list",
        "featured_tools",
    ]

    # Invalidate category cache
    if instance.category:
        cache_keys.append(f"tool_category_{instance.category}")

    # Invalidate similar tools cache
    cache_keys.append(f"similar_tools_{instance.pk}")

    cache.delete_many(cache_keys)


# Additional cache utility functions


def invalidate_search_cache():
    """
    Invalidate all search-related caches.
    Call this after reindexing or when search results may have changed.
    """
    pattern_keys = [
        "search_*",
        "tag_cloud_*",
        "popular_tags_*",
    ]

    for pattern in pattern_keys:
        # Note: Redis backend required for pattern deletion
        try:
            cache.delete_pattern(pattern)
        except AttributeError:
            # Fallback for non-Redis backends
            pass


def invalidate_all_blog_caches():
    """
    Invalidate all blog-related caches.
    Useful after bulk operations or major changes.
    """
    cache_keys = [
        "blog_post_list",
        "blog_recent_posts",
        "blog_popular_posts",
        "blog_tag_cloud",
        "main_post_list",
        "main_recent_posts",
        "portfolio_post_list",
        "portfolio_recent_posts",
    ]
    cache.delete_many(cache_keys)


def invalidate_all_tool_caches():
    """
    Invalidate all tool-related caches.
    Useful after bulk operations or major changes.
    """
    cache_keys = [
        "tool_list",
        "featured_tools",
        "tool_categories",
    ]
    cache.delete_many(cache_keys)


@receiver(post_save, sender=PersonalInfo)
@receiver(post_delete, sender=PersonalInfo)
def invalidate_personal_info_cache(sender, instance, **kwargs):
    """
    Invalidate personal info caches when PersonalInfo is saved or deleted.

    Cache keys invalidated:
    - Home page data
    - Personal page data
    - About page data
    """
    cache_keys = [
        "home_page_data",
        "personal_page_data",
        "about_page_data",
    ]
    # Also invalidate user-specific caches
    from django.contrib.auth import get_user_model

    User = get_user_model()
    for user in User.objects.all()[:100]:  # Limit to first 100 users
        cache_keys.append(f"home_page_data_user{user.pk}")

    cache.delete_many(cache_keys)


@receiver(post_save, sender=SocialLink)
@receiver(post_delete, sender=SocialLink)
def invalidate_social_link_cache(sender, instance, **kwargs):
    """
    Invalidate social link caches when SocialLink is saved or deleted.

    Cache keys invalidated:
    - Personal page data
    - Footer social links
    - Contact page data
    """
    cache_keys = [
        "personal_page_data",
        "footer_social_links",
        "contact_page_data",
    ]
    cache.delete_many(cache_keys)
