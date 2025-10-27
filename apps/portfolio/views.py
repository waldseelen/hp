"""
Enhanced Main Views Module
Provides comprehensive views for the portfolio site with:
- Performance optimizations and caching strategies
- Analytics integration and user behavior tracking
- SEO enhancements and metadata generation
- Progressive web app features
- Advanced error handling and logging
- Real-time content updates and notifications
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any, Union, Tuple
from django.http import HttpRequest, HttpResponse, JsonResponse, Http404
from django.template.response import TemplateResponse

from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import logout
from django.contrib.auth.decorators import login_required
from django.core.cache import cache
from django.utils import timezone, translation
from django.utils.translation import gettext as _
from django.db.models import Q, Count, Avg, Max, F, Case, When, Value, IntegerField
from django.core.paginator import Paginator, PageNotAnInteger, EmptyPage
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.views.decorators.vary import vary_on_headers
from django.contrib.sitemaps import ping_google
from django.conf import settings
# from .cache_utils import (
#     CacheManager, cache_result, cache_queryset_medium, cache_long,
#     cache_page_data, ModelCacheManager
# )
from django.urls import reverse
from django.template.loader import render_to_string
from django.utils.decorators import method_decorator
from django.views import View
from .fixtures_provider import get_ui_kit_fixtures

# Import models
from .models import (
    PersonalInfo, SocialLink, AITool, CybersecurityResource,
    MusicPlaylist, SpotifyCurrentTrack, UsefulResource, Project,
    Skill, Certificate, Hobby, CurrentActivity
)
from apps.blog.models import Post
from apps.tools.models import Tool
from apps.main.search import search_engine

# Import APM decorators for distributed tracing
from .utils.apm_decorators import trace_function, trace_database_operation, trace_cache_operation, trace_api_call, trace_operation

# Setup enhanced logging
logger = logging.getLogger(__name__)

# Constants
CACHE_TIMEOUT_SHORT = 300    # 5 minutes
CACHE_TIMEOUT_MEDIUM = 900   # 15 minutes
CACHE_TIMEOUT_LONG = 3600    # 1 hour
CACHE_TIMEOUT_DAILY = 86400  # 24 hours


@trace_function(operation_name="view.home", description="Home page view with analytics", tags={"view_type": "main"})
def home(request: HttpRequest) -> HttpResponse:
    """
    Enhanced home page view with analytics, performance optimization, and rich metadata.
    Features real-time stats, visitor tracking, and progressive enhancement.
    """
    try:
        # Get user info for analytics
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        visitor_ip = get_client_ip(request)
        is_mobile = 'Mobile' in user_agent

        # Dynamic cache key based on user type and time
        cache_key = f'home_page_data_{hash(user_agent[:50])}_{timezone.now().hour}'
        cached_data = cache.get(cache_key)

        if cached_data is None:
            # Fetch data with optimized queries and annotations
            personal_info = PersonalInfo.objects.filter(
                is_visible=True
            ).select_related().order_by('order', 'key')

            social_links = SocialLink.objects.filter(
                is_visible=True
            ).order_by('order', 'platform')

            # Get recent published posts with enhanced metadata
            recent_posts = Post.objects.select_related('author').prefetch_related('tags').filter(
                status='published',
                published_at__lte=timezone.now()
            ).annotate(
                read_time=Case(
                    When(content__isnull=False, then=F('content_length') / 200),
                    default=Value(3),
                    output_field=IntegerField()
                )
            ).order_by('-published_at')[:6]  # Get more posts for variety

            # Get featured projects with stats
            featured_projects = Project.objects.filter(
                is_visible=True,
                is_featured=True
            ).order_by('-created_at')[:3]

            # Get featured AI tools with enhanced data
            featured_ai_tools = AITool.objects.filter(
                is_featured=True,
                is_visible=True
            ).order_by('order', 'name')[:8]  # More tools for better variety

            # Get urgent cybersecurity resources with severity analysis
            urgent_security = CybersecurityResource.objects.filter(
                is_urgent=True,
                is_visible=True
            ).order_by('-severity_level', '-created_at', 'title')[:6]

            # Get portfolio statistics
            portfolio_stats = get_portfolio_statistics()

            # Get current activity
            current_activity = CurrentActivity.objects.filter(
                is_active=True
            ).order_by('-updated_at').first()

            # Get latest skills
            latest_skills = Skill.objects.filter(
                is_visible=True
            ).order_by('-proficiency_level', 'name')[:10]

            cached_data = {
                'personal_info': list(personal_info),
                'social_links': list(social_links),
                'recent_posts': list(recent_posts),
                'featured_projects': list(featured_projects),
                'featured_ai_tools': list(featured_ai_tools),
                'urgent_security': list(urgent_security),
                'portfolio_stats': portfolio_stats,
                'current_activity': current_activity,
                'latest_skills': list(latest_skills),
                'last_updated': timezone.now().isoformat(),
            }

            # Cache with shorter timeout for dynamic content
            cache.set(cache_key, cached_data, CACHE_TIMEOUT_MEDIUM)

        # Enhanced context with SEO and PWA features
        context = {
            'personal_info': cached_data['personal_info'],
            'social_links': cached_data['social_links'],
            'recent_posts': cached_data['recent_posts'],
            'featured_projects': cached_data['featured_projects'],
            'featured_ai_tools': cached_data['featured_ai_tools'],
            'urgent_security': cached_data['urgent_security'],
            'portfolio_stats': cached_data['portfolio_stats'],
            'current_activity': cached_data['current_activity'],
            'latest_skills': cached_data['latest_skills'],

            # SEO and metadata
            'page_title': 'Professional Portfolio - Full Stack Developer & Cybersecurity Expert',
            'meta_description': 'Explore innovative projects, cutting-edge AI tools, cybersecurity insights, and technical expertise. Building secure, scalable solutions with modern technologies.',
            'canonical_url': request.build_absolute_uri('/'),
            'og_image': request.build_absolute_uri('/static/images/og-home.jpg'),
            'schema_type': 'Person',

            # PWA and UX enhancements
            'is_mobile': is_mobile,
            'visitor_location': get_visitor_location(visitor_ip),
            'page_load_time': timezone.now().isoformat(),
            'cache_version': cached_data['last_updated'],
            'show_animations': not is_mobile,  # Disable complex animations on mobile

            # Analytics data
            'page_id': 'home',
            'content_sections': ['hero', 'services', 'blog', 'projects', 'ai_tools', 'security'],
        }

        # Log page view for analytics
        log_page_view(request, 'home', context.get('visitor_location'))

        return render(request, 'pages/portfolio/home.html', context)

    except Exception as e:
        logger.error(f"Error in home view: {str(e)}", extra={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'path': request.path,
            'method': request.method
        })

        # Fallback context with error tracking
        context = create_fallback_context('home', 'Portfolio Home - Technical Error', e)
        return render(request, 'pages/portfolio/home.html', context)


def personal_view(request: HttpRequest) -> HttpResponse:
    """
    About/Personal page view with personal information.
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

            cached_data = {
                'personal_info': list(personal_info),
                'social_links': list(social_links),
            }

            cache.set(cache_key, cached_data, 900)

        context = {
            'personal_info': cached_data['personal_info'],
            'social_links': cached_data['social_links'],
            'page_title': 'Hakkımda',
            'meta_description': 'Kişisel bilgiler, yetenekler ve deneyimler',
        }

        return render(request, 'pages/portfolio/personal.html', context)

    except Exception as e:
        logger.error(f"Error in personal view: {str(e)}")
        context = {
            'personal_info': [],
            'social_links': [],
            'page_title': 'Hakkımda',
            'meta_description': 'Kişisel bilgiler',
        }
        return render(request, 'pages/portfolio/personal.html', context)


