"""
Django signals for intelligent cache invalidation.
Automatically clears cache when models are saved or deleted.
"""

import logging

from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

logger = logging.getLogger(__name__)

# Import cache manager for advanced invalidation
try:
    from .cache_utils import cache_manager
except ImportError:
    cache_manager = None
    logger.warning("cache_utils not available, using basic cache invalidation")

# Import models (conditional imports above are intentional)
from .models import (  # noqa: E402
    AITool,
    BlogPost,
    CybersecurityResource,
    PersonalInfo,
    SocialLink,
    UsefulResource,
)

try:
    from apps.blog.models import Post
except ImportError:
    Post = None

try:
    from apps.tools.models import Tool
except ImportError:
    Tool = None


# Enhanced cache invalidation handlers with smart pattern matching


@receiver([post_save, post_delete], sender=PersonalInfo)
def invalidate_personalinfo_cache(sender, instance, created=False, **kwargs):
    """
    Invalidate PersonalInfo related caches when saved or deleted.
    PersonalInfo affects: home page, personal page, and portfolio statistics.
    """
    try:
        if cache_manager:
            # Invalidate all home page data variations (handles time-based key patterns)
            cache_manager.invalidate_pattern("home_page_data_*")
            # Invalidate personal page
            cache_manager.invalidate_cache("personal_page_data")
            # Invalidate portfolio statistics
            cache_manager.invalidate_cache("portfolio_statistics")
        else:
            # Fallback to basic invalidation
            cache.delete("home_page_data")
            cache.delete("personal_page_data")
            cache.delete("portfolio_statistics")

        action = (
            "created"
            if created
            else ("updated" if kwargs.get("update_fields") is None else "updated")
        )
        logger.info(f"Cache invalidated on PersonalInfo {action}: {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating PersonalInfo cache: {e}")


@receiver([post_save, post_delete], sender=SocialLink)
def invalidate_sociallink_cache(sender, instance, created=False, **kwargs):
    """
    Invalidate SocialLink related caches.
    SocialLink affects: home page and personal page.
    """
    try:
        if cache_manager:
            cache_manager.invalidate_pattern("home_page_data_*")
            cache_manager.invalidate_cache("personal_page_data")
        else:
            cache.delete("home_page_data")
            cache.delete("personal_page_data")

        action = "created" if created else "updated"
        logger.info(f"Cache invalidated on SocialLink {action}: {instance.id}")
    except Exception as e:
        logger.error(f"Error invalidating SocialLink cache: {e}")


if Post:

    @receiver([post_save, post_delete], sender=Post)
    def invalidate_post_cache(sender, instance, created=False, **kwargs):
        """
        Invalidate blog Post related caches.
        Post affects: home page (recent posts) and blog pages.
        """
        try:
            if cache_manager:
                cache_manager.invalidate_pattern("home_page_data_*")
                cache_manager.invalidate_pattern("blog_posts_*")
            else:
                cache.delete("home_page_data")
                cache.delete("blog_posts")

            action = "created" if created else "updated"
            logger.info(f"Cache invalidated on Post {action}: {instance.id}")
        except Exception as e:
            logger.error(f"Error invalidating Post cache: {e}")


if Tool:

    @receiver([post_save, post_delete], sender=Tool)
    def invalidate_tool_cache(sender, instance, created=False, **kwargs):
        """
        Invalidate Tool related caches.
        Tool affects: home page (featured tools) and tool pages.
        """
        try:
            if cache_manager:
                cache_manager.invalidate_pattern("home_page_data_*")
                cache_manager.invalidate_pattern("tools_*")
            else:
                cache.delete("home_page_data")
                cache.delete("tools")

            action = "created" if created else "updated"
            logger.info(f"Cache invalidated on Tool {action}: {instance.id}")
        except Exception as e:
            logger.error(f"Error invalidating Tool cache: {e}")


if AITool:

    @receiver([post_save, post_delete], sender=AITool)
    def invalidate_aitool_cache(sender, instance, created=False, **kwargs):
        """
        Invalidate AITool related caches.
        AITool affects: home page (featured AI tools) and AI optimizer pages.
        """
        try:
            if cache_manager:
                cache_manager.invalidate_pattern("home_page_data_*")
                cache_manager.invalidate_pattern("ai_tools_*")
            else:
                cache.delete("home_page_data")
                cache.delete("ai_tools")

            action = "created" if created else "updated"
            logger.info(f"Cache invalidated on AITool {action}: {instance.id}")
        except Exception as e:
            logger.error(f"Error invalidating AITool cache: {e}")


def clear_home_cache(**kwargs):
    """
    Fallback cache clearing function (kept for backwards compatibility).
    """
    cache.delete("home_page_data")


# ============================================================================
# SEARCH INDEX SIGNALS
# ============================================================================


