from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.template.loader import get_template
from django.template import TemplateDoesNotExist
from .cache_utils import CacheManager
from .models import PersonalInfo, SocialLink, AITool, CybersecurityResource, BlogCategory, MusicPlaylist, UsefulResource
from apps.blog.models import Post
from apps.tools.models import Tool
import logging

logger = logging.getLogger(__name__)

@receiver([post_save, post_delete], sender=PersonalInfo)
def invalidate_personal_info_cache(sender, instance, **kwargs):
    """Invalidate cache when PersonalInfo changes"""
    try:
        # Clear specific cache keys
        cache_keys_to_clear = [
            'home_personal_info_visible',
            'personal_personal_info_all', 
            'home_page_data',
            'personal_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
        
        # Clear template fragments
        try:
            cache.delete('template.cache.personal_info_section')
        except:
            pass
            
        # Clear pattern-based cache
        CacheManager.delete_pattern('personal_info*')
        
        logger.info(f"Invalidated PersonalInfo cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating PersonalInfo cache: {e}")

@receiver([post_save, post_delete], sender=SocialLink)
def invalidate_social_links_cache(sender, instance, **kwargs):
    """Invalidate cache when SocialLink changes"""
    try:
        cache_keys_to_clear = [
            'home_social_links_visible',
            'personal_social_links_all',
            'home_page_data',
            'personal_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        # Clear template fragments
        try:
            cache.delete('template.cache.social_links_section')
        except:
            pass
            
        CacheManager.delete_pattern('social_links*')
        
        logger.info(f"Invalidated SocialLink cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating SocialLink cache: {e}")

@receiver([post_save, post_delete], sender=Post)
def invalidate_blog_cache(sender, instance, **kwargs):
    """Invalidate cache when Post changes"""
    try:
        cache_keys_to_clear = [
            'home_recent_posts',
            'blog_published_posts',
            'blog_popular_posts',
            'home_page_data',
            f'blog_related_{instance.id}' if instance.id else None
        ]
        
        # Remove None values
        cache_keys_to_clear = [key for key in cache_keys_to_clear if key]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        # Clear template fragments
        try:
            cache.delete('template.cache.recent_posts_section')
        except:
            pass
            
        # Clear blog-specific patterns
        CacheManager.delete_pattern('blog*')
        CacheManager.delete_pattern('recent_posts*')
        
        logger.info(f"Invalidated Post cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating Post cache: {e}")

@receiver([post_save, post_delete], sender=Tool)  
def invalidate_tools_cache(sender, instance, **kwargs):
    """Invalidate cache when Tool changes"""
    try:
        cache_keys_to_clear = [
            'home_featured_tools',
            'tools_visible_tools',
            'tools_featured_tools', 
            'tools_tools_by_category',
            'projects_page_data',
            'home_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        CacheManager.delete_pattern('tools*')
        CacheManager.delete_pattern('projects*')
        
        logger.info(f"Invalidated Tool cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating Tool cache: {e}")

@receiver([post_save, post_delete], sender=AITool)
def invalidate_ai_tools_cache(sender, instance, **kwargs):
    """Invalidate cache when AITool changes"""
    try:
        cache_keys_to_clear = [
            'home_featured_ai_tools',
            'home_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        # Clear template fragments
        try:
            cache.delete('template.cache.featured_ai_tools_section')
        except:
            pass
            
        CacheManager.delete_pattern('ai_tools*')
        
        logger.info(f"Invalidated AITool cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating AITool cache: {e}")

@receiver([post_save, post_delete], sender=CybersecurityResource)
def invalidate_security_cache(sender, instance, **kwargs):
    """Invalidate cache when CybersecurityResource changes"""
    try:
        cache_keys_to_clear = [
            'home_urgent_security',
            'home_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        # Clear template fragments
        try:
            cache.delete('template.cache.urgent_security_section')
        except:
            pass
            
        CacheManager.delete_pattern('security*')
        
        logger.info(f"Invalidated CybersecurityResource cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating CybersecurityResource cache: {e}")

@receiver([post_save, post_delete], sender=BlogCategory)
def invalidate_blog_category_cache(sender, instance, **kwargs):
    """Invalidate cache when BlogCategory changes"""
    try:
        cache_keys_to_clear = [
            'home_featured_blog_categories',
            'blog_blog_categories',
            'home_page_data'
        ]
        
        for key in cache_keys_to_clear:
            cache.delete(key)
            
        CacheManager.delete_pattern('blog_cat*')
        
        logger.info(f"Invalidated BlogCategory cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating BlogCategory cache: {e}")

@receiver([post_save, post_delete], sender=MusicPlaylist)
def invalidate_music_cache(sender, instance, **kwargs):
    """Invalidate cache when MusicPlaylist changes"""
    try:
        cache.delete('music_page_data')
        CacheManager.delete_pattern('music*')
        
        logger.info(f"Invalidated MusicPlaylist cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating MusicPlaylist cache: {e}")

@receiver([post_save, post_delete], sender=UsefulResource)
def invalidate_useful_cache(sender, instance, **kwargs):
    """Invalidate cache when UsefulResource changes"""
    try:
        cache.delete('useful_page_data')
        CacheManager.delete_pattern('useful*')
        
        logger.info(f"Invalidated UsefulResource cache after {kwargs.get('signal', 'unknown')} signal")
        
    except Exception as e:
        logger.error(f"Error invalidating UsefulResource cache: {e}")