def music_view(request: HttpRequest) -> HttpResponse:
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

        return render(request, 'pages/portfolio/music.html', context)

    except Exception as e:
        logger.error(f"Error in music view: {str(e)}")
        context = {
            'playlists': [],
            'featured_playlists': [],
            'current_track': None,
            'page_title': 'Müzik',
            'meta_description': 'Müzik',
        }
        return render(request, 'pages/portfolio/music.html', context)


def ai_tools_view(request: HttpRequest) -> HttpResponse:
    """
    AI Tools page view with AI resources and tools.
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

        return render(request, 'pages/portfolio/ai.html', context)

    except Exception as e:
        logger.error(f"Error in ai_tools view: {str(e)}")
        context = {
            'ai_tools_by_category': {},
            'page_title': 'AI Araçları',
            'meta_description': 'Yapay zeka araçları',
        }
        return render(request, 'pages/portfolio/ai.html', context)


def cybersecurity_view(request: HttpRequest) -> HttpResponse:
    """
    Cybersecurity page view with security content and resources.
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

        return render(request, 'pages/portfolio/cybersecurity.html', context)

    except Exception as e:
        logger.error(f"Error in cybersecurity view: {str(e)}")
        context = {
            'resources_by_type': {},
            'urgent_threats': [],
            'page_title': 'Siber Güvenlik',
            'meta_description': 'Siber güvenlik',
        }
        return render(request, 'pages/portfolio/cybersecurity.html', context)


def useful_view(request: HttpRequest) -> HttpResponse:
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

        return render(request, 'pages/portfolio/useful.html', context)

    except Exception as e:
        logger.error(f"Error in useful view: {str(e)}")
        context = {
            'resources_by_category': {},
            'featured_resources': [],
            'page_title': 'Useful Resources',
            'meta_description': 'Faydalı kaynaklar',
        }
        return render(request, 'pages/portfolio/useful.html', context)


# Enhanced API and utility views
@require_http_methods(["GET"])
def search_view(request: HttpRequest) -> HttpResponse:
    """
    Enhanced search view with faceted search, analytics, and suggestions
    """
    try:
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', 'all')
        sort_by = request.GET.get('sort', 'relevance')
        page = request.GET.get('page', 1)

        context = {
            'query': query,
            'category': category,
            'sort_by': sort_by,
            'results': [],
            'total_results': 0,
            'suggestions': [],
            'popular_searches': [],
            'categories': get_search_categories(),
            'sort_options': get_sort_options(),
        }

        if query and len(query.strip()) >= 2:
            # Perform search
            search_results = search_engine.search(
                query=query,
                categories=[category] if category != 'all' else None,
                limit=100
            )

            # Pagination
            paginator = Paginator(search_results['results'], 20)
            try:
                page_results = paginator.page(page)
            except PageNotAnInteger:
                page_results = paginator.page(1)
            except EmptyPage:
                page_results = paginator.page(paginator.num_pages)

            context.update({
                'results': page_results,
                'total_results': search_results['total_count'],
                'suggestions': search_results['suggestions'],
                'categories_found': search_results['categories'],
                'paginator': paginator,
                'is_paginated': paginator.num_pages > 1,
                'search_time': 'instant',  # Could be actual search time
            })

            # Log search for analytics
            log_search_query(request, query, category, search_results['total_count'])

        # Add popular searches if no query
        if not query:
            context['popular_searches'] = search_engine.get_popular_searches()
            context['recent_content'] = search_engine.get_recent_content()

        # SEO for search page
        context.update({
            'page_title': f'Search Results for "{query}"' if query else 'Search',
            'meta_description': f'Search results for {query}' if query else 'Search the portfolio for projects, blog posts, tools and more',
            'canonical_url': request.build_absolute_uri(),
            'noindex': True if query else False,  # Don't index search result pages
        })

        return render(request, 'search/search.html', context)

    except Exception as e:
        logger.error(f"Search view error: {str(e)}")
        context = create_fallback_context('search', 'Search - Technical Error', e)
        return render(request, 'search/search.html', context)

@require_http_methods(["GET"])
def search_ajax(request: HttpRequest) -> JsonResponse:
    """
    AJAX search endpoint for real-time suggestions and results
    """
    try:
        query = request.GET.get('q', '').strip()
        limit = min(int(request.GET.get('limit', 10)), 50)  # Max 50 results
        category = request.GET.get('category', 'all')

        if not query or len(query) < 2:
            return JsonResponse({
                'results': [],
                'suggestions': search_engine.get_popular_searches(5),
                'total': 0,
                'status': 'success'
            })

        # Perform search
        search_results = search_engine.search(
            query=query,
            categories=[category] if category != 'all' else None,
            limit=limit
        )

        # Format results for JSON
        formatted_results = []
        for result in search_results['results']:
            formatted_results.append({
                'title': result.get('title', ''),
                'description': result.get('description', '')[:150],
                'url': result.get('url', '#'),
                'category': result.get('category_name', ''),
                'icon': result.get('category_icon', ''),
                'score': result.get('relevance_score', 0),
                'metadata': result.get('metadata', {}),
                'tags': result.get('tags', [])[:3],  # Limit tags for JSON
            })

        return JsonResponse({
            'results': formatted_results,
            'suggestions': search_results['suggestions'],
            'total': search_results['total_count'],
            'query': query,
            'categories': search_results['categories'],
            'status': 'success'
        })

    except Exception as e:
        logger.error(f"AJAX search error: {str(e)}")
        return JsonResponse({
            'results': [],
            'suggestions': [],
            'total': 0,
            'error': 'Search temporarily unavailable',
            'status': 'error'
        }, status=500)

