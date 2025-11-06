"""
HOME VIEWS - Ana Sayfa Görünüm Mantığı
===============================================================================

Bu modül, portfolio web sitesinin ana sayfasının görünüm mantığını içerir.
Ana sayfa tüm önemli içerikleri (blog yazıları, favori araçlar, AI araçları,
güvenlik uyarıları) bir araya getirir.

ÖNEMLİ ÖZELLİKLER:
- Kapsamlı cache sistemi (15 dakika)
- Fallback içerikler (veritabanı hataları için)
- Performans odaklı sorgular (select_related, prefetch_related)
- SEO optimizasyonları
"""

import logging
from types import SimpleNamespace

from django.core.cache import cache
from django.shortcuts import render
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Note: Model imports moved to function level to avoid circular imports
# from apps.blog.models import Post
# from apps.tools.models import Tool
# from ..models import AITool, CybersecurityResource, PersonalInfo, SocialLink

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
            summary=_(
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
            summary=_(
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
            summary=_(
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
        # Import models inside function to avoid circular imports
        from apps.blog.models import Post
        from apps.tools.models import Tool

        from ..models import AITool, CybersecurityResource, PersonalInfo, SocialLink

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
