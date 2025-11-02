"""
TOOLS VIEWS - Araç ve Kaynak Görünüm Mantıkları
===============================================================================

Bu modül, AI araçları, siber güvenlik ve faydalı kaynakların görünüm mantıklarını içerir.

TANIMLI GÖRÜNÜMLER:
- ai_tools_view(): AI araçları sayfası - kategorize edilmiş AI platformları
- cybersecurity_view(): Siber güvenlik sayfası - güvenlik kaynakları ve tehditler
- useful_view(): Faydalı kaynaklar sayfası - kategorize edilmiş araçlar ve siteler

CACHE STRATEJISI:
- Faydalı kaynaklar: 15 dakika (900 saniye)
- AI ve güvenlik: Cache yok (sık güncellenen içerik)
"""

import logging

from django.core.cache import cache
from django.shortcuts import render

from ..models import AITool, CybersecurityResource, UsefulResource

logger = logging.getLogger(__name__)


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
