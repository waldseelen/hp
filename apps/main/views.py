import logging
from types import SimpleNamespace

from django.contrib.auth import logout
from django.core.cache import cache
from django.shortcuts import redirect, render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

from apps.blog.models import Post
from apps.tools.models import Tool

from .models import (
    AITool,
    CybersecurityResource,
    MusicPlaylist,
    PersonalInfo,
    SocialLink,
    SpotifyCurrentTrack,
    UsefulResource,
)

logger = logging.getLogger(__name__)


def home(request):
    """
    Home page view with optimized queries and caching.
    """
    fallback_personal_info = [
        {
            "key": "bio",
            "type": "text",
            "value": _(
                "Building secure, human-centered products with a decade of full stack experience across Python, Django, React, and cloud native tooling."
            ),
        },
        {
            "key": "about",
            "type": "text",
            "value": _(
                "I help teams launch resilient platforms, harden security posture, and ship delightful experiences faster."
            ),
        },
    ]

    fallback_social_links = [
        {
            "platform": "github",
            "url": "https://github.com/bugraakin",
            "description": _("GitHub profile"),
        },
        {
            "platform": "linkedin",
            "url": "https://linkedin.com/in/bugraak",
            "description": _("LinkedIn profile"),
        },
        {
            "platform": "cal",
            "url": "https://cal.com/bugraakin",
            "description": _("Book a call"),
        },
    ]

    fallback_posts = [
        SimpleNamespace(
            title=_("Designing secure platforms without slowing release velocity"),
            excerpt=_(
                "How a blended DevSecOps model reduced incident response time by 40% while shipping weekly releases."
            ),
            read_time=6,
            link="https://cal.com/bugraakin",
            published_at=timezone.now(),
        ),
        SimpleNamespace(
            title=_("Observability playbook for product-minded teams"),
            excerpt=_(
                "Telemetry patterns that surface real user impact before it hits the roadmap."
            ),
            read_time=5,
            link="https://github.com/bugraakin",
            published_at=timezone.now(),
        ),
        SimpleNamespace(
            title=_("Scaling design systems with accessible defaults"),
            excerpt=_(
                "Lessons from leading multi-brand component libraries serving millions."
            ),
            read_time=7,
            link="https://linkedin.com/in/bugraak",
            published_at=timezone.now(),
        ),
    ]

    fallback_tools = [
        SimpleNamespace(
            name="Telemetry Deck",
            description=_(
                "Real-time observability dashboards that protect user privacy by design."
            ),
            url="https://telemetrydeck.com",
            tags=[_("Observability"), _("Realtime")],
            category_label=_("Ops & Monitoring"),
            rating=5,
        ),
        SimpleNamespace(
            name="Linear",
            description=_(
                "Product delivery OS for roadmaps, async rituals, and focused execution."
            ),
            url="https://linear.app",
            tags=[_("Product Ops"), _("Planning")],
            category_label=_("Product Delivery"),
            rating=5,
        ),
        SimpleNamespace(
            name="ThreatMapper",
            description=_(
                "Cloud native attack surface mapping to keep workloads hardened."
            ),
            url="https://github.com/deepfence/ThreatMapper",
            tags=[_("Security"), _("Cloud")],
            category_label=_("Security Toolkit"),
            rating=4,
        ),
    ]

    fallback_ai_tools = [
        SimpleNamespace(
            name="PromptLayer",
            description=_(
                "Audit and version AI prompts across teams with reproducible workflows."
            ),
            url="https://promptlayer.com",
            category_label=_("AI Workflow"),
        ),
        SimpleNamespace(
            name="LangFuse",
            description=_(
                "Tracing, evaluation, and analytics for LLM-powered features."
            ),
            url="https://langfuse.com",
            category_label=_("LLM Ops"),
        ),
    ]

    fallback_security = [
        SimpleNamespace(
            title=_("Offensive security sprints"),
            summary=_(
                "Two-week red-team style reviews that surface critical gaps before launch."
            ),
            severity_label=_("High"),
            severity_level=3,
            url="https://cal.com/bugraakin",
        ),
        SimpleNamespace(
            title=_("AI supply-chain risk review"),
            summary=_(
                "Model card auditing, prompt review, and vendor risk scoring for compliant releases."
            ),
            severity_label=_("Medium"),
            severity_level=2,
            url="https://cal.com/bugraakin",
        ),
    ]

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

            cached_data = {
                "personal_info": list(personal_info),
                "social_links": list(social_links),
                "recent_posts": list(recent_posts),
                "favorite_tools": list(favorite_tools),
                "featured_ai_tools": list(featured_ai_tools),
                "urgent_security": list(urgent_security),
            }

            # Cache for 15 minutes
            cache.set(cache_key, cached_data, 900)

        personal_info = [
            {
                "key": "bio",
                "type": "text",
                "value": _(
                    "Building secure, human-centered products with a decade of full stack experience across Python, Django, React, and cloud native tooling."
                ),
            },
            {
                "key": "about",
                "type": "text",
                "value": _(
                    "I help teams launch resilient platforms, harden security posture, and ship delightful experiences faster."
                ),
            },
        ]

        fallback_social_links = [
            {
                "platform": "github",
                "url": "https://github.com/bugraakin",
                "description": _("GitHub profile"),
            },
            {
                "platform": "linkedin",
                "url": "https://linkedin.com/in/bugraak",
                "description": _("LinkedIn profile"),
            },
            {
                "platform": "cal",
                "url": "https://cal.com/bugraakin",
                "description": _("Book a call"),
            },
        ]

        fallback_posts = [
            SimpleNamespace(
                title=_("Designing secure platforms without slowing release velocity"),
                excerpt=_(
                    "How a blended DevSecOps model reduced incident response time by 40% while shipping weekly."
                ),
                read_time=6,
                link="https://cal.com/bugraakin",
                published_at=timezone.now(),
            ),
            SimpleNamespace(
                title=_("Observability playbook for product-minded teams"),
                excerpt=_(
                    "Telemetry patterns that surface real user impact before it hits the roadmap."
                ),
                read_time=5,
                link="https://github.com/bugraakin",
                published_at=timezone.now(),
            ),
            SimpleNamespace(
                title=_("Scaling design systems with accessible defaults"),
                excerpt=_(
                    "Lessons from leading multi-brand component libraries serving millions."
                ),
                read_time=7,
                link="https://linkedin.com/in/bugraak",
                published_at=timezone.now(),
            ),
        ]

        fallback_tools = [
            SimpleNamespace(
                name="Telemetry Deck",
                description=_(
                    "Serverless analytics that surfaces actionable insight without storing personal data."
                ),
                url="https://telemetrydeck.com",
                tags=[_("Observability"), _("Realtime")],
                category_label=_("Ops & Monitoring"),
                rating=5,
            ),
            SimpleNamespace(
                name="Linear",
                description=_(
                    "Product delivery OS we rely on for engineering rituals, roadmaps, and async collaboration."
                ),
                url="https://linear.app",
                tags=[_("Product Ops"), _("Planning")],
                category_label=_("Product Delivery"),
                rating=5,
            ),
            SimpleNamespace(
                name="ThreatMapper",
                description=_(
                    "Cloud native threat mapping to keep workloads hardened in dynamic environments."
                ),
                url="https://github.com/deepfence/ThreatMapper",
                tags=[_("Security"), _("Cloud")],
                category_label=_("Security Toolkit"),
                rating=4,
            ),
        ]

        fallback_ai_tools = [
            SimpleNamespace(
                name="PromptLayer",
                description=_(
                    "Audit and version AI prompts across teams with reproducible workflows."
                ),
                url="https://promptlayer.com",
                category_label=_("AI Workflow"),
            ),
            SimpleNamespace(
                name="LangFuse",
                description=_(
                    "Tracing, evaluation, and analytics for LLM-powered features."
                ),
                url="https://langfuse.com",
                category_label=_("LLM Ops"),
            ),
        ]

        fallback_security = [
            SimpleNamespace(
                title=_("Offensive security sprints"),
                summary=_(
                    "Two-week red-team style reviews that surface critical gaps before launch."
                ),
                severity_label=_("High"),
                severity_level=3,
                url="https://cal.com/bugraakin",
            ),
            SimpleNamespace(
                title=_("AI supply-chain risk review"),
                summary=_(
                    "Model card auditing, prompt review, and vendor risk scoring for compliant releases."
                ),
                severity_label=_("Medium"),
                severity_level=2,
                url="https://cal.com/bugraakin",
            ),
        ]

        personal_info = cached_data["personal_info"] or fallback_personal_info
        social_links = cached_data["social_links"] or fallback_social_links
        recent_posts = cached_data["recent_posts"] or fallback_posts
        favorite_tools = cached_data["favorite_tools"] or fallback_tools
        featured_ai_tools = cached_data["featured_ai_tools"] or fallback_ai_tools
        urgent_security = cached_data["urgent_security"] or fallback_security

        context = {
            "personal_info": personal_info,
            "social_links": social_links,
            "recent_posts": recent_posts,
            "favorite_tools": favorite_tools,
            "featured_ai_tools": featured_ai_tools,
            "urgent_security": urgent_security,
            "page_title": "Home",
            "meta_description": "Full Stack Developer & Cybersecurity Enthusiast Portfolio",
        }

        return render(request, "pages/portfolio/home.html", context)

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}")
        # Return basic context in case of error
        context = {
            "personal_info": fallback_personal_info,
            "social_links": fallback_social_links,
            "recent_posts": fallback_posts,
            "favorite_tools": fallback_tools,
            "featured_ai_tools": fallback_ai_tools,
            "urgent_security": fallback_security,
            "page_title": "Home",
            "meta_description": "Portfolio",
        }
        return render(request, "pages/portfolio/home.html", context)


def personal_view(request):
    """
    About/Personal page view with personal information.
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

            cached_data = {
                "personal_info": list(personal_info),
                "social_links": list(social_links),
            }

            cache.set(cache_key, cached_data, 900)

        context = {
            "personal_info": cached_data["personal_info"],
            "social_links": cached_data["social_links"],
            "page_title": "Hakkımda",
            "meta_description": "Kişisel bilgiler, yetenekler ve deneyimler",
        }

        return render(request, "pages/portfolio/personal.html", context)

    except Exception as e:
        logger.error(f"Error in personal view: {str(e)}")
        context = {
            "personal_info": [],
            "social_links": [],
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


def logout_view(request):
    """
    Logout view with proper cleanup.
    """
    try:
        logout(request)
        return redirect("admin:login")
    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}")
        return redirect("admin:login")
