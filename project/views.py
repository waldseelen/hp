from __future__ import annotations

from typing import Dict, List

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _


def _safe_url(name: str, default: str = "/") -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return default


def _navigation_links() -> List[Dict[str, str]]:
    return [
        {
            "title": _("Return to homepage"),
            "description": _("Start fresh from the main dashboard."),
            "url": _safe_url("home"),
            "icon": "home",
        },
        {
            "title": _("Browse recent blog posts"),
            "description": _("Catch up on the latest tutorials and articles."),
            "url": _safe_url("blog:list", "/blog/"),
            "icon": "blog",
        },
        {
            "title": _("Explore featured projects"),
            "description": _("See portfolio highlights and case studies."),
            "url": _safe_url("tools:list", "/tools/"),
            "icon": "rocket",
        },
        {
            "title": _("Get in touch"),
            "description": _("Have a question? Reach out through the contact form."),
            "url": _safe_url("contact:form", "/contact/"),
            "icon": "mail",
        },
    ]


def custom_404(request, exception):
    """Custom 404 error handler with helpful navigation."""
    request.breadcrumbs_override = [
        {"name": _("Error")},
        {"name": "404"},
    ]

    context = {
        "request_path": request.path,
        "site_name": "Portfolio",
        "error_code": "404",
        "error_message": _("The page you are looking for does not exist."),
        "navigation_links": _navigation_links(),
        "search_placeholder": _("Search the site..."),
        "show_search": True,
        "suggested_terms": ["AI", "Cybersecurity", "Full Stack"],
        "support_email": "support@example.com",
    }
    return render(request, "errors/404.html", context, status=404)


def custom_500(request):
    """Custom 500 error handler that offers recovery options."""
    request.breadcrumbs_override = [
        {"name": _("Error")},
        {"name": "500"},
    ]

    context = {
        "site_name": "Portfolio",
        "error_code": "500",
        "error_message": _("Something went wrong on our side."),
        "navigation_links": _navigation_links(),
        "support_email": "support@example.com",
        "retry_suggestion": _("Please try again in a moment or return to a safe page."),
        "show_search": False,
    }
    return render(request, "errors/500.html", context, status=500)
