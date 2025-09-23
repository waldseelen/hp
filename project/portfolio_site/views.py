from __future__ import annotations

from typing import Dict, List

from django.shortcuts import render
from django.urls import NoReverseMatch, reverse
from django.utils.translation import gettext_lazy as _


def _safe_url(name: str, default: str = '/') -> str:
    try:
        return reverse(name)
    except NoReverseMatch:
        return default


def _navigation_links() -> List[Dict[str, str]]:
    return [
        {
            'title': _('Back to homepage'),
            'url': _safe_url('home'),
        },
        {
            'title': _('Visit the blog'),
            'url': _safe_url('blog:list', '/blog/'),
        },
        {
            'title': _('Explore projects'),
            'url': _safe_url('tools:list', '/tools/'),
        },
        {
            'title': _('Contact support'),
            'url': _safe_url('contact:form', '/contact/'),
        },
    ]


def error_404_view(request, exception, template_name='errors/404.html'):
    request.breadcrumbs_override = [
        {'name': _('Error')},
        {'name': '404'},
    ]

    context = {
        'request_path': request.path,
        'site_name': 'Portfolio',
        'error_code': '404',
        'error_message': _('Page not found'),
        'navigation_links': _navigation_links(),
        'search_placeholder': _('Search the site...'),
    }
    return render(request, template_name, context=context, status=404)


def error_500_view(request, template_name='errors/500.html'):
    request.breadcrumbs_override = [
        {'name': _('Error')},
        {'name': '500'},
    ]

    context = {
        'site_name': 'Portfolio',
        'error_code': '500',
        'error_message': _('Server error'),
        'navigation_links': _navigation_links(),
        'support_email': 'support@example.com',
        'retry_suggestion': _('Please try again in a moment or return to a safe page.'),
        'show_search': False,
    }
    return render(request, template_name, context=context, status=500)
