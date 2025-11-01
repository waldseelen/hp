from __future__ import annotations

from typing import Any, Dict, Iterable, List

from django.conf import settings
from django.urls import NoReverseMatch, Resolver404, resolve, reverse
from django.utils.translation import gettext_lazy as _

from .models import SocialLink

SECTION_LABELS: Dict[str, str] = {
    "blog": _("Blog"),
    "tools": _("Projects"),
    "contact": _("Contact"),
    "chat": _("Chat"),
    "personal": _("About"),
    "music": _("Music"),
    "playground": _("Playground"),
    "ai": _("AI Tools"),
    "cybersecurity": _("Cybersecurity"),
    "useful": _("Useful"),
}

BREADCRUMB_CONFIG: Dict[str, List[Dict[str, Any]]] = {
    "home": [],
    "main:personal": [{"name": _("About")}],
    "main:music": [{"name": _("Music")}],
    "main:ai": [{"name": _("AI Tools")}],
    "main:cybersecurity": [{"name": _("Cybersecurity")}],
    "main:useful": [{"name": _("Useful")}],
    "blog:list": [{"name": _("Blog")}],
    "blog:detail": [
        {"name": _("Blog"), "url_name": "blog:list"},
        {"name": _("Article")},
    ],
    "tools:list": [{"name": _("Projects")}],
    "tools:detail": [
        {"name": _("Projects"), "url_name": "tools:list"},
        {"name": _("Project Detail")},
    ],
    "contact:form": [{"name": _("Contact")}],
    "contact:success": [
        {"name": _("Contact"), "url_name": "contact:form"},
        {"name": _("Thank You")},
    ],
    "chat:chat": [{"name": _("Chat")}],
    "playground:index": [{"name": _("Playground")}],
    "playground:editor": [
        {"name": _("Playground"), "url_name": "playground:index"},
        {"name": _("Editor")},
    ],
    "playground:editor_language": [
        {"name": _("Playground"), "url_name": "playground:index"},
        {"name": _("Editor"), "url_name": "playground:editor"},
        {"name": _("Language")},
    ],
}


def _normalize_items(items: Any) -> List[Dict[str, Any]]:
    normalized: List[Dict[str, Any]] = []
    if not items:
        return normalized
    iterable: Iterable[Any]
    if isinstance(items, dict):
        iterable = [items]
    elif isinstance(items, (list, tuple, set)):
        iterable = items
    else:
        iterable = [items]

    for raw in iterable:
        if isinstance(raw, dict):
            name = raw.get("name") or raw.get("title")
            if not name:
                continue
            normalized.append(
                {
                    "name": str(name),
                    "url": raw.get("url"),
                }
            )
        elif isinstance(raw, (list, tuple)) and raw:
            name = raw[0]
            url = raw[1] if len(raw) > 1 else None
            normalized.append(
                {
                    "name": str(name),
                    "url": url,
                }
            )
    return normalized


def _configured_items(identifier: str) -> List[Dict[str, Any]]:
    configured = BREADCRUMB_CONFIG.get(identifier, [])
    items: List[Dict[str, Any]] = []
    for entry in configured:
        name = entry.get("name") or entry.get("title")
        if not name:
            continue
        crumb: Dict[str, Any] = {"name": str(name), "url": entry.get("url")}
        url_name = entry.get("url_name")
        if url_name and not crumb.get("url"):
            try:
                crumb["url"] = reverse(url_name)
            except NoReverseMatch:
                crumb["url"] = None
        items.append(crumb)
    return items


def _path_fallback(path: str) -> List[Dict[str, Any]]:
    parts = [part for part in path.split("/") if part]
    breadcrumbs: List[Dict[str, Any]] = []
    current = ""
    for part in parts:
        current += f"/{part}"
        label = SECTION_LABELS.get(part, part.replace("-", " ").title())
        breadcrumbs.append({"name": str(label), "url": current})
    return breadcrumbs


def social_links(request):
    """Expose social links globally."""
    return {
        "global_social_links": SocialLink.objects.filter(is_visible=True).order_by(
            "order", "platform"
        )
    }


def global_context(request):
    """Provide site-wide context helpers."""
    return {
        "site_name": getattr(settings, "SITE_NAME", "Portfolio"),
        "current_path": request.path,
        "is_authenticated": (
            request.user.is_authenticated if hasattr(request, "user") else False
        ),
    }


def breadcrumbs(request):  # noqa: C901
    """Build breadcrumb trail based on resolved URL and optional view hints."""
    try:
        match = getattr(request, "resolver_match", None) or resolve(request.path_info)
    except Resolver404:
        return {"breadcrumbs": []}

    try:
        home_url = reverse("home")
    except NoReverseMatch:
        home_url = "/"

    breadcrumb_items: List[Dict[str, Any]] = [
        {
            "name": _("Home"),
            "url": home_url,
            "active": False,
        }
    ]

    override_items = _normalize_items(getattr(request, "breadcrumbs_override", None))
    if override_items:
        tail = override_items
    else:
        identifier = ":".join(filter(None, [match.namespace, match.url_name]))
        tail = _configured_items(identifier)
        if not tail and match.url_name:
            tail = _configured_items(match.url_name)
        if not tail:
            tail = _path_fallback(request.path)

    extra_items = _normalize_items(getattr(request, "breadcrumbs_extra", None))
    if extra_items:
        tail.extend(extra_items)

    if tail:
        breadcrumb_items.extend(tail)

    if breadcrumb_items:
        for crumb in breadcrumb_items:
            crumb["active"] = False
        breadcrumb_items[-1]["active"] = True

    return {"breadcrumbs": breadcrumb_items}


def language_context(request):
    current_language = getattr(request, "LANGUAGE_CODE", None)
    return {
        "available_languages": getattr(settings, "LANGUAGES", ()),
        "current_language": current_language,
    }


def csp_nonce(request):
    return {"csp_nonce": getattr(request, "csp_nonce", "")}