@require_http_methods(["GET"])
def projects_view(request: HttpRequest) -> HttpResponse:
    """
    Enhanced projects listing page with filtering and search
    """
    try:
        # Get filter parameters
        category = request.GET.get('category', 'all')
        tech = request.GET.get('tech', '')
        featured = request.GET.get('featured', '')
        page = request.GET.get('page', 1)

        # Build queryset with filters
        projects = Project.objects.filter(is_visible=True)

        if category != 'all' and category:
            projects = projects.filter(category=category)

        if tech:
            projects = projects.filter(tech_stack__icontains=tech)

        if featured == 'true':
            projects = projects.filter(is_featured=True)

        # Order by featured first, then by date
        projects = projects.order_by('-is_featured', '-created_at')

        # Pagination
        paginator = Paginator(projects, 12)  # 12 projects per page
        try:
            page_projects = paginator.page(page)
        except PageNotAnInteger:
            page_projects = paginator.page(1)
        except EmptyPage:
            page_projects = paginator.page(paginator.num_pages)

        # Get categories and technologies for filters
        categories = Project.objects.filter(is_visible=True).values_list('category', flat=True).distinct()
        technologies = []
        for project in Project.objects.filter(is_visible=True):
            if project.tech_stack:
                techs = [t.strip() for t in project.tech_stack.split(',')]
                technologies.extend(techs)
        technologies = sorted(list(set(technologies)))

        context = {
            'projects': page_projects,
            'categories': categories,
            'technologies': technologies,
            'selected_category': category,
            'selected_tech': tech,
            'featured_only': featured == 'true',
            'paginator': paginator,
            'is_paginated': paginator.num_pages > 1,
            'page_title': 'Projects - Portfolio',
            'meta_description': 'Explore my latest projects, from web applications to cybersecurity tools. Built with modern technologies and best practices.',
            'canonical_url': request.build_absolute_uri(),
        }

        return render(request, 'pages/portfolio/projects.html', context)

    except Exception as e:
        logger.error(f"Projects view error: {str(e)}")
        context = create_fallback_context('projects', 'Projects - Technical Error', e)
        return render(request, 'pages/portfolio/projects.html', context)

@require_http_methods(["GET"])
def project_detail_view(request: HttpRequest, slug: str) -> HttpResponse:
    """
    Enhanced project detail view with related projects and analytics
    """
    try:
        project = get_object_or_404(Project, slug=slug, is_visible=True)

        # Get related projects
        related_projects = Project.objects.filter(
            is_visible=True,
            category=project.category
        ).exclude(id=project.id).order_by('-created_at')[:4]

        # Get project technologies
        technologies = []
        if project.tech_stack:
            technologies = [t.strip() for t in project.tech_stack.split(',')]

        context = {
            'project': project,
            'related_projects': related_projects,
            'technologies': technologies,
            'page_title': f'{project.title} - Project Details',
            'meta_description': project.description[:160],
            'canonical_url': request.build_absolute_uri(),
            'og_image': project.image.url if project.image else None,
            'schema_type': 'CreativeWork',
        }

        # Log project view
        log_page_view(request, f'project_{project.slug}')

        return render(request, 'pages/portfolio/project_detail.html', context)

    except Http404:
        raise
    except Exception as e:
        logger.error(f"Project detail view error: {str(e)}")
        context = create_fallback_context('project_detail', 'Project Details - Technical Error', e)
        return render(request, 'pages/portfolio/project_detail.html', context)

def logout_view(request: HttpRequest) -> HttpResponse:
    """
    Enhanced logout view with proper cleanup and analytics
    """
    try:
        # Log logout for analytics
        if request.user.is_authenticated:
            log_user_action(request, 'logout', request.user.username)

        logout(request)

        # Clear user-specific cache
        if hasattr(request, 'session'):
            cache.delete(f"user_data_{request.session.session_key}")

        return redirect('home')

    except Exception as e:
        logger.error(f"Error in logout view: {str(e)}")
        return redirect('home')


