"""
Search API Views for MeiliSearch Integration

Provides RESTful API endpoints for site-wide search with:
- Query-based search with typo tolerance
- Category and type filtering
- Pagination and result limiting
- Search suggestions and autocomplete
- Performance metrics logging
"""

import logging
import time
from typing import Any, Dict

from django.http import JsonResponse
from django.views.decorators.http import require_GET

from rest_framework import status
from rest_framework.decorators import api_view, throttle_classes
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle

from apps.main.search_index import search_index_manager

logger = logging.getLogger(__name__)


class SearchRateThrottle(AnonRateThrottle):
    """Custom rate throttle for search API (100 requests per minute)"""

    rate = "100/min"


def _extract_search_params(request):
    """Extract and validate search parameters from request."""
    query = request.GET.get("q", "").strip()

    if not query:
        return None, Response(
            {
                "success": False,
                "error": 'Query parameter "q" is required',
                "message": "Please provide a search query (min 2 characters)",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    if len(query) < 2:
        return None, Response(
            {
                "success": False,
                "error": "Query too short",
                "message": "Search query must be at least 2 characters",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    params = {
        "query": query,
        "category": request.GET.get("category", None),
        "content_type": request.GET.get("type", None),
        "is_visible": request.GET.get("is_visible", "true").lower() == "true",
        "page": max(1, int(request.GET.get("page", 1))),
        "per_page": min(100, max(1, int(request.GET.get("per_page", 20)))),
        "sort_field": request.GET.get("sort", "relevance"),
    }

    return params, None


def _build_search_filters(category, content_type, is_visible):
    """Build MeiliSearch filter string."""
    filters = []

    if is_visible:
        filters.append("metadata.is_visible = true")

    if category:
        filters.append(f'model_type = "{category}"')

    if content_type:
        filters.append(f'metadata.type = "{content_type}"')

    return " AND ".join(filters) if filters else None


def _build_search_params(query, page, per_page, sort_field, filters):
    """Build complete MeiliSearch search parameters."""
    search_params = {
        "q": query,
        "limit": per_page,
        "offset": (page - 1) * per_page,
        "attributesToHighlight": ["title", "name", "excerpt", "description"],
        "highlightPreTag": "<mark>",
        "highlightPostTag": "</mark>",
        "facets": ["model_type", "search_category", "metadata.category"],
    }

    if filters:
        search_params["filter"] = filters

    if sort_field != "relevance":
        sort_map = {
            "date": "metadata.published_at:desc",
            "rating": "metadata.rating:desc",
            "views": "metadata.view_count:desc",
            "title": "title:asc",
        }
        if sort_field in sort_map:
            search_params["sort"] = [sort_map[sort_field]]

    return search_params


def _format_search_results(hits):
    """Format raw search hits for API response."""
    formatted_results = []
    for hit in hits:
        formatted_result = {
            "id": hit.get("model_id"),
            "model_type": hit.get("model_type"),
            "category": hit.get("search_category"),
            "icon": hit.get("search_icon", "📄"),
            "title": hit.get("title") or hit.get("name"),
            "excerpt": hit.get("excerpt") or hit.get("description", "")[:200],
            "url": hit.get("url"),
            "tags": hit.get("tags", [])[:5],
            "metadata": _extract_display_metadata(hit.get("metadata", {})),
            "highlights": hit.get("_formatted", {}),
        }
        formatted_results.append(formatted_result)
    return formatted_results


@api_view(["GET"])
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

    # Extract and validate query parameters
    params, error_response = _extract_search_params(request)
    if error_response:
        return error_response

    query = params["query"]
    category = params["category"]
    content_type = params["content_type"]
    is_visible = params["is_visible"]
    page = params["page"]
    per_page = params["per_page"]
    sort_field = params["sort_field"]

    try:
        # Build search parameters
        filters = _build_search_filters(category, content_type, is_visible)
        search_params = _build_search_params(query, page, per_page, sort_field, filters)

        # Execute search with monitoring
        from apps.main.monitoring import search_monitor

        user_id = request.user.id if request.user.is_authenticated else None

        search_start = time.time()
        with search_monitor.track_query(query, user_id):
            search_results = search_index_manager.index.search(**search_params)
        search_duration = time.time() - search_start

        # Extract and format results
        hits = search_results.get("hits", [])
        estimated_total = search_results.get("estimatedTotalHits", 0)
        processing_time_ms = search_results.get("processingTimeMs", 0)

        formatted_results = _format_search_results(hits)

        # Extract facets (category counts)
        facet_distribution = search_results.get("facetDistribution", {})

        # Build pagination info
        total_pages = (estimated_total + per_page - 1) // per_page
        pagination = {
            "page": page,
            "per_page": per_page,
            "total_results": estimated_total,
            "total_pages": total_pages,
            "has_next": page < total_pages,
            "has_prev": page > 1,
            "next_page": page + 1 if page < total_pages else None,
            "prev_page": page - 1 if page > 1 else None,
        }

        # Performance metrics
        total_duration = time.time() - start_time
        performance = {
            "total_ms": round(total_duration * 1000, 2),
            "search_ms": round(search_duration * 1000, 2),
            "meili_processing_ms": processing_time_ms,
            "overhead_ms": round((total_duration - search_duration) * 1000, 2),
        }

        # Log search query for analytics
        logger.info(
            f"Search: query='{query}' category={category} results={len(hits)} "
            f"total={estimated_total} duration={total_duration * 1000:.2f}ms"
        )

        # Build response
        response_data = {
            "success": True,
            "query": query,
            "filters": {
                "category": category,
                "type": content_type,
                "is_visible": is_visible,
            },
            "results": formatted_results,
            "facets": facet_distribution,
            "pagination": pagination,
            "performance": performance,
        }

        return Response(response_data, status=status.HTTP_200_OK)

    except Exception as e:
        logger.error(f"Search API error: {e}", exc_info=True)

        return Response(
            {
                "success": False,
                "error": "Search failed",
                "message": str(e),
                "query": query,
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
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
    query = request.GET.get("q", "").strip()
    limit = min(10, max(1, int(request.GET.get("limit", 5))))

    if not query or len(query) < 2:
        return Response(
            {
                "success": False,
                "error": "Query too short",
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        # Search with prefix matching and monitoring
        from apps.main.monitoring import search_monitor

        user_id = request.user.id if request.user.is_authenticated else None

        with search_monitor.track_query(f"suggest:{query}", user_id):
            search_results = search_index_manager.index.search(
                q=query,
                limit=limit,
                attributesToSearchOn=["title", "name", "tags"],
            )

        # Extract unique suggestions from results
        suggestions = []
        seen = set()

        for hit in search_results.get("hits", []):
            title = hit.get("title") or hit.get("name")
            if title and title.lower() not in seen:
                suggestions.append(
                    {
                        "title": title,
                        "description": (
                            hit.get("excerpt") or hit.get("description", "")
                        )[:150],
                        "type": hit.get("search_category"),
                        "category": hit.get("search_category"),
                        "url": hit.get("url"),
                        "icon": hit.get("search_icon", "📄"),
                        "date": hit.get("metadata", {}).get("published_at", ""),
                    }
                )
                seen.add(title.lower())

        return Response(
            {
                "success": True,
                "query": query,
                "suggestions": suggestions[:limit],
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Search suggest error: {e}", exc_info=True)
        return Response(
            {
                "success": False,
                "error": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["GET"])
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
        field_dist = stats.get("field_distribution", {})
        model_counts = {}

        if "model_type" in field_dist:
            for model_name in search_index_manager.model_registry.keys():
                config = search_index_manager.get_model_config(model_name)
                model_class = config["model"]
                db_count = model_class.objects.count()

                model_counts[model_name] = {
                    "db_count": db_count,
                    "indexed_count": field_dist.get("model_type", {}).get(
                        model_name, 0
                    ),
                    "in_sync": True,  # TODO: Check if counts match
                }

        return Response(
            {
                "success": True,
                "stats": {
                    "total_documents": stats.get("number_of_documents", 0),
                    "is_indexing": stats.get("is_indexing", False),
                    "models": model_counts,
                    "index_name": search_index_manager.index_name,
                },
            },
            status=status.HTTP_200_OK,
        )

    except Exception as e:
        logger.error(f"Search stats error: {e}", exc_info=True)
        return Response(
            {
                "success": False,
                "error": str(e),
            },
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


def _extract_date_fields(metadata, display_meta):
    """Extract and format date fields."""
    if "published_at" in metadata and metadata["published_at"]:
        from datetime import datetime

        try:
            dt = datetime.fromtimestamp(metadata["published_at"])
            display_meta["published_date"] = dt.strftime("%Y-%m-%d")
        except (ValueError, TypeError, OSError):
            pass


def _extract_author_category(metadata, display_meta):
    """Extract author and category information."""
    if "author" in metadata:
        display_meta["author"] = metadata.get("author_display", metadata["author"])

    if "category_display" in metadata:
        display_meta["category"] = metadata["category_display"]


def _extract_metrics(metadata, display_meta):
    """Extract rating, views, and reading time."""
    if "rating" in metadata and metadata["rating"]:
        display_meta["rating"] = metadata["rating"]

    if "view_count" in metadata and metadata["view_count"]:
        display_meta["views"] = metadata["view_count"]

    if "reading_time" in metadata and metadata["reading_time"]:
        display_meta["reading_time"] = f"{metadata['reading_time']} min"


def _extract_flags_and_difficulty(metadata, display_meta):
    """Extract status flags and difficulty/severity."""
    if "is_featured" in metadata and metadata["is_featured"]:
        display_meta["featured"] = True

    if "is_free" in metadata:
        display_meta["free"] = metadata["is_free"]

    if "difficulty" in metadata:
        display_meta["difficulty"] = metadata["difficulty"]

    if "severity_level" in metadata:
        severity_map = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
        display_meta["severity"] = severity_map.get(metadata["severity_level"], "Unknown")


def _extract_display_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format metadata for display.

    Refactored to reduce complexity: C:17 → C:4
    Uses extractor functions for each metadata category.

    Args:
        metadata: Raw metadata dict from search document

    Returns:
        Formatted metadata dict with only display-relevant fields
    """
    display_meta = {}

    _extract_date_fields(metadata, display_meta)
    _extract_author_category(metadata, display_meta)
    _extract_metrics(metadata, display_meta)
    _extract_flags_and_difficulty(metadata, display_meta)

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

    query = request.GET.get("q", "")
    category = request.GET.get("category", None)
    page = request.GET.get("page", 1)

    context = {
        "query": query,
        "category": category,
        "page": page,
    }

    return render(request, "main/search_results.html", context)


# Legacy view (redirect to new API)
@require_GET
def search_view(request):
    """
    Legacy search view (redirects to search results page).
    Kept for backwards compatibility.
    """
    from django.shortcuts import redirect

    query = request.GET.get("q", "")

    if query:
        return redirect(f"/search/results/?q={query}")

    return JsonResponse(
        {"error": "No search query provided", "usage": "/search/results/?q=your+query"},
        status=400,
    )
