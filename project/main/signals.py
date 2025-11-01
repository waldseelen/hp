from django.core.cache import cache
from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from blog.models import Post
from tools.models import Tool

from apps.portfolio.cache_keys import invalidate_model_cache

from .models import PersonalInfo, SocialLink


@receiver([post_save, post_delete], sender=PersonalInfo)
@receiver([post_save, post_delete], sender=SocialLink)
@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Tool)
def clear_home_cache(sender, instance, **kwargs):
    """Invalidate cache when models change using centralized cache manager"""
    model_label = f"{sender._meta.app_label}.{sender._meta.model_name}"
    invalidate_model_cache(
        model_label, instance.id if hasattr(instance, "id") else None
    )
