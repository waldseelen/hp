"""
MAIN VIEWS - ANA GÖRÜNÜM MANTIKLARI (Portfolio Ana Sayfaları)
===============================================================================

Bu dosya, portfolio web sitesinin ana sayfalarının görünüm mantıklarını içerir.
Tüm temel sayfaların (anasayfa, hakkımda, projeler vb.) render işlemlerini yönetir.

TANIMLI GÖRÜNÜMLER:
- home(): Ana sayfa - featured içerikler, son blog yazıları, favori araçlar
- personal_view(): Hakkımda sayfası - kişisel bilgiler, sertifikalar, yetenekler
- music_view(): Müzik sayfası - playlistler ve şu an çalan müzik
- ai_tools_view(): AI Araçları sayfası - yapay zeka araçları kategorileri
- cybersecurity_view(): Siber güvenlik sayfası - güvenlik kaynakları ve tehditler
- useful_view(): Faydalı kaynaklar sayfası - kategorilere ayrılmış araçlar
- projects_view(): Projeler sayfası - portfolio projeleri listeleme
- project_detail_view(): Proje detay sayfası - tekil proje görüntüleme
- logout_view(): Çıkış işlemi yönetimi

ÖNEMLİ ÖZELLİKLER:
- Cache sistemi optimizasyonu (15 dakika cache süresi)
- Hata yönetimi ve loglama sistemi
- Performans odaklı veritabanı sorguları (select_related, prefetch_related)
- SEO optimizasyonları (meta description, page title)
- Görüntülenme sayısı takibi (proje detaylarında)
- İlgili içerik önerileri (related content algorithm)

CACHE STRATEJISI:
- Ana sayfa: 15 dakika (900 saniye)
- Kişisel sayfa: 15 dakika
- Müzik sayfası: 5 dakika (dinamik içerik)
- Faydalı kaynaklar: 15 dakika
- Projeler: 15 dakika

HATA YÖNETİMİ:
- Try-except blokları ile güvenli çalışma
- Logger kullanarak hata kaydetme
- Fallback içerikler (boş listeler, default değerler)
- Kullanıcı deneyimini bozamayan graceful degradation

İLİŞKİLER VE BAĞIMLILIKLAR:
- main.models: Tüm ana veri modelleri
- blog.models: Blog yazıları entegrasyonu
- tools.models: Araç koleksiyonu
- templates/main/: HTML şablon dosyaları
- Django cache framework: Redis/Memcached desteği
"""

from typing import Dict, List, Any, Optional, Union
from django.shortcuts import render, redirect
from django.contrib.auth import logout
from django.core.cache import cache
from django.http import HttpRequest, HttpResponse, JsonResponse
from django.db.models import QuerySet
from ..cache_utils import (
    CacheManager, cache_result, cache_queryset_medium, cache_long,
    cache_page_data, ModelCacheManager
)
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from apps.main.models import PersonalInfo, SocialLink, AITool, CybersecurityResource, MusicPlaylist, SpotifyCurrentTrack, UsefulResource
from apps.blog.models import Post
from apps.tools.models import Tool
from apps.main.performance import performance_metrics, alert_manager
import logging

# Cache helper functions for home page data
@cache_queryset_medium
def get_cached_personal_info() -> List[PersonalInfo]:
    """Get cached personal information"""
    return list(PersonalInfo.objects.filter(
        is_visible=True
    ).order_by('order', 'key'))

@cache_queryset_medium
def get_cached_social_links() -> List[SocialLink]:
    """Get cached social links"""
    return list(SocialLink.objects.filter(
        is_visible=True
    ).order_by('order', 'platform'))

@cache_queryset_medium
def get_cached_recent_posts():
    """Get cached recent blog posts"""
    return list(Post.objects.select_related('author').filter(
        status='published',
        published_at__lte=timezone.now()
    ).order_by('-published_at')[:3])

@cache_queryset_medium
def get_cached_favorite_tools():
    """Get cached favorite tools"""
    return list(Tool.objects.visible().filter(
        is_favorite=True
    ).order_by('category', 'title')[:6])

@cache_queryset_medium
def get_cached_featured_ai_tools():
    """Get cached featured AI tools"""
    return list(AITool.objects.filter(
        is_featured=True,
        is_visible=True
    ).order_by('order', 'name')[:4])

