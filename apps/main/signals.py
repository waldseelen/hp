from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from .models import PersonalInfo, SocialLink
from apps.blog.models import Post
from apps.tools.models import Tool

@receiver([post_save, post_delete], sender=PersonalInfo)
@receiver([post_save, post_delete], sender=SocialLink)
@receiver([post_save, post_delete], sender=Post)
@receiver([post_save, post_delete], sender=Tool)
def clear_home_cache(**kwargs):
    cache.delete('home_page_data')