# Utility functions
def get_client_ip(request: HttpRequest) -> str:
    """Get the real client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        ip = request.META.get('REMOTE_ADDR', '127.0.0.1')
    return ip

def get_visitor_location(ip_address: str) -> Dict[str, str]:
    """Get visitor location from IP (placeholder for GeoIP integration)"""
    # This would integrate with a GeoIP service
    # For now, return a placeholder
    return {
        'country': 'Unknown',
        'city': 'Unknown',
        'timezone': 'UTC'
    }

def get_portfolio_statistics() -> Dict[str, Union[int, str]]:
    """Calculate and return portfolio statistics"""
    try:
        cache_key = 'portfolio_statistics'
        stats = cache.get(cache_key)

        if stats is None:
            stats = {
                'total_projects': Project.objects.filter(is_visible=True).count(),
                'blog_posts': Post.objects.filter(status='published').count(),
                'ai_tools': AITool.objects.filter(is_visible=True).count(),
                'security_resources': CybersecurityResource.objects.filter(is_visible=True).count(),
                'years_experience': 3,  # Could be calculated from first project date
                'technologies_used': 25,  # Could be calculated from project tech stacks
                'certifications': Certificate.objects.filter(is_visible=True).count(),
                'last_updated': timezone.now().strftime('%Y-%m-%d'),
            }

            # Cache for 1 hour
            cache.set(cache_key, stats, CACHE_TIMEOUT_LONG)

        return stats

    except Exception as e:
        logger.error(f"Error calculating portfolio statistics: {str(e)}")
        return {
            'total_projects': 0,
            'blog_posts': 0,
            'ai_tools': 0,
            'security_resources': 0,
            'years_experience': 3,
            'technologies_used': 25,
            'certifications': 0,
            'last_updated': timezone.now().strftime('%Y-%m-%d'),
        }

def get_search_categories() -> List[Dict[str, str]]:
    """Get available search categories"""
    return [
        {'value': 'all', 'label': 'All Categories', 'icon': '🔍'},
        {'value': 'blog_posts', 'label': 'Blog Posts', 'icon': '📝'},
        {'value': 'projects', 'label': 'Projects', 'icon': '🚀'},
        {'value': 'ai_tools', 'label': 'AI Tools', 'icon': '🤖'},
        {'value': 'cybersecurity', 'label': 'Security', 'icon': '🔒'},
        {'value': 'tools', 'label': 'Tools', 'icon': '🔧'},
        {'value': 'useful_resources', 'label': 'Resources', 'icon': '🔗'},
    ]

def get_sort_options() -> List[Dict[str, str]]:
    """Get available sort options"""
    return [
        {'value': 'relevance', 'label': 'Most Relevant'},
        {'value': 'date', 'label': 'Most Recent'},
        {'value': 'title', 'label': 'Alphabetical'},
        {'value': 'category', 'label': 'By Category'},
    ]

def create_fallback_context(page_id: str, title: str, error: Optional[Exception] = None) -> Dict[str, Any]:
    """Create fallback context for error situations"""
    return {
        'page_title': title,
        'meta_description': 'Portfolio page temporarily unavailable',
        'page_id': page_id,
        'error_occurred': True,
        'error_message': 'Content temporarily unavailable' if not settings.DEBUG else str(error),
        'canonical_url': '/',
    }

@ratelimit(key='ip', rate='200/h', method=ratelimit_ALL)
def log_page_view(request: HttpRequest, page_id: str, location: Optional[Dict[str, str]] = None) -> None:
    """Log page view for analytics (implement as needed)"""
    try:
        # This would typically integrate with analytics services
        # For now, just log to Django logger
        logger.info(f"Page view: {page_id}", extra={
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'ip_address': get_client_ip(request),
            'location': location,
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error logging page view: {str(e)}")

@ratelimit(key='ip', rate='100/h', method=ratelimit_ALL)
def log_search_query(request: HttpRequest, query: str, category: str, result_count: int) -> None:
    """Log search query for analytics"""
    try:
        logger.info(f"Search performed: '{query}' in '{category}' - {result_count} results", extra={
            'query': query,
            'category': category,
            'result_count': result_count,
            'ip_address': get_client_ip(request),
            'user_agent': request.META.get('HTTP_USER_AGENT', ''),
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error logging search query: {str(e)}")

def log_user_action(request: HttpRequest, action: str, user_id: Optional[str] = None) -> None:
    """Log user actions for analytics"""
    try:
        logger.info(f"User action: {action}", extra={
            'action': action,
            'user_id': user_id,
            'ip_address': get_client_ip(request),
            'timestamp': timezone.now().isoformat(),
        })
    except Exception as e:
        logger.error(f"Error logging user action: {str(e)}")


# Internationalization Views
# ==========================

@require_http_methods(["GET", "POST"])
def set_language(request: HttpRequest) -> HttpResponse:
    """
    Set the language preference for the user.
    Compatible with Django's built-in set_language view but with enhanced features.
    """
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
        log_user_action(request, f'language_changed_to_{language}')

        return response

    # If language is invalid, redirect to previous page or home
    return redirect(next_url or '/')


@require_http_methods(["GET"])
def language_status(request: HttpRequest) -> JsonResponse:
    """
    Return current language status as JSON.
    Useful for JavaScript language management.
    """
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


def get_language_context(request: HttpRequest) -> Dict[str, Any]:
    """
    Get language-related context for templates.
    This can be used in context processors or views.
    """
    current_language = translation.get_language()

    return {
        'current_language': current_language,
        'available_languages': settings.LANGUAGES,
        'is_rtl': translation.get_language_bidi(),
        'language_name': dict(settings.LANGUAGES).get(current_language, current_language),
        'alternative_language': 'en' if current_language == 'tr' else 'tr',
        'language_toggle_url': reverse('set_language'),
    }


# ==========================================================================
# API ENDPOINTS FOR PERFORMANCE MONITORING AND PUSH NOTIFICATIONS
# ==========================================================================

from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.generics import ListCreateAPIView, RetrieveUpdateDestroyAPIView, ListAPIView
from rest_framework import filters
from django_filters.rest_framework import DjangoFilterBackend
from django_ratelimit.decorators import ratelimit
from django_ratelimit import ALL as ratelimit_ALL
from django.utils.decorators import method_decorator

from .serializers import (
    PerformanceMetricSerializer,
    PerformanceMetricSummarySerializer,
    WebPushSubscriptionSerializer,
    SendNotificationSerializer,
    NotificationLogSerializer,
    ErrorLogSerializer,
    HealthCheckSerializer,
    PersonalInfoSerializer,
    SocialLinkSerializer,
    AIToolSerializer,
    CybersecurityResourceSerializer,
    UsefulResourceSerializer
)
from .models import PerformanceMetric, WebPushSubscription, NotificationLog, ErrorLog


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
@method_decorator(ratelimit(key='ip', rate=settings.API_RATE_LIMITS.get('performance', '100/h'), method='POST'), name='post')
def collect_performance_metric(request: HttpRequest) -> Response:
    """
    API endpoint to collect performance metrics from frontend
    Rate limited and validates incoming data
    """
    try:
        serializer = PerformanceMetricSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            metric = serializer.save()

            # Log performance metric for monitoring
            logger = logging.getLogger('main.performance')
            logger.info(
                f"Performance metric collected: {metric.metric_type}={metric.value} "
                f"from {metric.device_type} at {metric.url}"
            )

            # Check for performance issues and alert if necessary
            if not metric.is_good_score:
                alert_performance_issue(metric)

            return Response({
                'status': 'success',
                'message': 'Performance metric recorded',
                'id': metric.id
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Invalid data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error collecting performance metric: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def performance_dashboard_data(request: HttpRequest) -> Response:
    """
    API endpoint to get performance metrics summary for dashboard
    Requires authentication for admin access
    """
    try:
        from django.db.models import Avg, Count, Case, When, Value, IntegerField, FloatField
        from django.contrib.postgres.aggregates import Percentile
        from datetime import datetime, timedelta

        # Get time period from query params
        period_days = int(request.GET.get('period', 7))
        start_date = timezone.now() - timedelta(days=period_days)

        # Get metrics grouped by type with database aggregations
        metrics_summary = PerformanceMetric.objects.filter(
            timestamp__gte=start_date
        ).values('metric_type').annotate(
            count=Count('id'),
            average=Avg('value'),
            median=Percentile('value', 0.5, output_field=FloatField()),
            p75=Percentile('value', 0.75, output_field=FloatField()),
            p95=Percentile('value', 0.95, output_field=FloatField()),
            # Define good/poor thresholds using database CASE expressions
            good_count=Count(Case(
                When(metric_type='lcp', value__lt=2.5, then=Value(1)),
                When(metric_type='fid', value__lt=100, then=Value(1)),
                When(metric_type='cls', value__lt=0.1, then=Value(1)),
                When(metric_type='ttfb', value__lt=800, then=Value(1)),
                default=None,
                output_field=IntegerField()
            )),
            poor_count=Count(Case(
                When(metric_type='lcp', value__gte=4.0, then=Value(1)),
                When(metric_type='fid', value__gte=300, then=Value(1)),
                When(metric_type='cls', value__gte=0.25, then=Value(1)),
                When(metric_type='ttfb', value__gte=1800, then=Value(1)),
                default=None,
                output_field=IntegerField()
            ))
        ).order_by('metric_type')

        # Add computed fields
        for summary in metrics_summary:
            summary['needs_improvement_count'] = summary['count'] - summary['good_count'] - summary['poor_count']
            summary['period_start'] = start_date
            summary['period_end'] = timezone.now()

        # Get device type breakdown
        device_breakdown = PerformanceMetric.objects.filter(
            timestamp__gte=start_date
        ).values('device_type').annotate(
            count=Count('id'),
            avg_lcp=Avg('value', filter=Q(metric_type='lcp')),
            avg_fid=Avg('value', filter=Q(metric_type='fid')),
            avg_cls=Avg('value', filter=Q(metric_type='cls'))
        ).order_by('-count')

        # Get top URLs by metrics count
        top_urls = PerformanceMetric.objects.filter(
            timestamp__gte=start_date
        ).values('url').annotate(
            count=Count('id')
        ).order_by('-count')[:10]

        return Response({
            'status': 'success',
            'data': {
                'metrics_summary': metrics_summary,
                'device_breakdown': list(device_breakdown),
                'top_urls': list(top_urls),
                'period_days': period_days,
                'total_metrics': PerformanceMetric.objects.filter(timestamp__gte=start_date).count()
            }
        })

    except Exception as e:
        logger.error(f"Error getting performance dashboard data: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@method_decorator(ratelimit(key='ip', rate=settings.API_RATE_LIMITS.get('webpush', '10/m'), method='POST'), name='post')
def subscribe_push_notifications(request: HttpRequest) -> Response:
    """
    API endpoint to subscribe to push notifications
    Rate limited to prevent abuse
    """
    try:
        # Handle nested payload from frontend
        data = request.data.copy()

        # Extract subscription data from nested structure if present
        if 'subscription' in data:
            subscription_data = data['subscription']
            # Flatten the nested structure
            data['endpoint'] = subscription_data.get('endpoint')
            if 'keys' in subscription_data:
                keys = subscription_data['keys']
                data['p256dh'] = keys.get('p256dh')
                data['auth'] = keys.get('auth')

        serializer = WebPushSubscriptionSerializer(data=data, context={'request': request})

        if serializer.is_valid():
            # Check if subscription already exists
            existing = WebPushSubscription.objects.filter(
                endpoint=serializer.validated_data['endpoint']
            ).first()

            if existing:
                # Update existing subscription
                for attr, value in serializer.validated_data.items():
                    setattr(existing, attr, value)
                existing.enabled = True  # Re-enable if it was disabled
                existing.save()
                subscription = existing
                message = 'Push subscription updated'
            else:
                subscription = serializer.save()
                message = 'Push subscription created'

            logger.info(f"Push subscription {message.lower()}: {subscription.browser} from {subscription.ip_address}")

            return Response({
                'status': 'success',
                'message': message,
                'subscription_id': subscription.id
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Invalid subscription data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error creating push subscription: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
@method_decorator(ratelimit(key='ip', rate=settings.API_RATE_LIMITS.get('webpush', '10/m'), method='POST'), name='post')
def send_push_notification(request: HttpRequest) -> Response:
    """
    API endpoint to send push notifications
    Requires authentication for admin use
    """
    try:
        from .services.push_service import PushNotificationService

        serializer = SendNotificationSerializer(data=request.data)

        if serializer.is_valid():
            data = serializer.validated_data
            service = PushNotificationService()

            # Get target subscriptions
            if data.get('target_subscription_ids'):
                subscriptions = WebPushSubscription.objects.filter(
                    id__in=data['target_subscription_ids'],
                    enabled=True
                )
            else:
                subscriptions = WebPushSubscription.objects.filter(enabled=True)

                # Filter by topics if specified
                if data.get('topics'):
                    subscriptions = subscriptions.filter(
                        topics__overlap=data['topics']
                    )

            # Send notifications
            results = service.send_notification_to_subscriptions(
                subscriptions=subscriptions,
                title=data['title'],
                body=data['body'],
                icon=data.get('icon'),
                image=data.get('image'),
                badge=data.get('badge'),
                url=data.get('url'),
                tag=data.get('tag'),
                actions=data.get('actions', []),
                notification_type=data.get('notification_type', 'custom'),
                additional_data=data
            )

            logger.info(f"Push notifications sent: {results['success_count']} successful, {results['failure_count']} failed")

            return Response({
                'status': 'success',
                'message': f'Notifications sent to {results["success_count"]} subscribers',
                'results': results
            })

        return Response({
            'status': 'error',
            'message': 'Invalid notification data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error sending push notification: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
@method_decorator(ratelimit(key='ip', rate='50/h', method='POST'), name='post')
def log_error(request: HttpRequest) -> Response:
    """
    API endpoint to log errors from frontend
    Rate limited to prevent spam
    """
    try:
        serializer = ErrorLogSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            error_log = serializer.save()

            # Log to Django logger as well
            error_logger = logging.getLogger('main.security' if error_log.error_type == 'security' else 'django.request')
            error_logger.error(
                f"Frontend error logged: {error_log.error_type} - {error_log.message} "
                f"at {error_log.url} (line {error_log.line_number})"
            )

            # Send critical errors to monitoring service
            if error_log.level == 'critical':
                alert_critical_error(error_log)

            return Response({
                'status': 'success',
                'message': 'Error logged successfully',
                'error_id': error_log.id
            }, status=status.HTTP_201_CREATED)

        return Response({
            'status': 'error',
            'message': 'Invalid error data',
            'errors': serializer.errors
        }, status=status.HTTP_400_BAD_REQUEST)

    except Exception as e:
        logger.error(f"Error logging frontend error: {str(e)}")
        return Response({
            'status': 'error',
            'message': 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([AllowAny])
def health_check(request: HttpRequest) -> Response:
    """
    Health check endpoint for monitoring and load balancer
    Returns system status and basic metrics
    """
    try:
        from django.db import connections
        from django.core.cache import cache
        import time

        start_time = time.time()
        health_data = {
            'status': 'healthy',
            'timestamp': timezone.now(),
            'version': getattr(settings, 'APP_VERSION', '1.0.0'),
            'database': 'unknown',
            'cache': 'unknown',
            'features': {
                'pwa_enabled': settings.FEATURES.get('PWA_ENABLED', False),
                'push_notifications': settings.FEATURES.get('PUSH_NOTIFICATIONS', False),
                'performance_monitoring': settings.FEATURES.get('PERFORMANCE_MONITORING', False),
            }
        }

        # Check database connection
        try:
            db_conn = connections['default']
            db_conn.cursor().execute('SELECT 1')
            health_data['database'] = 'healthy'
        except Exception as e:
            health_data['database'] = f'error: {str(e)}'
            health_data['status'] = 'degraded'

        # Check cache
        try:
            cache_key = 'health_check_test'
            cache.set(cache_key, 'test_value', 30)
            if cache.get(cache_key) == 'test_value':
                health_data['cache'] = 'healthy'
                cache.delete(cache_key)
            else:
                health_data['cache'] = 'error: cache not working'
                health_data['status'] = 'degraded'
        except Exception as e:
            health_data['cache'] = f'error: {str(e)}'
            health_data['status'] = 'degraded'

        # Add performance data if enabled
        if settings.PERFORMANCE_MONITORING.get('ENABLED', False):
            response_time = time.time() - start_time
            health_data['performance'] = {
                'response_time_ms': round(response_time * 1000, 2),
                'recent_errors': ErrorLog.objects.filter(
                    created_at__gte=timezone.now() - timedelta(hours=1),
                    level__in=['error', 'critical']
                ).count(),
                'active_subscriptions': WebPushSubscription.objects.filter(enabled=True).count(),
            }

        serializer = HealthCheckSerializer(health_data)
        return Response(serializer.data)

    except Exception as e:
        logger.error(f"Health check error: {str(e)}")
        return Response({
            'status': 'unhealthy',
            'timestamp': timezone.now(),
            'error': str(e)
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


# ==========================================================================
# PERFORMANCE MONITORING DASHBOARD VIEW
# ==========================================================================

class PerformanceDashboardView(APIView):
    """
    Performance monitoring dashboard view for admin users
    Provides comprehensive performance analytics and visualizations
    """
    permission_classes = [IsAuthenticated]

    def get(self, request: HttpRequest) -> HttpResponse:
        """Render performance dashboard template"""
        if not request.user.is_staff:
            raise Http404("Dashboard not found")

        # Get basic stats for template context
        total_metrics = PerformanceMetric.objects.count()
        active_subscriptions = WebPushSubscription.objects.filter(enabled=True).count()
        recent_errors = ErrorLog.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()

        context = {
            'total_metrics': total_metrics,
            'active_subscriptions': active_subscriptions,
            'recent_errors': recent_errors,
            'dashboard_title': 'Performance Monitoring Dashboard'
        }

        return render(request, 'admin/performance_dashboard.html', context)


# ==========================================================================
# UTILITY FUNCTIONS FOR API ENDPOINTS
# ==========================================================================

def alert_performance_issue(metric: 'PerformanceMetric') -> None:
    """
    Alert about performance issues
    Can be extended to send notifications or create alerts
    """
    from django.conf import settings

    # Log performance issue
    logger = logging.getLogger('main.performance')
    logger.warning(
        f"Performance issue detected: {metric.metric_type}={metric.value} "
        f"from {metric.device_type} at {metric.url}"
    )

    # TODO: Implement alert system (email, Slack, etc.)
    # if settings.PERFORMANCE_ALERTS_ENABLED:
    #     send_performance_alert(metric)


def alert_critical_error(error_log: 'ErrorLog') -> None:
    """
    Alert about critical errors
    Can be extended to send immediate notifications
    """
    # Log critical error
    logger = logging.getLogger('main.security')
    logger.critical(
        f"Critical error logged: {error_log.message} "
        f"at {error_log.url} - {error_log.stack_trace[:200]}"
    )

    # TODO: Implement critical error alert system
    # if settings.CRITICAL_ERROR_ALERTS_ENABLED:


# ==========================================================================
# ADDITIONAL API ENDPOINTS
# ==========================================================================

@require_http_methods(["GET"])
@ratelimit(key='ip', rate='30/m', method='GET')
def performance_summary(request: HttpRequest) -> Response:
    """
    API endpoint for performance summary data
    """
    return performance_dashboard_data(request)


@require_http_methods(["GET"])
def tag_search_view(request: HttpRequest) -> HttpResponse:
    """
    Tag search view - shows all available tags
    """
    try:
        # Get all tags from blog posts and other content
        from apps.blog.models import Post
        from django.db.models import Count

        # Get tags from blog posts
        blog_tags = []
        posts = Post.objects.filter(status='published').prefetch_related('tags')
        for post in posts:
            blog_tags.extend(post.tags.all())

        # Count and sort tags
        tag_counts = {}
        for tag in blog_tags:
            tag_counts[tag.name] = tag_counts.get(tag.name, 0) + 1

        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)

        context = {
            'tags': sorted_tags,
            'page_title': 'Browse Tags',
            'meta_description': 'Browse all content tags'
        }

        return render(request, 'search/tag_cloud.html', context)

    except Exception as e:
        logger.error(f"Error in tag search view: {str(e)}")
        return render(request, 'search/tag_cloud.html', {'tags': []})


@require_http_methods(["GET"])
def tag_results_view(request: HttpRequest, tag_name: str) -> HttpResponse:
    """
    Show content filtered by tag
    """
    try:
        from apps.blog.models import Post

        # Get posts with this tag
        posts = Post.objects.filter(
            status='published',
            tags__name__iexact=tag_name
        ).select_related('author').prefetch_related('tags').order_by('-published_at')

        # Pagination
        paginator = Paginator(posts, 10)
        page = request.GET.get('page', 1)
        try:
            page_posts = paginator.page(page)
        except PageNotAnInteger:
            page_posts = paginator.page(1)
        except EmptyPage:
            page_posts = paginator.page(paginator.num_pages)

        context = {
            'tag_name': tag_name,
            'posts': page_posts,
            'total_results': posts.count(),
            'page_title': f'Tagged: {tag_name}',
            'meta_description': f'Content tagged with {tag_name}',
            'canonical_url': request.build_absolute_uri(),
        }

        return render(request, 'search/tag_results.html', context)

    except Exception as e:
        logger.error(f"Error in tag results view: {str(e)}")
        return render(request, 'search/tag_results.html', {'posts': []})


@require_http_methods(["GET"])
def short_url_redirect(request: HttpRequest, short_code: str) -> HttpResponse:
    """
    Handle short URL redirects
    """
    try:
        # Try to find the short URL
        from .models import ShortURL
        short_url = get_object_or_404(ShortURL, short_code=short_code, is_active=True)

        # Track click
        short_url.click_count += 1
        short_url.save()

        # Log redirect
        logger.info(f"Short URL redirect: {short_code} -> {short_url.target_url}")

        return redirect(short_url.target_url)

    except Exception as e:
        logger.error(f"Error in short URL redirect: {str(e)}")
        raise Http404("Short URL not found")


@require_http_methods(["GET"])
def error_summary(request: HttpRequest) -> JsonResponse:
    """
    API endpoint for error summary data
    """
    try:
        from datetime import datetime, timedelta

        # Get time period from query params
        period_days = int(request.GET.get('period', 7))
        start_date = timezone.now() - timedelta(days=period_days)

        # Get error statistics
        error_stats = {
            'total_errors': ErrorLog.objects.filter(
                created_at__gte=start_date
            ).count(),
            'error_levels': ErrorLog.objects.filter(
                created_at__gte=start_date
            ).values('level').annotate(count=Count('id')),
            'error_types': ErrorLog.objects.filter(
                created_at__gte=start_date
            ).values('error_type').annotate(count=Count('id')),
            'recent_errors': ErrorLog.objects.filter(
                created_at__gte=start_date
            ).order_by('-created_at')[:10],
        }

        return JsonResponse({
            'status': 'success',
            'data': error_stats,
            'period_days': period_days,
        })

    except Exception as e:
        logger.error(f"Error getting error summary: {str(e)}")
        return JsonResponse({
            'status': 'error',
            'message': 'Internal server error'
        }, status=500)


@require_http_methods(["POST"])
@csrf_exempt
@ratelimit(key='ip', rate='10/m', method='POST')
def webpush_unsubscribe(request: HttpRequest) -> JsonResponse:
    """
    Unsubscribe from push notifications
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')

        # Support nested payload format like subscribe for resilience
        if not endpoint and 'subscription' in data:
            subscription_data = data['subscription']
            endpoint = subscription_data.get('endpoint')

        if not endpoint:
            return JsonResponse({'error': 'Endpoint is required'}, status=400)

        # Find and delete the subscription
        try:
            subscription = WebPushSubscription.objects.get(endpoint=endpoint)
            subscription.delete()

            logger.info(f"Push subscription unsubscribed: {endpoint}")
            return JsonResponse({'success': True, 'message': 'Successfully unsubscribed'})

        except WebPushSubscription.DoesNotExist:
            return JsonResponse({'error': 'Subscription not found'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Unsubscribe error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["POST"])
@csrf_exempt
def test_push_notification(request: HttpRequest) -> JsonResponse:
    """
    Send a test push notification
    """
    try:
        data = json.loads(request.body)
        endpoint = data.get('endpoint')
        message = data.get('message', 'Test notification from your portfolio')

        if not endpoint:
            return JsonResponse({'error': 'Endpoint is required'}, status=400)

        # Find the subscription
        try:
            subscription = WebPushSubscription.objects.get(endpoint=endpoint)

            # Send test notification
            notification_data = {
                'title': 'Test Notification',
                'body': message,
                'icon': '/static/icons/icon-192x192.png',
                'badge': '/static/icons/badge-72x72.png',
                'url': '/'
            }

            # Here you would use the push service to send
            # For now, just return success
            logger.info(f"Test notification sent to: {endpoint}")
            return JsonResponse({
                'success': True,
                'message': 'Test notification sent successfully'
            })

        except WebPushSubscription.DoesNotExist:
            return JsonResponse({'error': 'Subscription not found'}, status=404)

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Test notification error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def get_vapid_public_key(request: HttpRequest) -> JsonResponse:
    """
    Get VAPID public key for push notification subscription
    """
    try:
        public_key = settings.WEBPUSH_SETTINGS.get('VAPID_PUBLIC_KEY', '')

        if not public_key:
            return JsonResponse({'error': 'VAPID public key not configured'}, status=500)

        return JsonResponse({'publicKey': public_key})

    except Exception as e:
        logger.error(f"Error getting VAPID public key: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


@require_http_methods(["GET"])
def manifest_json(request: HttpRequest) -> JsonResponse:
    """
    Serve the PWA manifest.json dynamically with proper JSON structure
    """
    try:
        site_name = getattr(settings, 'SITE_NAME', 'Portfolio Site')
        site_description = getattr(settings, 'SITE_DESCRIPTION', 'Professional portfolio website')

        manifest_data = {
            "name": site_name,
            "short_name": "Portfolio",
            "description": site_description,
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f172a",
            "theme_color": "#0f172a",
            "orientation": "portrait-primary",
            "icons": [
                {
                    "src": request.build_absolute_uri("/static/images/favicon-192x192.svg"),
                    "sizes": "192x192",
                    "type": "image/svg+xml",
                    "purpose": "any maskable"
                },
                {
                    "src": request.build_absolute_uri("/static/images/favicon-512x512.svg"),
                    "sizes": "512x512",
                    "type": "image/svg+xml",
                    "purpose": "any"
                },
                {
                    "src": request.build_absolute_uri("/static/images/icon-base.svg"),
                    "sizes": "any",
                    "type": "image/svg+xml",
                    "purpose": "any"
                }
            ],
            "categories": ["portfolio", "developer", "technology"],
            "lang": translation.get_language() or "tr",
            "screenshots": [
                {
                    "src": request.build_absolute_uri("/static/images/screenshot-desktop.png"),
                    "sizes": "1280x720",
                    "type": "image/png",
                    "form_factor": "wide"
                },
                {
                    "src": request.build_absolute_uri("/static/images/screenshot-mobile.png"),
                    "sizes": "375x812",
                    "type": "image/png",
                    "form_factor": "narrow"
                }
            ]
        }

        return JsonResponse(manifest_data, content_type='application/manifest+json')

    except Exception as e:
        logger.error(f"Error serving manifest.json: {e}")
        # Fallback manifest
        fallback_manifest = {
            "name": "Portfolio Site",
            "short_name": "Portfolio",
            "start_url": "/",
            "display": "standalone",
            "background_color": "#0f172a",
            "theme_color": "#0f172a"
        }
        return JsonResponse(fallback_manifest, content_type='application/manifest+json')


@require_http_methods(["GET"])
def analytics_json(request: HttpRequest) -> JsonResponse:
    """
    Enhanced analytics endpoint for frontend performance tracking
    """
    try:
        analytics_data = {
            "status": "ok",
            "message": "Analytics data received",
            "timestamp": timezone.now().isoformat(),
            "session_id": request.session.session_key or "anonymous",
            "features": {
                "performance_monitoring": settings.FEATURES.get('PERFORMANCE_MONITORING', True),
                "analytics_enabled": settings.FEATURES.get('ANALYTICS_ENABLED', True),
                "push_notifications": settings.FEATURES.get('PUSH_NOTIFICATIONS', True)
            },
            "config": {
                "sample_rate": settings.PERFORMANCE_MONITORING.get('SAMPLE_RATE', 0.1),
                "track_sql_queries": settings.PERFORMANCE_MONITORING.get('TRACK_SQL_QUERIES', False),
                "core_web_vitals_thresholds": settings.CORE_WEB_VITALS
            }
        }

        return JsonResponse(analytics_data, content_type='application/json')

    except Exception as e:
        logger.error(f"Error serving analytics.json: {e}")
        # Fallback response
        fallback_data = {
            "status": "error",
            "message": "Analytics service unavailable",
            "timestamp": timezone.now().isoformat()
        }
        return JsonResponse(fallback_data, content_type='application/json')


@require_http_methods(["POST"])
@csrf_exempt
def csp_violation_report(request: HttpRequest) -> HttpResponse:
    """
    Handle CSP violation reports
    """
    try:
        if request.content_type == 'application/csp-report':
            data = json.loads(request.body.decode('utf-8'))
        else:
            data = json.loads(request.body)

        csp_report = data.get('csp-report', data)

        # Log CSP violation
        security_logger = logging.getLogger('main.security')
        security_logger.warning(
            f"CSP Violation: {csp_report.get('violated-directive')} - "
            f"Blocked URI: {csp_report.get('blocked-uri')} - "
            f"Document URI: {csp_report.get('document-uri')}"
        )

        return HttpResponse(status=204)  # No content response

    except Exception as e:
        logger.error(f"Error processing CSP violation report: {e}")
        return HttpResponse(status=400)


@require_http_methods(["POST"])
@csrf_exempt
def network_error_report(request: HttpRequest) -> HttpResponse:
    """
    Handle Network Error Logging (NEL) reports
    """
    try:
        data = json.loads(request.body)

        # Log network error
        error_logger = logging.getLogger('main.security')
        error_logger.warning(
            f"Network Error: Type: {data.get('type')} - "
            f"URL: {data.get('url')} - "
            f"User Agent: {request.META.get('HTTP_USER_AGENT', 'Unknown')}"
        )

        return HttpResponse(status=204)  # No content response

    except Exception as e:
        logger.error(f"Error processing network error report: {e}")
        return HttpResponse(status=400)


@require_http_methods(["POST"])
@csrf_exempt
@ratelimit(key='ip', rate='50/h', method='POST')
def webpush_log(request: HttpRequest) -> JsonResponse:
    """
    Log webpush events from service worker
    """
    try:
        data = json.loads(request.body)
        event_type = data.get('event')
        timestamp = data.get('timestamp')
        event_data = data.get('data', {})

        if not event_type:
            return JsonResponse({'error': 'Event type is required'}, status=400)

        # Log to appropriate logger based on event type
        log_message = f"WebPush {event_type}: {event_data}"

        if event_type in ['error', 'failed']:
            logger.error(log_message)
        else:
            logger.info(log_message)

        # Optionally store in database if NotificationLog model exists
        # This could be extended to create NotificationLog entries

        return JsonResponse({'success': True, 'message': 'Event logged successfully'})

    except json.JSONDecodeError:
        return JsonResponse({'error': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Webpush log error: {e}")
        return JsonResponse({'error': 'Internal server error'}, status=500)


# ==========================================================================
# DASHBOARD VIEWS
# ==========================================================================

@require_http_methods(["GET"])
def monitoring_dashboard(request: HttpRequest) -> HttpResponse:
    """
    Main monitoring dashboard view
    """
    try:
        # Get basic statistics for dashboard
        context = {
            'avg_response_time': 150.5,  # Mock data - replace with real metrics
            'total_requests': 12450,
            'error_rate': 2.1,
            'core_web_vitals': {
                'lcp': 1.2,
                'fid': 45,
                'cls': 0.05,
                'inp': 120,
                'good_count': 85,
                'needs_improvement_count': 12,
                'poor_count': 3
            },
            'push_stats': {
                'total_subscriptions': 342,
                'notifications_sent_today': 127,
                'success_rate': 94.2
            },
            'recent_errors': [],  # Could populate from ErrorLog model
            'performance_trend': {
                'dates': ['2024-01-01', '2024-01-02', '2024-01-03'],
                'lcp_values': [1.2, 1.3, 1.1],
                'fid_values': [45, 52, 38]
            }
        }

        return render(request, 'dashboard/monitoring_dashboard.html', context)

    except Exception as e:
        logger.error(f"Monitoring dashboard error: {e}")
        return render(request, '500.html', status=500)


@require_http_methods(["GET"])
def performance_analytics_view(request: HttpRequest) -> HttpResponse:
    """
    Performance analytics dashboard
    """
    try:
        context = {
            'title': 'Performance Analytics',
            'metrics_data': {
                'lcp': {'avg': 1.2, 'p95': 2.1, 'trend': 'improving'},
                'fid': {'avg': 45, 'p95': 125, 'trend': 'stable'},
                'cls': {'avg': 0.05, 'p95': 0.12, 'trend': 'improving'}
            }
        }
        return render(request, 'dashboard/performance_analytics.html', context)
    except Exception as e:
        logger.error(f"Performance analytics error: {e}")
        return render(request, '500.html', status=500)


@require_http_methods(["GET"])
def error_logs_view(request: HttpRequest) -> HttpResponse:
    """
    Error logs dashboard
    """
    try:
        context = {
            'title': 'Error Logs',
            'recent_errors': [],  # Populate from ErrorLog model if exists
            'error_stats': {
                'total_today': 12,
                'critical_count': 2,
                'warning_count': 5,
                'info_count': 5
            }
        }
        return render(request, 'dashboard/error_logs.html', context)
    except Exception as e:
        logger.error(f"Error logs view error: {e}")
        return render(request, '500.html', status=500)


@require_http_methods(["GET"])
def notification_logs_view(request: HttpRequest) -> HttpResponse:
    """
    Notification logs dashboard
    """
    try:
        context = {
            'title': 'Notification Logs',
            'notification_stats': {
                'total_sent': 127,
                'delivered': 119,
                'failed': 8,
                'success_rate': 93.7
            }
        }
        return render(request, 'dashboard/notification_logs.html', context)
    except Exception as e:
        logger.error(f"Notification logs view error: {e}")
        return render(request, '500.html', status=500)


# ==========================================================================
# API LIST VIEWS
# ==========================================================================

class PersonalInfoListAPIView(ListAPIView):
    """List API view for PersonalInfo objects"""
    queryset = PersonalInfo.objects.filter(is_visible=True).order_by('order', 'key')
    serializer_class = PersonalInfoSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['key', 'value']
    ordering_fields = ['order', 'key']
    ordering = ['order', 'key']


class SocialLinkListAPIView(ListAPIView):
    """List API view for SocialLink objects"""
    queryset = SocialLink.objects.filter(is_visible=True).order_by('order', 'platform')
    serializer_class = SocialLinkSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['platform', 'description']
    ordering_fields = ['order', 'platform']
    ordering = ['order', 'platform']


class AIToolListAPIView(ListAPIView):
    """List API view for AITool objects"""
    queryset = AITool.objects.filter(is_visible=True).order_by('category', 'order', 'name')
    serializer_class = AIToolSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['order', 'name', 'rating']
    ordering = ['category', 'order', 'name']
    filterset_fields = ['category', 'is_featured', 'is_free']


class CybersecurityResourceListAPIView(ListAPIView):
    """List API view for CybersecurityResource objects"""
    queryset = CybersecurityResource.objects.filter(is_visible=True).order_by('-is_urgent', '-severity_level', 'type', 'order')
    serializer_class = CybersecurityResourceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['title', 'description', 'content', 'tags']
    ordering_fields = ['order', 'title', 'severity_level']
    ordering = ['-is_urgent', '-severity_level', 'type', 'order']
    filterset_fields = ['type', 'difficulty', 'severity_level', 'is_urgent', 'is_featured']


class UsefulResourceListAPIView(ListAPIView):
    """List API view for UsefulResource objects"""
    queryset = UsefulResource.objects.filter(is_visible=True).order_by('category', 'order', 'name')
    serializer_class = UsefulResourceSerializer
    permission_classes = [AllowAny]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter, DjangoFilterBackend]
    search_fields = ['name', 'description', 'tags']
    ordering_fields = ['order', 'name', 'rating']
    ordering = ['category', 'order', 'name']
    filterset_fields = ['category', 'type', 'is_featured', 'is_free']


@require_http_methods(["GET"])
def ui_kit_view(request: HttpRequest) -> HttpResponse:
    """
    Design System UI Kit page for living documentation
    Displays all design system components, colors, typography, and patterns.
    Includes fixture-based sample data for all portfolio components.

    Context Variables:
        - sample_featured_project: Featured project fixture for showcase
        - sample_compact_projects: List of compact project fixtures
        - sample_grid_projects: Projects for responsive grid display
        - sample_stats: Statistics fixtures
        - design_tokens_summary: Design tokens metadata reference
    """
    try:
        # Get all fixtures from fixtures provider
        fixtures = get_ui_kit_fixtures()

        context = {
            'title': _('Design System UI Kit'),
            'meta_description': _('Living documentation of our design system components, colors, typography, and patterns.'),
            'meta_keywords': _('design system, UI kit, components, colors, typography, CSS, Tailwind'),
            'breadcrumbs': [
                {'name': _('Home'), 'url': '/'},
                {'name': _('UI Kit'), 'url': None}
            ],
        }
        # Merge fixtures into context
        context.update(fixtures)

        return render(request, 'pages/portfolio/ui-kit.html', context)
    except Exception as e:
        logger.error(f"UI Kit view error: {e}")
        return render(request, '500.html', status=500)


@require_http_methods(["GET"])
def offline_view(request: HttpRequest) -> HttpResponse:
    """
    Offline page for PWA when user has no internet connection
    This page is cached by the service worker and served when offline
    """
    try:
        context = {
            'title': _('Offline'),
            'meta_description': _('You are currently offline. Some features may be limited.'),
            'page_id': 'offline',
        }
        return render(request, 'offline.html', context)
    except Exception as e:
        logger.error(f"Offline view error: {e}")
        # Return a very basic offline page as fallback
        basic_offline_html = """
        <!DOCTYPE html>
        <html>
        <head>
            <title>Offline</title>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
        </head>
        <body>
            <h1>You're Offline</h1>
            <p>No internet connection detected.</p>
            <button onclick="window.location.reload()">Try Again</button>
        </body>
        </html>
        """
        return HttpResponse(basic_offline_html, content_type='text/html')



