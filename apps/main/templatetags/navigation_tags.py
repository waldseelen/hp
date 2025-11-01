from __future__ import annotations

from typing import Iterable

from django import template
from django.urls import Resolver404, resolve

register = template.Library()


def _matches_target(match, target: str) -> bool:
    if not target:
        return False
    namespace = match.namespace or ""
    url_name = match.url_name or ""
    current_full = ":".join(filter(None, [namespace, url_name]))

    candidates: Iterable[str]
    if "|" in target:
        candidates = (candidate.strip() for candidate in target.split("|"))
    else:
        candidates = (target,)

    for candidate in candidates:
        if not candidate:
            continue
        if candidate == current_full:
            return True
        if ":" not in candidate and candidate == url_name:
            return True
        if candidate.endswith(":*") and current_full.startswith(candidate[:-2]):
            return True
    return False


def _resolve_request(context):
    request = context.get("request")
    if not request:
        return None, None
    try:
        return request, resolve(request.path_info)
    except Resolver404:
        return request, None


@register.simple_tag(takes_context=True)
def nav_active(context, url_name: str, css_class: str = "is-active") -> str:
    """Return css_class when current view matches url_name (supports namespaces)."""
    request, match = _resolve_request(context)
    if not request or not match:
        return ""
    return css_class if _matches_target(match, url_name) else ""


@register.simple_tag(takes_context=True)
def nav_active_any(context, url_names: str, css_class: str = "is-active") -> str:
    """Allow pipe-delimited list of url names to share the same active class."""
    request, match = _resolve_request(context)
    if not request or not match:
        return ""
    return css_class if _matches_target(match, url_names) else ""


@register.simple_tag(takes_context=True)
def is_current_page(context, url_names: str) -> bool:
    """Return True when the resolved URL matches any provided name."""
    _, match = _resolve_request(context)
    if not match:
        return False
    return _matches_target(match, url_names)


@register.simple_tag(takes_context=True)
def nav_section_active(context, path_prefix: str, css_class: str = "is-active") -> str:
    """Mark navigation active when the request path starts with the prefix."""
    request = context.get("request")
    if not request or not path_prefix:
        return ""
    return css_class if request.path.startswith(path_prefix) else ""


@register.inclusion_tag("components/navigation/breadcrumb.html", takes_context=True)
def render_breadcrumbs(context):
    """Render breadcrumb partial with provided breadcrumb items."""
    breadcrumbs = context.get("breadcrumbs", [])
    return {"breadcrumbs": breadcrumbs}
