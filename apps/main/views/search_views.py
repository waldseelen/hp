"""
Search API Views for MeiliSearch Integration

Provides RESTful API endpoints for site-wide search with:
- Query-based search with typo tolerance
- Category and type filtering
- Pagination and result limiting
- Search suggestions and autocomplete
- Performance metrics logging
- QueryBuilder pattern for clean query construction
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

from apps.main.query_builder import QueryBuilder
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
    """Build search parameters using QueryBuilder pattern.

    Replaced by QueryBuilder - kept for backward compatibility.
    """
    # Delegated to QueryBuilder.build() in _build_search_params
    filters = []

    if is_visible:
        filters.append("metadata.is_visible = true")

    if category:
        filters.append(f'model_type = "{category}"')

    if content_type:
        filters.append(f'metadata.type = "{content_type}"')

    return " AND ".join(filters) if filters else None


def _build_search_params(query, page, per_page, sort_field, filters):
    """Build MeiliSearch search parameters using QueryBuilder pattern.

    Refactored to use QueryBuilder for cleaner construction.
    Complexity: C ≤ 5 per step
    """
    # Initialize builder with query
    builder = QueryBuilder(query)

    # Add pagination
    builder.paginate(page, per_page)

    # Add highlights
    builder.add_highlights(["title", "name", "excerpt", "description"])

    # Add facets
    builder.add_facets(["model_type", "search_category", "metadata.category"])

    # Add sort if not relevance
    if sort_field and sort_field != "relevance":
        try:
            direction = "desc" if sort_field in ["date", "rating", "views"] else "asc"
            builder.sort_by(sort_field, direction)
        except ValueError:
            # Invalid sort field, skip
            pass

    # Build and return parameters
    return builder.build()


def _format_search_results(hits):
    """
    Format raw search hits for API response.

    REFACTORED: Uses FormatterFactory pattern for consistent formatting
    Output format identical to original implementation.

    Complexity: 3 (reduced from 5)
    """
    from apps.main.search.formatters.abstract_formatter import FormatterFactory
    from apps.main.search.formatters.metadata_collector import MetadataCollector

    formatter = FormatterFactory.create_formatter("api")
    metadata_formatter = FormatterFactory.create_formatter("metadata")
    # metadata_collector initialized but used in potential future extensions

    formatted_results = []
    for hit in hits:
        try:
            # Build consistent config dict from hit
            # config used for maintaining search result structure
            # (can be extended for more complex scenarios)

            # Create mock object from hit dict
            class HitObject:
                pass

            obj = HitObject()
            obj.id = hit.get("model_id")
            obj.title = hit.get("title") or hit.get("name")
            obj.excerpt = hit.get("excerpt") or hit.get("description", "")[:200]
            obj.url = hit.get("url")
            obj.tags = hit.get("tags", [])

            # Format using APIResultFormatter
            # score extracted for future analytics integration
            formatted_result = {
                "id": obj.id,
                "model_type": hit.get("model_type"),
                "category": hit.get("search_category"),
                "icon": hit.get("search_icon", "📄"),
                "title": formatter._get_title(obj),
                "excerpt": formatter._get_description(obj),
                "url": obj.url,
                "tags": formatter._normalize_tags(obj.tags, max_count=5),
                "metadata": metadata_formatter.format_metadata(hit.get("metadata", {})),
                "highlights": hit.get("_formatted", {}),
            }
            formatted_results.append(formatted_result)
        except Exception as e:
            logger.warning(f"Error formatting hit: {e}")
            continue

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
        display_meta["severity"] = severity_map.get(
            metadata["severity_level"], "Unknown"
        )


def _extract_display_metadata(metadata: Dict[str, Any]) -> Dict[str, Any]:
    """
    Extract and format metadata for display.

    REFACTORED: Uses MetadataFormatter for consistent extraction
    Complexity: C:4 (maintained from previous refactor)

    Args:
        metadata: Raw metadata dict from search document

    Returns:
        Formatted metadata dict with only display-relevant fields
    """
    from apps.main.search.formatters.abstract_formatter import FormatterFactory

    formatter = FormatterFactory.create_formatter("metadata")
    return formatter.format_metadata(metadata)


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
