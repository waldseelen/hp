"""
Django signals for intelligent cache invalidation.
Automatically clears cache when models are saved or deleted.
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
import logging

logger = logging.getLogger(__name__)

# Import cache manager for advanced invalidation
try:
    from .cache_utils import cache_manager
except ImportError:
    cache_manager = None
    logger.warning("cache_utils not available, using basic cache invalidation")

# Import models
from .models import PersonalInfo, SocialLink

try:
    from apps.blog.models import Post
except ImportError:
    Post = None

try:
    from apps.tools.models import Tool
except ImportError:
    Tool = None

try:
    from apps.ai_optimizer.models import AITool
except (ImportError, RuntimeError):
    AITool = None


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
            cache_manager.invalidate_pattern('home_page_data_*')
            # Invalidate personal page
            cache_manager.invalidate_cache('personal_page_data')
            # Invalidate portfolio statistics
            cache_manager.invalidate_cache('portfolio_statistics')
        else:
            # Fallback to basic invalidation
            cache.delete('home_page_data')
            cache.delete('personal_page_data')
            cache.delete('portfolio_statistics')

        action = "created" if created else ("updated" if kwargs.get('update_fields') is None else "updated")
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
            cache_manager.invalidate_pattern('home_page_data_*')
            cache_manager.invalidate_cache('personal_page_data')
        else:
            cache.delete('home_page_data')
            cache.delete('personal_page_data')

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
                cache_manager.invalidate_pattern('home_page_data_*')
                cache_manager.invalidate_pattern('blog_posts_*')
            else:
                cache.delete('home_page_data')
                cache.delete('blog_posts')

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
                cache_manager.invalidate_pattern('home_page_data_*')
                cache_manager.invalidate_pattern('tools_*')
            else:
                cache.delete('home_page_data')
                cache.delete('tools')

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
                cache_manager.invalidate_pattern('home_page_data_*')
                cache_manager.invalidate_pattern('ai_tools_*')
            else:
                cache.delete('home_page_data')
                cache.delete('ai_tools')

            action = "created" if created else "updated"
            logger.info(f"Cache invalidated on AITool {action}: {instance.id}")
        except Exception as e:
            logger.error(f"Error invalidating AITool cache: {e}")


def clear_home_cache(**kwargs):
    """
    Fallback cache clearing function (kept for backwards compatibility).
    """
    cache.delete('home_page_data')
