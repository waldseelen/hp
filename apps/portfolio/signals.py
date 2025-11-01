from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from apps.blog.models import Post

from .cache_keys import invalidate_model_cache
from .models import (
    AITool,
    BlogCategory,
    CybersecurityResource,
    MusicPlaylist,
    PersonalInfo,
    SocialLink,
    UsefulResource,
)

try:
    from apps.tools.models import Tool
except ImportError:
    Tool = None

import logging

logger = logging.getLogger(__name__)


@receiver([post_save, post_delete], sender=PersonalInfo)
def invalidate_personal_info_cache(sender, instance, **kwargs):
    """Invalidate cache when PersonalInfo changes"""
    try:
        # Use centralized cache invalidation
        invalidate_model_cache(
            "portfolio.PersonalInfo", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated PersonalInfo cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating PersonalInfo cache: {e}")


@receiver([post_save, post_delete], sender=SocialLink)
def invalidate_social_links_cache(sender, instance, **kwargs):
    """Invalidate cache when SocialLink changes"""
    try:
        invalidate_model_cache(
            "portfolio.SocialLink", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated SocialLink cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating SocialLink cache: {e}") @ receiver(
            [post_save, post_delete], sender=Post
        )


def invalidate_blog_cache(sender, instance, **kwargs):
    """Invalidate cache when Post changes"""
    try:
        invalidate_model_cache(
            "blog.Post", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated Post cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating Post cache: {e}")


if Tool:

    @receiver([post_save, post_delete], sender=Tool)
    def invalidate_tools_cache(sender, instance, **kwargs):
        """Invalidate cache when Tool changes"""
        try:
            invalidate_model_cache(
                "tools.Tool", instance.id if hasattr(instance, "id") else None
            )

            logger.info(
                f"Invalidated Tool cache after {kwargs.get('signal', 'unknown')} signal"
            )

        except Exception as e:
            logger.error(f"Error invalidating Tool cache: {e}")


@receiver([post_save, post_delete], sender=AITool)
def invalidate_ai_tools_cache(sender, instance, **kwargs):
    """Invalidate cache when AITool changes"""
    try:
        invalidate_model_cache(
            "portfolio.AITool", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated AITool cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating AITool cache: {e}")


@receiver([post_save, post_delete], sender=CybersecurityResource)
def invalidate_security_cache(sender, instance, **kwargs):
    """Invalidate cache when CybersecurityResource changes"""
    try:
        invalidate_model_cache(
            "portfolio.CybersecurityResource",
            instance.id if hasattr(instance, "id") else None,
        )

        logger.info(
            f"Invalidated CybersecurityResource cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating CybersecurityResource cache: {e}")


@receiver([post_save, post_delete], sender=BlogCategory)
def invalidate_blog_category_cache(sender, instance, **kwargs):
    """Invalidate cache when BlogCategory changes"""
    try:
        invalidate_model_cache(
            "portfolio.BlogCategory", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated BlogCategory cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating BlogCategory cache: {e}")


@receiver([post_save, post_delete], sender=MusicPlaylist)
def invalidate_music_cache(sender, instance, **kwargs):
    """Invalidate cache when MusicPlaylist changes"""
    try:
        invalidate_model_cache(
            "portfolio.MusicPlaylist", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated MusicPlaylist cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating MusicPlaylist cache: {e}")


@receiver([post_save, post_delete], sender=UsefulResource)
def invalidate_useful_cache(sender, instance, **kwargs):
    """Invalidate cache when UsefulResource changes"""
    try:
        invalidate_model_cache(
            "portfolio.UsefulResource", instance.id if hasattr(instance, "id") else None
        )

        logger.info(
            f"Invalidated UsefulResource cache after {kwargs.get('signal', 'unknown')} signal"
        )

    except Exception as e:
        logger.error(f"Error invalidating UsefulResource cache: {e}")
