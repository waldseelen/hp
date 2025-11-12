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

import logging

from django.contrib.auth import logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils import timezone

from apps.blog.models import Post
from apps.main.models import (
    AITool,
    CybersecurityResource,
    MusicPlaylist,
    PersonalInfo,
    SocialLink,
    SpotifyCurrentTrack,
    UsefulResource,
)
from apps.tools.models import Tool

logger = logging.getLogger(__name__)


def home(request):
    """
    Home page view with optimized queries and caching.
    """
    try:
        # Cache key for the home page data
        cache_key = "home_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Fetch data with optimized queries
            personal_info = PersonalInfo.objects.filter(is_visible=True).order_by(
                "order", "key"
            )

            social_links = SocialLink.objects.filter(is_visible=True).order_by(
                "order", "platform"
            )

            # Get recent published posts with author info
            recent_posts = (
                Post.objects.select_related("author")
                .filter(status="published", published_at__lte=timezone.now())
                .order_by("-published_at")[:3]
            )

            # Get favorite tools
            favorite_tools = (
                Tool.objects.visible()
                .filter(is_favorite=True)
                .order_by("category", "title")[:6]
            )

            # Get featured AI tools
            featured_ai_tools = AITool.objects.filter(
                is_featured=True, is_visible=True
            ).order_by("order", "name")[:4]

            # Get urgent cybersecurity resources
            urgent_security = CybersecurityResource.objects.filter(
                is_urgent=True, is_visible=True
            ).order_by("-severity_level", "title")[:3]

            # current_activities = []  # Model removed

            # Get featured blog categories
            from apps.main.models import BlogCategory

            featured_blog_categories = BlogCategory.objects.filter(
                is_visible=True
            ).order_by("order", "name")[:6]

            cached_data = {
                "personal_info": list(personal_info),
                "social_links": list(social_links),
                "recent_posts": list(recent_posts),
                "favorite_tools": list(favorite_tools),
                "featured_ai_tools": list(featured_ai_tools),
                "urgent_security": list(urgent_security),
                # 'current_activities': [],  # Model removed
                "featured_blog_categories": list(featured_blog_categories),
            }

            # Cache for 15 minutes
            cache.set(cache_key, cached_data, 900)

        context = {
            "personal_info": cached_data["personal_info"],
            "social_links": cached_data["social_links"],
            "recent_posts": cached_data["recent_posts"],
            "favorite_tools": cached_data["favorite_tools"],
            "featured_ai_tools": cached_data["featured_ai_tools"],
            "urgent_security": cached_data["urgent_security"],
            # 'current_activities': [],  # Model removed
            "featured_blog_categories": cached_data["featured_blog_categories"],
            "page_title": "Home",
            "meta_description": "Full Stack Developer & Cybersecurity Enthusiast Portfolio",
        }

        return render(request, "pages/portfolio/home.html", context)

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Return basic context in case of error
        context = {
            "personal_info": [],
            "social_links": [],
            "recent_posts": [],
            "favorite_tools": [],
            "featured_ai_tools": [],
            "urgent_security": [],
            "current_activities": [],
            "featured_blog_categories": [],
            "page_title": "Home",
            "meta_description": "Portfolio",
        }
        return render(request, "pages/portfolio/home.html", context)


def personal_view(request):
    """
    About/Personal page view with personal information, certificates and skills.
    """
    try:
        cache_key = "personal_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            personal_info = PersonalInfo.objects.filter(
                is_visible=True,
                key__in=["about", "skills", "experience", "education", "bio"],
            ).order_by("order", "key")

            social_links = SocialLink.objects.filter(is_visible=True).order_by(
                "order", "platform"
            )

            # Get certificates, skills and hobbies
            # certificates = []  # Model removed
            # skills = []  # Model removed
            # hobbies = []  # Model removed

            cached_data = {
                "personal_info": list(personal_info),
                "social_links": list(social_links),
                # 'certificates': [],  # Model removed
                # 'skills': [],  # Model removed
                # 'hobbies': [],  # Model removed
            }

            cache.set(cache_key, cached_data, 900)

        context = {
            "personal_info": cached_data["personal_info"],
            "social_links": cached_data["social_links"],
            # 'certificates': [],  # Model removed
            # 'skills': [],  # Model removed
            # 'hobbies': [],  # Model removed
            "page_title": "Hakkımda",
            "meta_description": "Kişisel bilgiler, sertifikalar, yetenekler ve deneyimler",
        }

        return render(request, "pages/portfolio/personal.html", context)

    except Exception as e:
        logger.error(f"Error in personal view: {str(e)}")
        context = {
            "personal_info": [],
            "social_links": [],
            # 'certificates': [],  # Model removed
            # 'skills': [],  # Model removed
            # 'hobbies': [],  # Model removed
            "page_title": "Hakkımda",
            "meta_description": "Kişisel bilgiler",
        }
        return render(request, "pages/portfolio/personal.html", context)


