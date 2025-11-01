from typing import Any, Dict, List

from django.conf import settings
from django.http import HttpRequest
from django.urls import resolve

from .models import PersonalInfo, SocialLink


def social_links(request: HttpRequest) -> Dict[str, Any]:
    """
    Context processor to provide global social links for the footer.
    """
    return {
        "global_social_links": SocialLink.objects.filter(is_visible=True).order_by(
            "order", "platform"
        )
    }


def global_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Global context processor to provide site-wide context variables.
    """
    return {
        "site_name": getattr(settings, "SITE_NAME", "Professional Portfolio"),
        "site_description": getattr(
            settings, "SITE_DESCRIPTION", "Full Stack Developer"
        ),
        "global_social_links": SocialLink.objects.filter(is_visible=True).order_by(
            "order", "platform"
        ),
        "personal_info": PersonalInfo.objects.filter(is_visible=True).order_by("order"),
    }


def breadcrumbs(request: HttpRequest) -> Dict[str, List[Dict[str, Any]]]:
    """
    Context processor to provide breadcrumb navigation for all templates.
    """
    try:
        resolved_match = resolve(request.path)
        url_name = resolved_match.url_name
        namespace = resolved_match.namespace

        breadcrumb_list = [{"title": "Ana Sayfa", "url": "/"}]

        # Define breadcrumb mappings
        breadcrumb_mapping = {
            # Main app
            "home": [],
            "personal": [{"title": "Hakkımda", "url": None}],
            "ai": [{"title": "AI Araçları", "url": None}],
            "cybersecurity": [{"title": "Siber Güvenlik", "url": None}],
            "music": [{"title": "Müzik", "url": None}],
            "useful": [{"title": "Useful", "url": None}],
            # Blog app
            "blog:list": [{"title": "Blog", "url": None}],
            "blog:detail": [
                {"title": "Blog", "url": "/blog/"},
                {"title": "Makale", "url": None},
            ],
            # Tools app
            "tools:list": [{"title": "Projeler", "url": None}],
            "tools:detail": [
                {"title": "Projeler", "url": "/tools/"},
                {"title": "Proje Detayı", "url": None},
            ],
            # Contact app
            "contact:form": [{"title": "İletişim", "url": None}],
            "contact:success": [
                {"title": "İletişim", "url": "/contact/"},
                {"title": "Teşekkürler", "url": None},
            ],
            # Chat app
            "chat:chat": [{"title": "Canlı Sohbet", "url": None}],
        }

        # Build the full URL name with namespace
        full_url_name = f"{namespace}:{url_name}" if namespace else url_name

        # Get breadcrumbs for the current page
        if full_url_name in breadcrumb_mapping:
            breadcrumb_list.extend(breadcrumb_mapping[full_url_name])
        elif url_name in breadcrumb_mapping:
            breadcrumb_list.extend(breadcrumb_mapping[url_name])

        # Append view-provided dynamic extras if present
        if hasattr(request, "breadcrumbs_extra"):
            breadcrumb_list.extend(request.breadcrumbs_extra)

        return {"breadcrumbs": breadcrumb_list}

    except Exception:
        # Fallback for any errors
        return {"breadcrumbs": [{"title": "Ana Sayfa", "url": "/"}]}


def language_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Add language-related context to all templates.
    Provides current language, available languages, and helper functions.
    """
    from django.conf import settings
    from django.urls import reverse
    from django.utils import translation

    current_language = translation.get_language()

    return {
        "CURRENT_LANGUAGE": current_language,
        "AVAILABLE_LANGUAGES": settings.LANGUAGES,
        "LANGUAGE_BIDI": translation.get_language_bidi(),
        "LANGUAGE_NAME": dict(settings.LANGUAGES).get(
            current_language, current_language
        ),
        "ALTERNATIVE_LANGUAGE": "en" if current_language == "tr" else "tr",
        "LANGUAGE_TOGGLE_URL": reverse("main:set_language"),
        "LANGUAGE_STATUS_URL": reverse("main:language_status"),
    }


def csp_nonce(request: HttpRequest) -> Dict[str, str]:
    """
    Context processor to provide CSP nonce for templates.
    Allows templates to use inline scripts and styles securely.
    """
    return {"csp_nonce": getattr(request, "csp_nonce", "")}
