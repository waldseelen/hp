"""
Search API Views for Advanced Search Implementation
Provides REST API endpoints for:
- Autocomplete suggestions
- Full-text search
- Search analytics
- Search filters and facets
"""

import json
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Any

from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils.decorators import method_decorator
from django.views import View
from django.core.cache import cache
from django.utils import timezone
from django.db.models import Count, Q
from django.core.paginator import Paginator
from django.conf import settings

from apps.main.fulltext_search import postgresql_search
from apps.main.search import search_engine
from apps.blog.models import Post
from apps.main.models import AITool, CybersecurityResource, UsefulResource
from apps.tools.models import Tool

logger = logging.getLogger(__name__)


class SearchAutocompleteView(View):
    """
    API endpoint for search autocomplete suggestions
    GET /api/search/autocomplete/?q=<query>
    """

    def get(self, request):
        query = request.GET.get('q', '').strip()

        if not query or len(query) < 2:
            return JsonResponse({
                'suggestions': [],
                'query': query,
                'message': 'Query too short'
            })

        try:
            # Check cache first
            cache_key = f"autocomplete_{query.lower()}"
            cached_suggestions = cache.get(cache_key)

            if cached_suggestions:
                return JsonResponse({
                    'suggestions': cached_suggestions,
                    'query': query,
                    'cached': True
                })

            suggestions = []

            # Get title-based suggestions from different models
            suggestions.extend(self._get_blog_suggestions(query))
            suggestions.extend(self._get_tool_suggestions(query))
            suggestions.extend(self._get_ai_tool_suggestions(query))

            # Get popular term suggestions
            suggestions.extend(self._get_popular_term_suggestions(query))

            # Sort by relevance and limit
            suggestions.sort(key=lambda x: x.get('score', 0), reverse=True)
            suggestions = suggestions[:10]

            # Cache for 5 minutes
            cache.set(cache_key, suggestions, 300)

            return JsonResponse({
                'suggestions': suggestions,
                'query': query,
                'cached': False
            })

        except Exception as e:
            logger.error(f"Autocomplete API error: {e}")
            return JsonResponse({
                'error': 'Search suggestions unavailable',
                'suggestions': [],
                'query': query
            }, status=500)

    def _get_blog_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get blog post title suggestions"""
        try:
            posts = Post.objects.filter(
                status='published',
                title__icontains=query
            ).values('title', 'slug')[:5]

            return [
                {
                    'text': post['title'],
                    'type': 'title',
                    'category': 'Blog Posts',
                    'url': f"/blog/{post['slug']}/",
                    'score': 0.9
                }
                for post in posts
            ]
        except Exception:
            return []

    def _get_tool_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get tool title suggestions"""
        try:
            tools = Tool.objects.filter(
                is_visible=True,
                title__icontains=query
            ).values('title', 'id')[:3]

            return [
                {
                    'text': tool['title'],
                    'type': 'tool',
                    'category': 'Tools',
                    'url': f"/tools/{tool['id']}/",
                    'score': 0.8
                }
                for tool in tools
            ]
        except Exception:
            return []

    def _get_ai_tool_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get AI tool suggestions"""
        try:
            ai_tools = AITool.objects.filter(
                is_visible=True,
                name__icontains=query
            ).values('name', 'url')[:3]

            return [
                {
                    'text': tool['name'],
                    'type': 'ai_tool',
                    'category': 'AI Tools',
                    'url': tool['url'],
                    'score': 0.7
                }
                for tool in ai_tools
            ]
        except Exception:
            return []

    def _get_popular_term_suggestions(self, query: str) -> List[Dict[str, Any]]:
        """Get popular search term suggestions"""
        popular_terms = [
            'django', 'python', 'javascript', 'react', 'vue',
            'nodejs', 'api', 'database', 'security', 'ai',
            'machine learning', 'web development', 'css', 'html',
            'cybersecurity', 'automation', 'testing', 'deployment'
        ]

        matching_terms = [
            term for term in popular_terms
            if query.lower() in term.lower() and term.lower() != query.lower()
        ][:3]

        return [
            {
                'text': term,
                'type': 'term',
                'category': 'Popular Terms',
                'score': 0.6
            }
            for term in matching_terms
        ]


class SearchAPIView(View):
    """
    API endpoint for full-text search
    GET /api/search/?q=<query>&category=<category>&page=<page>
    """

    def get(self, request):
        query = request.GET.get('q', '').strip()
        category = request.GET.get('category', '')
        page = int(request.GET.get('page', 1))
        per_page = int(request.GET.get('per_page', 20))

        if not query:
            return JsonResponse({
                'error': 'Query parameter is required',
                'results': [],
                'total': 0
            }, status=400)

        try:
            # Use PostgreSQL full-text search if available, fallback to basic search
            if self._has_postgresql():
                search_results = postgresql_search.full_text_search(
                    query=query,
                    models=[category] if category else None,
                    limit=per_page * 3,  # Get more results for pagination
                    highlight=True
                )
                results = search_results['results']
            else:
                # Fallback to basic search engine
                search_results = search_engine.search(
                    query=query,
                    categories=[category] if category else None,
                    limit=per_page * 3
                )
                results = search_results['results']

            # Paginate results
            paginator = Paginator(results, per_page)
            page_obj = paginator.get_page(page)

            # Format results for API response
            formatted_results = []
            for result in page_obj:
                formatted_result = {
                    'id': result.get('id'),
                    'title': result.get('title'),
                    'description': result.get('description'),
                    'url': result.get('url'),
                    'type': result.get('type'),
                    'category': result.get('category'),
                    'score': result.get('rank', result.get('relevance_score', 0)),
                    'date': result.get('date'),
                    'tags': result.get('tags', []),
                    'highlight': {
                        'title': result.get('title_highlight'),
                        'content': result.get('content_highlight')
                    }
                }
                formatted_results.append(formatted_result)

            # Log search for analytics
            self._log_search_analytics(query, len(results), category, request)

            return JsonResponse({
                'query': query,
                'results': formatted_results,
                'pagination': {
                    'page': page,
                    'per_page': per_page,
                    'total_pages': paginator.num_pages,
                    'total_results': paginator.count,
                    'has_next': page_obj.has_next(),
                    'has_previous': page_obj.has_previous()
                },
                'filters': self._get_available_filters(results),
                'suggestions': search_results.get('suggestions', [])
            })

        except Exception as e:
            logger.error(f"Search API error: {e}")
            return JsonResponse({
                'error': 'Search unavailable',
                'results': [],
                'total': 0
            }, status=500)

    def _has_postgresql(self) -> bool:
        """Check if PostgreSQL is available"""
        try:
            from django.db import connection
            return 'postgresql' in connection.vendor
        except Exception:
            return False

    def _get_available_filters(self, results: List[Dict]) -> Dict[str, List]:
        """Get available filters based on search results"""
        categories = {}
        date_ranges = {}
        tags = {}

        for result in results[:50]:  # Analyze first 50 results
            # Categories
            category = result.get('category', 'Other')
            categories[category] = categories.get(category, 0) + 1

            # Date ranges (for blog posts)
            date = result.get('date')
            if date:
                try:
                    if isinstance(date, str):
                        date = datetime.fromisoformat(date.replace('Z', '+00:00'))

                    now = timezone.now()
                    if date >= now - timedelta(days=7):
                        date_ranges['week'] = date_ranges.get('week', 0) + 1
                    elif date >= now - timedelta(days=30):
                        date_ranges['month'] = date_ranges.get('month', 0) + 1
                    elif date >= now - timedelta(days=365):
                        date_ranges['year'] = date_ranges.get('year', 0) + 1
                except Exception:
                    pass

            # Tags
            for tag in result.get('tags', [])[:3]:  # Limit to 3 tags per result
                tags[tag] = tags.get(tag, 0) + 1

        return {
            'categories': [
                {'name': cat, 'count': count}
                for cat, count in sorted(categories.items(), key=lambda x: x[1], reverse=True)
            ][:5],
            'date_ranges': [
                {'name': range_name, 'count': count}
                for range_name, count in date_ranges.items()
            ],
            'popular_tags': [
                {'name': tag, 'count': count}
                for tag, count in sorted(tags.items(), key=lambda x: x[1], reverse=True)
            ][:10]
        }

    def _log_search_analytics(self, query: str, result_count: int, category: str, request):
        """Log search query for analytics"""
        try:
            analytics_data = {
                'query': query,
                'result_count': result_count,
                'category': category,
                'timestamp': timezone.now().isoformat(),
                'user_agent': request.META.get('HTTP_USER_AGENT', ''),
                'ip_address': self._get_client_ip(request),
                'referer': request.META.get('HTTP_REFERER', '')
            }

            # Store in cache for analytics aggregation
            analytics_key = f"search_analytics_{timezone.now().strftime('%Y-%m-%d')}"
            daily_searches = cache.get(analytics_key, [])
            daily_searches.append(analytics_data)
            cache.set(analytics_key, daily_searches, 86400)  # 24 hours

            logger.info(f"Search: {query} -> {result_count} results")

        except Exception as e:
            logger.error(f"Error logging search analytics: {e}")

    def _get_client_ip(self, request) -> str:
        """Get client IP address"""
        x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
        if x_forwarded_for:
            return x_forwarded_for.split(',')[0]
        return request.META.get('REMOTE_ADDR', '')


class SearchFiltersView(View):
    """
    API endpoint for search filters and facets
    GET /api/search/filters/
    """

    def get(self, request):
        try:
            # Get available filters from PostgreSQL search engine
            if hasattr(postgresql_search, 'get_search_filters'):
                filters = postgresql_search.get_search_filters()
            else:
                filters = self._get_basic_filters()

            return JsonResponse({
                'filters': filters,
                'cached': True
            })

        except Exception as e:
            logger.error(f"Search filters API error: {e}")
            return JsonResponse({
                'error': 'Filters unavailable',
                'filters': {}
            }, status=500)

    def _get_basic_filters(self) -> Dict[str, Any]:
        """Get basic filters when PostgreSQL search is not available"""
        return {
            'categories': [
                {'id': 'blog', 'name': 'Blog Posts', 'icon': '📝'},
                {'id': 'tools', 'name': 'Tools', 'icon': '🔧'},
                {'id': 'ai_tools', 'name': 'AI Tools', 'icon': '🤖'},
            ],
            'date_ranges': [
                {'id': 'week', 'name': 'Past Week'},
                {'id': 'month', 'name': 'Past Month'},
                {'id': 'year', 'name': 'Past Year'},
            ],
            'popular_tags': [
                'django', 'python', 'javascript', 'ai', 'security',
                'web development', 'api', 'database', 'react', 'css'
            ]
        }


class SearchAnalyticsView(View):
    """
    API endpoint for search analytics
    GET /api/search/analytics/
    """

    def get(self, request):
        try:
            days = int(request.GET.get('days', 7))

            # Get analytics data from cache
            analytics = self._get_analytics_data(days)

            return JsonResponse({
                'analytics': analytics,
                'period': f"Last {days} days"
            })

        except Exception as e:
            logger.error(f"Search analytics API error: {e}")
            return JsonResponse({
                'error': 'Analytics unavailable',
                'analytics': {}
            }, status=500)

    def _get_analytics_data(self, days: int) -> Dict[str, Any]:
        """Get search analytics data for specified number of days"""
        all_searches = []

        # Collect search data from cache for each day
        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            analytics_key = f"search_analytics_{date}"
            daily_searches = cache.get(analytics_key, [])
            all_searches.extend(daily_searches)

        if not all_searches:
            return {
                'total_searches': 0,
                'unique_queries': 0,
                'average_results': 0,
                'popular_queries': [],
                'no_result_queries': [],
                'search_trends': {}
            }

        # Process analytics
        queries = [search['query'] for search in all_searches]
        result_counts = [search['result_count'] for search in all_searches]

        # Popular queries
        query_counts = {}
        for query in queries:
            query_counts[query] = query_counts.get(query, 0) + 1

        popular_queries = sorted(
            query_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:10]

        # No result queries
        no_result_queries = [
            search['query'] for search in all_searches
            if search['result_count'] == 0
        ]

        no_result_counts = {}
        for query in no_result_queries:
            no_result_counts[query] = no_result_counts.get(query, 0) + 1

        top_no_results = sorted(
            no_result_counts.items(),
            key=lambda x: x[1],
            reverse=True
        )[:5]

        return {
            'total_searches': len(all_searches),
            'unique_queries': len(set(queries)),
            'average_results': round(sum(result_counts) / len(result_counts)) if result_counts else 0,
            'popular_queries': [
                {'query': query, 'count': count}
                for query, count in popular_queries
            ],
            'no_result_queries': [
                {'query': query, 'count': count}
                for query, count in top_no_results
            ],
            'search_trends': self._calculate_search_trends(all_searches, days)
        }

    def _calculate_search_trends(self, searches: List[Dict], days: int) -> Dict[str, int]:
        """Calculate daily search trends"""
        trends = {}

        for i in range(days):
            date = (timezone.now() - timedelta(days=i)).strftime('%Y-%m-%d')
            daily_count = len([
                s for s in searches
                if s['timestamp'].startswith(date)
            ])
            trends[date] = daily_count

        return trends


@require_http_methods(["GET"])
def popular_searches_api(request):
    """
    API endpoint for popular search terms
    GET /api/search/popular/
    """
    try:
        # This would typically come from a SearchLog model
        popular_terms = [
            {'term': 'django', 'count': 150, 'category': 'Technology'},
            {'term': 'python', 'count': 120, 'category': 'Programming'},
            {'term': 'javascript', 'count': 100, 'category': 'Programming'},
            {'term': 'ai tools', 'count': 85, 'category': 'AI'},
            {'term': 'cybersecurity', 'count': 75, 'category': 'Security'},
            {'term': 'web development', 'count': 65, 'category': 'Development'},
            {'term': 'api', 'count': 55, 'category': 'Technology'},
            {'term': 'database', 'count': 45, 'category': 'Data'},
        ]

        return JsonResponse({
            'popular_searches': popular_terms,
            'last_updated': timezone.now().isoformat()
        })

    except Exception as e:
        logger.error(f"Popular searches API error: {e}")
        return JsonResponse({
            'error': 'Popular searches unavailable',
            'popular_searches': []
        }, status=500)