def music_view(request):
    """
    Music page view with playlists and current track.
    """
    try:
        cache_key = "music_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Get visible playlists
            playlists = MusicPlaylist.objects.filter(is_visible=True).order_by(
                "order", "name"
            )

            # Get featured playlists
            featured_playlists = playlists.filter(is_featured=True)[:3]

            # Get current Spotify track if available
            current_track = SpotifyCurrentTrack.objects.first()

            cached_data = {
                "playlists": list(playlists),
                "featured_playlists": list(featured_playlists),
                "current_track": current_track,
            }

            cache.set(cache_key, cached_data, 300)  # 5 minutes cache

        context = {
            "playlists": cached_data["playlists"],
            "featured_playlists": cached_data["featured_playlists"],
            "current_track": cached_data["current_track"],
            "page_title": "Müzik",
            "meta_description": "Müzik playlistleri, şu an çaldığım şarkılar ve favori sanatçılar",
        }

        return render(request, "pages/portfolio/music.html", context)

    except Exception as e:
        logger.error(f"Error in music view: {str(e)}")
        context = {
            "playlists": [],
            "featured_playlists": [],
            "current_track": None,
            "page_title": "Müzik",
            "meta_description": "Müzik",
        }
        return render(request, "pages/portfolio/music.html", context)


def ai_tools_view(request):
    """
    AI Tools page view with AI resources and tools.
    """
    try:
        # Get AI tools by category
        ai_tools_by_category = {}
        for category_code, category_name in AITool.CATEGORY_CHOICES:
            tools = AITool.objects.filter(
                category=category_code, is_visible=True
            ).order_by("order", "name")
            if tools.exists():
                ai_tools_by_category[category_name] = tools

        context = {
            "ai_tools_by_category": ai_tools_by_category,
            "page_title": "AI Araçları",
            "meta_description": "Yapay zeka araçları ve platformları - Sevdiğim AI yer imleri",
        }

        return render(request, "pages/portfolio/ai.html", context)

    except Exception as e:
        logger.error(f"Error in ai_tools view: {str(e)}")
        context = {
            "ai_tools_by_category": {},
            "page_title": "AI Araçları",
            "meta_description": "Yapay zeka araçları",
        }
        return render(request, "pages/portfolio/ai.html", context)


def cybersecurity_view(request):
    """
    Cybersecurity page view with security content and resources.
    """
    try:
        # Get cybersecurity resources by type
        resources_by_type = {}
        for type_code, type_name in CybersecurityResource.TYPE_CHOICES:
            resources = CybersecurityResource.objects.filter(
                type=type_code, is_visible=True
            ).order_by("-is_urgent", "-severity_level", "order", "title")
            if resources.exists():
                resources_by_type[type_name] = resources

        # Get urgent threats
        urgent_threats = CybersecurityResource.objects.filter(
            is_urgent=True, is_visible=True
        ).order_by("-severity_level", "title")[:5]

        context = {
            "resources_by_type": resources_by_type,
            "urgent_threats": urgent_threats,
            "page_title": "Siber Güvenlik",
            "meta_description": "Siber güvenlik kaynakları, araçları ve güncel bilgiler",
        }

        return render(request, "pages/portfolio/cybersecurity.html", context)

    except Exception as e:
        logger.error(f"Error in cybersecurity view: {str(e)}")
        context = {
            "resources_by_type": {},
            "urgent_threats": [],
            "page_title": "Siber Güvenlik",
            "meta_description": "Siber güvenlik",
        }
        return render(request, "pages/portfolio/cybersecurity.html", context)