def sync_to_search_index(sender, instance, created, **kwargs):
    """
    Generic signal handler to sync model to search index.
    Called after save for searchable models.
    """
    import time

    start_time = time.time()
    success = False
    error_message = None

    try:
        from .monitoring import search_monitor
        from .search_index import search_index_manager

        # Index the document (will skip if not visible/published)
        result = search_index_manager.index_document(instance)
        success = result

        duration_ms = (time.time() - start_time) * 1000

        # Log to monitoring system
        search_monitor.log_index_sync(
            model_name=sender.__name__,
            operation="index",
            success=success,
            duration_ms=duration_ms,
            document_count=1,
            error=None if success else "Document not indexed (visibility check failed)",
        )

        logger.info(
            f"Search index updated: {sender.__name__} id={instance.id} ({duration_ms:.2f}ms)"
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_message = str(e)

        # Log error to monitoring
        try:
            from .monitoring import search_monitor

            search_monitor.log_index_sync(
                model_name=sender.__name__,
                operation="index",
                success=False,
                duration_ms=duration_ms,
                document_count=1,
                error=error_message,
            )
        except Exception:
            # Monitoring may not be available
            pass

        logger.error(
            f"Failed to index {sender.__name__} id={instance.id}: {e}", exc_info=True
        )


def remove_from_search_index(sender, instance, **kwargs):
    """
    Generic signal handler to remove document from search index.
    Called before delete for searchable models.
    """
    import time

    start_time = time.time()
    success = False
    error_message = None

    try:
        from .monitoring import search_monitor
        from .search_index import search_index_manager

        # Delete from index
        result = search_index_manager.delete_document(sender.__name__, instance.id)
        success = result

        duration_ms = (time.time() - start_time) * 1000

        # Log to monitoring system
        search_monitor.log_index_sync(
            model_name=sender.__name__,
            operation="delete",
            success=success,
            duration_ms=duration_ms,
            document_count=1,
            error=None,
        )

        logger.info(
            f"Search index removed: {sender.__name__} id={instance.id} ({duration_ms:.2f}ms)"
        )

    except Exception as e:
        duration_ms = (time.time() - start_time) * 1000
        error_message = str(e)

        # Log error to monitoring
        try:
            from .monitoring import search_monitor

            search_monitor.log_index_sync(
                model_name=sender.__name__,
                operation="delete",
                success=False,
                duration_ms=duration_ms,
                document_count=1,
                error=error_message,
            )
        except Exception:
            # Monitoring may not be available
            pass

        logger.error(
            f"Failed to remove {sender.__name__} id={instance.id} from index: {e}",
            exc_info=True,
        )


# Register search index signals for indexable models

# BlogPost (from apps.main.models)


@receiver([post_save], sender=BlogPost)
def index_blogpost_on_save(sender, instance, created=False, **kwargs):
    """Index BlogPost to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=BlogPost)
def remove_blogpost_on_delete(sender, instance, **kwargs):
    """Remove BlogPost from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


@receiver([post_save], sender=AITool)
def index_aitool_on_save(sender, instance, created=False, **kwargs):
    """Index AITool to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=AITool)
def remove_aitool_on_delete(sender, instance, **kwargs):
    """Remove AITool from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


@receiver([post_save], sender=UsefulResource)
def index_usefulresource_on_save(sender, instance, created=False, **kwargs):
    """Index UsefulResource to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=UsefulResource)
def remove_usefulresource_on_delete(sender, instance, **kwargs):
    """Remove UsefulResource from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


@receiver([post_save], sender=CybersecurityResource)
def index_cybersecurity_on_save(sender, instance, created=False, **kwargs):
    """Index CybersecurityResource to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=CybersecurityResource)
def remove_cybersecurity_on_delete(sender, instance, **kwargs):
    """Remove CybersecurityResource from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


@receiver([post_save], sender=PersonalInfo)
def index_personalinfo_on_save(sender, instance, created=False, **kwargs):
    """Index PersonalInfo to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=PersonalInfo)
def remove_personalinfo_on_delete(sender, instance, **kwargs):
    """Remove PersonalInfo from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


@receiver([post_save], sender=SocialLink)
def index_sociallink_on_save(sender, instance, created=False, **kwargs):
    """Index SocialLink to search engine on save"""
    sync_to_search_index(sender, instance, created, **kwargs)


@receiver([post_delete], sender=SocialLink)
def remove_sociallink_on_delete(sender, instance, **kwargs):
    """Remove SocialLink from search engine on delete"""
    remove_from_search_index(sender, instance, **kwargs)


# Try to register Tool model signals if available
if Tool:

    @receiver([post_save], sender=Tool)
    def index_tool_on_save(sender, instance, created=False, **kwargs):
        """Index Tool to search engine on save"""
        sync_to_search_index(sender, instance, created, **kwargs)

    @receiver([post_delete], sender=Tool)
    def remove_tool_on_delete(sender, instance, **kwargs):
        """Remove Tool from search engine on delete"""
        remove_from_search_index(sender, instance, **kwargs)