@cache_queryset_medium
def get_cached_urgent_security():
    """Get cached urgent security resources"""
    return list(CybersecurityResource.objects.filter(
        is_urgent=True,
        is_visible=True
    ).order_by('-severity_level', 'title')[:3])

@cache_queryset_medium
def get_cached_featured_blog_categories():
    """Get cached featured blog categories"""
    from apps.main.models import BlogCategory
    return list(BlogCategory.objects.filter(
        is_visible=True
    ).order_by('order', 'name')[:6])

logger = logging.getLogger(__name__)


def get_client_ip(request):
    """Get the real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip


@cache_page_data('home', timeout=CacheManager.TIMEOUTS['medium'])
def home(request: HttpRequest) -> HttpResponse:
    """
    Home page view with optimized queries and caching.
    Uses individual cached functions for better cache granularity.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered home page template with context data
    """
    try:
        # Use cached helper functions for better granular caching
        context = {
            'personal_info': get_cached_personal_info(),
            'social_links': get_cached_social_links(),
            'recent_posts': get_cached_recent_posts(),
            'favorite_tools': get_cached_favorite_tools(),
            'featured_ai_tools': get_cached_featured_ai_tools(),
            'urgent_security': get_cached_urgent_security(),
            'featured_blog_categories': get_cached_featured_blog_categories(),
            'page_title': 'Home',
            'meta_description': 'Full Stack Developer & Cybersecurity Enthusiast Portfolio',
        }
        
        return render(request, 'main/home.html', context)
        
    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Return basic context in case of error
        context = {
            'personal_info': [],
            'social_links': [],
            'recent_posts': [],
            'favorite_tools': [],
            'featured_ai_tools': [],
            'urgent_security': [],
            'current_activities': [],
            'featured_blog_categories': [],
            'page_title': 'Home',
            'meta_description': 'Portfolio',
        }
        return render(request, 'main/home.html', context)


def personal_view(request: HttpRequest) -> HttpResponse:
    """
    About/Personal page view with personal information, certificates and skills.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered personal/about page template
    """
    try:
        cache_key = 'personal_page_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            personal_info = PersonalInfo.objects.filter(
                is_visible=True,
                key__in=['about', 'skills', 'experience', 'education', 'bio']
            ).order_by('order', 'key')
            
            social_links = SocialLink.objects.filter(
                is_visible=True
            ).order_by('order', 'platform')
            
            # Get certificates, skills and hobbies
            # certificates = []  # Model removed
            # skills = []  # Model removed  
            # hobbies = []  # Model removed
            
            cached_data = {
                'personal_info': list(personal_info),
                'social_links': list(social_links),
                # 'certificates': [],  # Model removed
                # 'skills': [],  # Model removed
                # 'hobbies': [],  # Model removed
            }
            
            cache.set(cache_key, cached_data, 900)
        
        context = {
            'personal_info': cached_data['personal_info'],
            'social_links': cached_data['social_links'],
            # 'certificates': [],  # Model removed
            # 'skills': [],  # Model removed
            # 'hobbies': [],  # Model removed
            'page_title': 'Hakkımda',
            'meta_description': 'Kişisel bilgiler, sertifikalar, yetenekler ve deneyimler',
        }
        
        return render(request, 'main/personal.html', context)
        
    except Exception as e:
        logger.error(f"Error in personal view: {str(e)}")
        context = {
            'personal_info': [],
            'social_links': [],
            # 'certificates': [],  # Model removed
            # 'skills': [],  # Model removed
            # 'hobbies': [],  # Model removed
            'page_title': 'Hakkımda',
            'meta_description': 'Kişisel bilgiler',
        }
        return render(request, 'main/personal.html', context)


def music_view(request):
    """
    Music page view with playlists and current track.
    """
    try:
        cache_key = 'music_page_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            # Get visible playlists
            playlists = MusicPlaylist.objects.filter(
                is_visible=True
            ).order_by('order', 'name')
            
            # Get featured playlists
            featured_playlists = playlists.filter(is_featured=True)[:3]
            
            # Get current Spotify track if available
            current_track = SpotifyCurrentTrack.objects.first()
            
            cached_data = {
                'playlists': list(playlists),
                'featured_playlists': list(featured_playlists),
                'current_track': current_track,
            }
            
            cache.set(cache_key, cached_data, 300)  # 5 minutes cache
        
        context = {
            'playlists': cached_data['playlists'],
            'featured_playlists': cached_data['featured_playlists'],
            'current_track': cached_data['current_track'],
            'page_title': 'Müzik',
            'meta_description': 'Müzik playlistleri, şu an çaldığım şarkılar ve favori sanatçılar',
        }
        
        return render(request, 'main/music.html', context)
        
    except Exception as e:
        logger.error(f"Error in music view: {str(e)}")
        context = {
            'playlists': [],
            'featured_playlists': [],
            'current_track': None,
            'page_title': 'Müzik',
            'meta_description': 'Müzik',
        }
        return render(request, 'main/music.html', context)


def ai_tools_view(request: HttpRequest) -> HttpResponse:
    """
    AI Tools page view with AI resources and tools.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered AI tools page template
    """
    try:
        # Get AI tools by category
        ai_tools_by_category = {}
        for category_code, category_name in AITool.CATEGORY_CHOICES:
            tools = AITool.objects.filter(
                category=category_code,
                is_visible=True
            ).order_by('order', 'name')
            if tools.exists():
                ai_tools_by_category[category_name] = tools
        
        context = {
            'ai_tools_by_category': ai_tools_by_category,
            'page_title': 'AI Araçları',
            'meta_description': 'Yapay zeka araçları ve platformları - Sevdiğim AI yer imleri',
        }
        
        return render(request, 'main/ai.html', context)
        
    except Exception as e:
        logger.error(f"Error in ai_tools view: {str(e)}")
        context = {
            'ai_tools_by_category': {},
            'page_title': 'AI Araçları',
            'meta_description': 'Yapay zeka araçları',
        }
        return render(request, 'main/ai.html', context)


def cybersecurity_view(request: HttpRequest) -> HttpResponse:
    """
    Cybersecurity page view with security content and resources.

    Args:
        request: HTTP request object

    Returns:
        HttpResponse: Rendered cybersecurity page template
    """
    try:
        # Get cybersecurity resources by type
        resources_by_type = {}
        for type_code, type_name in CybersecurityResource.TYPE_CHOICES:
            resources = CybersecurityResource.objects.filter(
                type=type_code,
                is_visible=True
            ).order_by('-is_urgent', '-severity_level', 'order', 'title')
            if resources.exists():
                resources_by_type[type_name] = resources
        
        # Get urgent threats
        urgent_threats = CybersecurityResource.objects.filter(
            is_urgent=True,
            is_visible=True
        ).order_by('-severity_level', 'title')[:5]
        
        context = {
            'resources_by_type': resources_by_type,
            'urgent_threats': urgent_threats,
            'page_title': 'Siber Güvenlik',
            'meta_description': 'Siber güvenlik kaynakları, araçları ve güncel bilgiler',
        }
        
        return render(request, 'main/cybersecurity.html', context)
        
    except Exception as e:
        logger.error(f"Error in cybersecurity view: {str(e)}")
        context = {
            'resources_by_type': {},
            'urgent_threats': [],
            'page_title': 'Siber Güvenlik',
            'meta_description': 'Siber güvenlik',
        }
        return render(request, 'main/cybersecurity.html', context)


def useful_view(request):
    """
    Useful resources page view with categorized tools and websites.
    """
    try:
        cache_key = 'useful_page_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            # Get resources by category
            resources_by_category = {}
            for category_code, category_name in UsefulResource.CATEGORY_CHOICES:
                resources = UsefulResource.objects.filter(
                    category=category_code,
                    is_visible=True
                ).order_by('order', 'name')
                if resources.exists():
                    resources_by_category[category_name] = resources
            
            # Get featured resources
            featured_resources = UsefulResource.objects.filter(
                is_featured=True,
                is_visible=True
            ).order_by('order', 'name')[:6]
            
            cached_data = {
                'resources_by_category': resources_by_category,
                'featured_resources': list(featured_resources),
            }
            
            cache.set(cache_key, cached_data, 900)  # 15 minutes cache
        
        context = {
            'resources_by_category': cached_data['resources_by_category'],
            'featured_resources': cached_data['featured_resources'],
            'page_title': 'Useful Resources',
            'meta_description': 'Faydalı araçlar, siteler ve uygulamalar koleksiyonu',
        }
        
        return render(request, 'main/useful.html', context)
        
    except Exception as e:
        logger.error(f"Error in useful view: {str(e)}")
        context = {
            'resources_by_category': {},
            'featured_resources': [],
            'page_title': 'Useful Resources',
            'meta_description': 'Faydalı kaynaklar',
        }
        return render(request, 'main/useful.html', context)


def projects_view(request):
    """
    Projects page view with portfolio projects.
    """
    try:
        cache_key = 'projects_page_data'
        cached_data = cache.get(cache_key)
        
        if cached_data is None:
            # Get visible projects
            all_projects = Tool.objects.filter(
                is_visible=True
            ).order_by('-is_featured', 'order', '-created_at')
            
            # Get featured projects
            featured_projects = all_projects.filter(is_featured=True)[:3]
            
            # Get projects by category instead of status
            projects_by_category = {}
            for category_code, category_name in Tool.CATEGORY_CHOICES:
                projects = all_projects.filter(category=category_code)
                if projects.exists():
                    projects_by_category[category_name] = projects
            
            cached_data = {
                'all_projects': list(all_projects),
                'featured_projects': list(featured_projects),
                'projects_by_category': projects_by_category,
            }
            
            cache.set(cache_key, cached_data, 900)  # 15 minutes cache
        
        context = {
            'all_projects': cached_data['all_projects'],
            'featured_projects': cached_data['featured_projects'],
            'projects_by_category': cached_data['projects_by_category'],
            'page_title': 'Projeler',
            'meta_description': 'Geliştirdiğim projeler ve portföy çalışmaları',
        }
        
        return render(request, 'main/projects.html', context)
        
    except Exception as e:
        logger.error(f"Error in projects view: {str(e)}")
        context = {
            'all_projects': [],
            'featured_projects': [],
            'projects_by_category': {},
            'page_title': 'Projeler',
            'meta_description': 'Projeler',
        }
        return render(request, 'main/projects.html', context)


def project_detail_view(request, slug):
    """
    Project detail view with full project information.
    """
    try:
        from django.shortcuts import get_object_or_404
        
        project = get_object_or_404(
            Tool.objects.filter(is_visible=True),
            slug=slug
        )
        
        # Increment view count
        project.increment_view_count()
        
        # Get related projects (same tech stack or similar difficulty)
        related_projects = Tool.objects.filter(
            is_visible=True
        ).exclude(pk=project.pk)[:4]
        
        if not related_projects.exists():
            # Fallback to other featured projects
            related_projects = Tool.objects.filter(
                is_visible=True,
                is_featured=True
            ).exclude(pk=project.pk)[:4]
        
        # Add dynamic breadcrumb for this project
        request.breadcrumbs_extra = [
            {'title': project.title, 'url': None}
        ]
        
        context = {
            'project': project,
            'related_projects': related_projects,
            'page_title': f'{project.title} - Proje Detayı',
            'meta_description': project.description[:160] if project.description else f'{project.title} proje detayları',
        }
        
        return render(request, 'main/project_detail.html', context)
        
    except Exception as e:
        logger.error(f"Error in project_detail view: {str(e)}")
        return redirect('main:projects')


def logout_view(request):
    """
    Logout view with proper cleanup.
    """
    try:
        logout(request)
        return redirect('home')
    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}")
        return redirect('home')


# Internationalization Views
# ==========================

@require_http_methods(["GET", "POST"])
def set_language(request):
    """
    Set the language preference for the user.
    Compatible with Django's built-in set_language view but with enhanced features.
    """
    from django.utils import translation
    from django.conf import settings
    from django.urls import reverse
    
    next_url = request.POST.get('next', request.GET.get('next'))
    language = request.POST.get('language', request.GET.get('language'))
    
    # Validate language
    if language and language in [lang[0] for lang in settings.LANGUAGES]:
        # Activate the language for this request
        translation.activate(language)
        
        # Create the response
        if next_url:
            response = redirect(next_url)
        else:
            response = redirect('/')
        
        # Set the language cookie
        response.set_cookie(
            'django_language', 
            language,
            max_age=365 * 24 * 60 * 60,  # 1 year
            httponly=False,  # Allow JavaScript access for client-side management
            samesite='Lax'
        )
        
        # Log the language change
        try:
            logger.info(f"Language changed to {language} for user", extra={
                'language': language,
                'ip_address': get_client_ip(request),
                'timestamp': timezone.now().isoformat(),
            })
        except Exception:
            pass  # Silently fail logging
        
        return response
    
    # If language is invalid, redirect to previous page or home
    return redirect(next_url or '/')


@require_http_methods(["GET"])
def language_status(request):
    """
    Return current language status as JSON.
    Useful for JavaScript language management.
    """
    from django.utils import translation
    from django.conf import settings
    
    current_language = translation.get_language()
    available_languages = [
        {
            'code': lang[0],
            'name': str(lang[1]),
            'is_current': lang[0] == current_language
        }
        for lang in settings.LANGUAGES
    ]
    
    return JsonResponse({
        'current_language': current_language,
        'available_languages': available_languages,
        'rtl': translation.get_language_bidi(),
    })


@require_http_methods(["GET"])  
def health_check(request):
    """
    API endpoint for system health check
    Returns JSON with system status information
    """
    import time
    import django
    from django.db import connection
    
    try:
        # Check database connectivity
        start_time = time.time()
        cursor = connection.cursor()
        cursor.execute("SELECT 1")
        db_time = time.time() - start_time
        db_status = "healthy"
        
        # Check cache if Redis is configured
        cache_status = "not_configured"
        cache_time = 0
        try:
            from django.core.cache import cache
            start_time = time.time()
            cache.set('health_check', 'ok', 1)
            if cache.get('health_check') == 'ok':
                cache_time = time.time() - start_time
                cache_status = "healthy"
            else:
                cache_status = "error"
        except Exception:
            cache_status = "error"
        
        # System information
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now().isoformat(),
            'services': {
                'database': {
                    'status': db_status,
                    'response_time_ms': round(db_time * 1000, 2)
                },
                'cache': {
                    'status': cache_status,
                    'response_time_ms': round(cache_time * 1000, 2)
                }
            },
            'environment': {
                'debug': settings.DEBUG,
                'django_version': django.get_version(),
            }
        }
        
        # Determine overall status
        if db_status != "healthy":
            health_data['status'] = 'unhealthy'
            return JsonResponse(health_data, status=503)
        
        return JsonResponse(health_data)
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return JsonResponse({
            'status': 'unhealthy',
            'timestamp': timezone.now().isoformat(),
            'error': str(e)
        }, status=503)


def performance_dashboard_view(request):
    """
    Performance monitoring dashboard view.
    Shows real-time metrics, health status, and alerting information.
    """
    try:
        # Get performance metrics summary
        metrics_summary = performance_metrics.get_metrics_summary(hours=24)
        real_time_data = performance_metrics.get_real_time_data()
        health_status = performance_metrics.get_health_status()
        recent_alerts = alert_manager.get_recent_alerts(minutes=60)

        context = {
            'metrics_summary': metrics_summary,
            'real_time_data': real_time_data,
            'health_status': health_status,
            'recent_alerts': recent_alerts,
            'page_title': 'Performance Dashboard',
            'meta_description': 'Real-time performance monitoring dashboard with Core Web Vitals tracking',
            'dashboard_refresh_interval': 30000,  # 30 seconds
        }

        return render(request, 'main/dashboard.html', context)

    except Exception as e:
        logger.error(f"Error in performance dashboard view: {str(e)}")
        context = {
            'metrics_summary': {'metrics': {}, 'health_score': 'F', 'total_entries': 0},
            'real_time_data': {'status': 'error', 'error': str(e)},
            'health_status': {'status': 'unhealthy'},
            'recent_alerts': [],
            'page_title': 'Performance Dashboard',
            'meta_description': 'Performance monitoring dashboard',
            'dashboard_refresh_interval': 30000,
        }
        return render(request, 'main/dashboard.html', context)