def useful_view(request):
    """
    Useful resources page view with categorized tools and websites.
    """
    try:
        cache_key = "useful_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Get resources by category
            resources_by_category = {}
            for category_code, category_name in UsefulResource.CATEGORY_CHOICES:
                resources = UsefulResource.objects.filter(
                    category=category_code, is_visible=True
                ).order_by("order", "name")
                if resources.exists():
                    resources_by_category[category_name] = resources

            # Get featured resources
            featured_resources = UsefulResource.objects.filter(
                is_featured=True, is_visible=True
            ).order_by("order", "name")[:6]

            cached_data = {
                "resources_by_category": resources_by_category,
                "featured_resources": list(featured_resources),
            }

            cache.set(cache_key, cached_data, 900)  # 15 minutes cache

        context = {
            "resources_by_category": cached_data["resources_by_category"],
            "featured_resources": cached_data["featured_resources"],
            "page_title": "Useful Resources",
            "meta_description": "Faydalı araçlar, siteler ve uygulamalar koleksiyonu",
        }

        return render(request, "pages/portfolio/useful.html", context)

    except Exception as e:
        logger.error(f"Error in useful view: {str(e)}")
        context = {
            "resources_by_category": {},
            "featured_resources": [],
            "page_title": "Useful Resources",
            "meta_description": "Faydalı kaynaklar",
        }
        return render(request, "pages/portfolio/useful.html", context)


def projects_view(request):
    """
    Projects page view with portfolio projects.
    """
    try:
        cache_key = "projects_page_data"
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Get visible projects
            all_projects = Tool.objects.filter(is_visible=True).order_by(
                "-is_favorite", "-created_at"
            )

            # Get featured projects
            featured_projects = all_projects.filter(is_favorite=True)[:3]

            # Get projects by category instead of status
            projects_by_category = {}
            for category_code, category_name in Tool.CATEGORY_CHOICES:
                projects = all_projects.filter(category=category_code)
                if projects.exists():
                    projects_by_category[category_name] = projects

            cached_data = {
                "all_projects": list(all_projects),
                "featured_projects": list(featured_projects),
                "projects_by_category": projects_by_category,
            }

            cache.set(cache_key, cached_data, 900)  # 15 minutes cache

        context = {
            "all_projects": cached_data["all_projects"],
            "featured_projects": cached_data["featured_projects"],
            "projects_by_category": cached_data["projects_by_category"],
            "page_title": "Projeler",
            "meta_description": "Geliştirdiğim projeler ve portföy çalışmaları",
        }

        return render(request, "pages/portfolio/projects.html", context)

    except Exception as e:
        logger.error(f"Error in projects view: {str(e)}")
        context = {
            "all_projects": [],
            "featured_projects": [],
            "projects_by_category": {},
            "page_title": "Projeler",
            "meta_description": "Projeler",
        }
        return render(request, "pages/portfolio/projects.html", context)


def project_detail_view(request, slug):
    """
    Project detail view with full project information.
    """
    from django.http import Http404
    from django.shortcuts import get_object_or_404

    try:
        project = get_object_or_404(Tool.objects.filter(is_visible=True), slug=slug)

        # Increment view count
        project.increment_view_count()

        # Get related projects (same tech stack or similar difficulty)
        related_projects = Tool.objects.filter(is_visible=True).exclude(pk=project.pk)[
            :4
        ]

        if not related_projects.exists():
            # Fallback to other featured projects
            related_projects = Tool.objects.filter(
                is_visible=True, is_favorite=True
            ).exclude(pk=project.pk)[:4]

        context = {
            "project": project,
            "related_projects": related_projects,
            "page_title": f"{project.title} - Proje Detayı",
            "meta_description": (
                project.description[:160]
                if project.description
                else f"{project.title} proje detayları"
            ),
        }

        return render(request, "pages/portfolio/project_detail.html", context)

    except Http404:
        # Re-raise 404 to let Django handle it properly
        raise
    except Exception as e:
        logger.error(f"Error in project_detail view: {str(e)}")
        return redirect("main:projects")


def logout_view(request):
    """
    Logout view with proper cleanup.
    """
    try:
        logout(request)
        return redirect("home")
    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}")
        return redirect("home")
