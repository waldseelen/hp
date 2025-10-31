"""
Search API Views for MeiliSearch Integration

Provides RESTful API endpoints for site-wide search with:
- Query-based search with typo tolerance
- Category and type filtering
- Pagination and result limiting
- Search suggestions and autocomplete
- Performance metrics logging
"""

import time
import logging
from typing import Dict, List, Any, Optional
from django.http import JsonResponse
from django.views.decorators.http import require_GET
from django.views.decorators.cache import cache_page
from django.core.cache import cache
from django.conf import settings
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.throttling import AnonRateThrottle, UserRateThrottle
from rest_framework.response import Response
from rest_framework import status

from apps.main.search_index import search_index_manager

logger = logging.getLogger(__name__)


class SearchRateThrottle(AnonRateThrottle):
    """Custom rate throttle for search API (100 requests per minute)"""
    rate = '100/min'


@api_view(['GET'])
@throttle_classes([SearchRateThrottle])
def search_api(request):
    """
    Site-wide search API endpoint.

    Query Parameters:
        q (str): Search query (required, min 2 characters)
        category (str): Filter by search category (BlogPost, AITool, etc.)
        type (str): Filter by content type (optional)
        is_visible (bool): Filter by visibility (default: true)
        page (int): Page number (default: 1)
        per_page (int): Results per page (default: 20, max: 100)
        sort (str): Sort field (relevance, date, rating)
        order (str): Sort order (asc, desc)

    Returns:
        JSON response with search results, metadata, and performance metrics

    Example:
        GET /api/search/?q=django&category=BlogPost&page=1&per_page=20

    Response:
        {
            "success": true,
            "query": "django",
            "results": [...],
            "facets": {...},
            "pagination": {...},
            "performance": {...}
        }
    """
    start_time = time.time()

    # Extract query parameters
    query = request.GET.get('q', '').strip()
    category = request.GET.get('category', None)
    content_type = request.GET.get('type', None)
    is_visible = request.GET.get('is_visible', 'true').lower() == 'true'
    page = max(1, int(request.GET.get('page', 1)))
    per_page = min(100, max(1, int(request.GET.get('per_page', 20))))
    sort_field = request.GET.get('sort', 'relevance')
    sort_order = request.GET.get('order', 'desc')

    # Validate query
    if not query:
        return Response({
            'success': False,
            'error': 'Query parameter "q" is required',
            'message': 'Please provide a search query (min 2 characters)',
        }, status=status.HTTP_400_BAD_REQUEST)

    if len(query) < 2:
        return Response({
            'success': False,
            'error': 'Query too short',
            'message': 'Search query must be at least 2 characters',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Build MeiliSearch query
        search_params = {
            'q': query,
            'limit': per_page,
            'offset': (page - 1) * per_page,
            'attributesToHighlight': ['title', 'name', 'excerpt', 'description'],
            'highlightPreTag': '<mark>',
            'highlightPostTag': '</mark>',
        }

        # Build filter string
        filters = []

        # Visibility filter (always applied for public search)
        if is_visible:
            filters.append('metadata.is_visible = true')

        # Category filter
        if category:
            filters.append(f'model_type = "{category}"')

        # Type filter
        if content_type:
            filters.append(f'metadata.type = "{content_type}"')

        # Apply filters
        if filters:
            search_params['filter'] = ' AND '.join(filters)

        # Sorting
        if sort_field != 'relevance':
            sort_map = {
                'date': 'metadata.published_at:desc',
                'rating': 'metadata.rating:desc',
                'views': 'metadata.view_count:desc',
                'title': 'title:asc',
            }

            if sort_field in sort_map:
                search_params['sort'] = [sort_map[sort_field]]

        # Facets (for category counts)
        search_params['facets'] = ['model_type', 'search_category', 'metadata.category']

        # Execute search with monitoring
        from apps.main.monitoring import search_monitor
        user_id = request.user.id if request.user.is_authenticated else None

        search_start = time.time()
        with search_monitor.track_query(query, user_id):
            search_results = search_index_manager.index.search(**search_params)
        search_duration = time.time() - search_start

        # Extract results
        hits = search_results.get('hits', [])
        estimated_total = search_results.get('estimatedTotalHits', 0)
        processing_time_ms = search_results.get('processingTimeMs', 0)

        # Format results for response
        formatted_results = []
        for hit in hits:
            formatted_result = {
                'id': hit.get('model_id'),
                'model_type': hit.get('model_type'),
                'category': hit.get('search_category'),
                'icon': hit.get('search_icon', '📄'),
                'title': hit.get('title') or hit.get('name'),
                'excerpt': hit.get('excerpt') or hit.get('description', '')[:200],
                'url': hit.get('url'),
                'tags': hit.get('tags', [])[:5],  # Limit to 5 tags
                'metadata': _extract_display_metadata(hit.get('metadata', {})),
                'highlights': hit.get('_formatted', {}),  # Highlighted text
            }
            formatted_results.append(formatted_result)

        # Extract facets (category counts)
        facet_distribution = search_results.get('facetDistribution', {})

        # Build pagination info
        total_pages = (estimated_total + per_page - 1) // per_page
        pagination = {
            'page': page,
            'per_page': per_page,
            'total_results': estimated_total,
            'total_pages': total_pages,
            'has_next': page < total_pages,
            'has_prev': page > 1,
            'next_page': page + 1 if page < total_pages else None,
            'prev_page': page - 1 if page > 1 else None,
        }

        # Performance metrics
        total_duration = time.time() - start_time
        performance = {
            'total_ms': round(total_duration * 1000, 2),
            'search_ms': round(search_duration * 1000, 2),
            'meili_processing_ms': processing_time_ms,
            'overhead_ms': round((total_duration - search_duration) * 1000, 2),
        }

        # Log search query for analytics
        logger.info(
            f"Search: query='{query}' category={category} results={len(hits)} "
            f"total={estimated_total} duration={total_duration*1000:.2f}ms"
        )

        # Build response
        response_data = {
            'success': True,
            'query': query,
            'filters': {
                'category': category,
                'type': content_type,
                'is_visible': is_visible,
            },
            'results': formatted_results,
            'facets': facet_distribution,
            'pagination': pagination,
            'performance': performance,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Search API error: {e}", exc_info=True)

        return Response({
            'success': False,
            'error': 'Search failed',
            'message': str(e),
            'query': query,
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@throttle_classes([SearchRateThrottle])
def search_suggest(request):
    """
    Search autocomplete/suggestions API.

    Query Parameters:
        q (str): Partial search query (min 2 characters)
        limit (int): Max suggestions (default: 5, max: 10)

    Returns:
        JSON array of search suggestions

    Example:
        GET /api/search/suggest/?q=dja&limit=5

    Response:
        {
            "success": true,
            "query": "dja",
            "suggestions": [
                {"text": "django", "count": 42},
                {"text": "django rest framework", "count": 18},
                ...
            ]
        }
    """
    query = request.GET.get('q', '').strip()
    limit = min(10, max(1, int(request.GET.get('limit', 5))))

    if not query or len(query) < 2:
        return Response({
            'success': False,
            'error': 'Query too short',
        }, status=status.HTTP_400_BAD_REQUEST)

    try:
        # Search with prefix matching and monitoring
        from apps.main.monitoring import search_monitor
        user_id = request.user.id if request.user.is_authenticated else None

        with search_monitor.track_query(f"suggest:{query}", user_id):
            search_results = search_index_manager.index.search(
                q=query,
                limit=limit,
                attributesToSearchOn=['title', 'name', 'tags'],
            )

        # Extract unique suggestions from results
        suggestions = []
        seen = set()

        for hit in search_results.get('hits', []):
            title = hit.get('title') or hit.get('name')
            if title and title.lower() not in seen:
                suggestions.append({
                    'text': title,
                    'category': hit.get('search_category'),
                    'url': hit.get('url'),
                })
                seen.add(title.lower())

        return Response({
            'success': True,
            'query': query,
            'suggestions': suggestions[:limit],
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Search suggest error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
def search_stats(request):
    """
    Get search index statistics.

    Returns:
        JSON with index stats (document count, indexing status, etc.)

    Example:
        GET /api/search/stats/

    Response:
        {
            "success": true,
            "stats": {
                "document_count": 1234,
                "is_indexing": false,
                "models": {...}
            }
        }
    """
    try:
        stats = search_index_manager.get_index_stats()

        # Get per-model counts
        field_dist = stats.get('field_distribution', {})
        model_counts = {}

        if 'model_type' in field_dist:
            for model_name in search_index_manager.model_registry.keys():
                config = search_index_manager.get_model_config(model_name)
                model_class = config['model']
                db_count = model_class.objects.count()

                model_counts[model_name] = {
                    'db_count': db_count,
                    'indexed_count': field_dist.get('model_type', {}).get(model_name, 0),
                    'in_sync': True,  # TODO: Check if counts match
                }

        return Response({
            'success': True,
            'stats': {
                'total_documents': stats.get('number_of_documents', 0),
                'is_indexing': stats.get('is_indexing', False),
                'models': model_counts,
                'index_name': search_index_manager.index_name,
            }
        }, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Search stats error: {e}", exc_info=True)
        return Response({
            'success': False,
            'error': str(e),
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


def _extract_display_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format metadata for display.

    Args:
        metadata: Raw metadata dict from search document

    Returns:
        Formatted metadata dict with only display-relevant fields
    """
    display_meta = {}

    # Date fields (convert timestamps to ISO strings)
    if 'published_at' in metadata and metadata['published_at']:
        from datetime import datetime
        try:
            dt = datetime.fromtimestamp(metadata['published_at'])
            display_meta['published_date'] = dt.strftime('%Y-%m-%d')
        except:
            pass

    # Author info
    if 'author' in metadata:
        display_meta['author'] = metadata.get('author_display', metadata['author'])

    # Category
    if 'category_display' in metadata:
        display_meta['category'] = metadata['category_display']

    # Rating/popularity
    if 'rating' in metadata and metadata['rating']:
        display_meta['rating'] = metadata['rating']

    if 'view_count' in metadata and metadata['view_count']:
        display_meta['views'] = metadata['view_count']

    # Reading time (for blog posts)
    if 'reading_time' in metadata and metadata['reading_time']:
        display_meta['reading_time'] = f"{metadata['reading_time']} min"

    # Status flags
    if 'is_featured' in metadata and metadata['is_featured']:
        display_meta['featured'] = True

    if 'is_free' in metadata:
        display_meta['free'] = metadata['is_free']

    # Difficulty/severity
    if 'difficulty' in metadata:
        display_meta['difficulty'] = metadata['difficulty']

    if 'severity_level' in metadata:
        severity_map = {1: 'Low', 2: 'Medium', 3: 'High', 4: 'Critical'}
        display_meta['severity'] = severity_map.get(metadata['severity_level'], 'Unknown')

    return display_meta


# Search results page view
def search_results_view(request):
    """
    Render search results page.

    Query Parameters:
        q (str): Search query
        category (str): Filter by category (optional)
        page (int): Page number (optional)
    """
    from django.shortcuts import render

    query = request.GET.get('q', '')
    category = request.GET.get('category', None)
    page = request.GET.get('page', 1)

    context = {
        'query': query,
        'category': category,
        'page': page,
    }

    return render(request, 'main/search_results.html', context)


# Legacy view (redirect to new API)
@require_GET
def search_view(request):
    """
    Legacy search view (redirects to search results page).
    Kept for backwards compatibility.
    """
    from django.shortcuts import redirect
    query = request.GET.get('q', '')

    if query:
        return redirect(f'/search/results/?q={query}')

    return JsonResponse({
        'error': 'No search query provided',
        'usage': '/search/results/?q=your+query'
    }, status=400)
