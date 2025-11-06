"""
Search views for portfolio site
"""

from django.core.paginator import Paginator
from django.http import JsonResponse
from django.shortcuts import render
from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from django.views.generic import TemplateView

from apps.main.search import search_engine
from apps.main.tag_collectors import get_tag_registry


class SearchView(TemplateView):
    """Main search view"""

    template_name = "search/search.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        query = self.request.GET.get("q", "").strip()
        categories = self.request.GET.getlist("category")
        page = self.request.GET.get("page", 1)

        context.update(
            {
                "query": query,
                "selected_categories": categories,
                "search_categories": self._get_search_categories(),
                "popular_searches": search_engine.get_popular_searches(),
                "recent_content": search_engine.get_recent_content(),
            }
        )

        if query:
            # Perform search
            search_results = search_engine.search(
                query=query, categories=categories if categories else None, limit=50
            )

            # Paginate results
            paginator = Paginator(search_results["results"], 12)
            page_obj = paginator.get_page(page)

            context.update(
                {
                    "search_results": search_results,
                    "page_obj": page_obj,
                    "has_results": len(search_results["results"]) > 0,
                }
            )

            # Add search suggestions if no results
            if not search_results["results"]:
                context["suggestions"] = search_results["suggestions"]

        return context

    def _get_search_categories(self):
        """Get available search categories"""
        return [
            {"key": "blog_posts", "name": "Blog Posts", "icon": "📝"},
            {"key": "projects", "name": "Projects", "icon": "🚀"},
            {"key": "tools", "name": "Tools", "icon": "🔧"},
            {"key": "ai_tools", "name": "AI Tools", "icon": "🤖"},
            {"key": "cybersecurity", "name": "Cybersecurity", "icon": "🔒"},
            {"key": "useful_resources", "name": "Resources", "icon": "🔗"},
        ]


def search_api(request):
    """API endpoint for search (for AJAX requests)"""
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "Invalid request"}, status=400)

    query = request.GET.get("q", "").strip()
    categories = request.GET.getlist("category")
    limit = int(request.GET.get("limit", 20))

    if not query or len(query) < 2:
        return JsonResponse(
            {"results": [], "total_count": 0, "message": "Query too short"}
        )

    try:
        search_results = search_engine.search(
            query=query, categories=categories if categories else None, limit=limit
        )

        # Format results for JSON response
        formatted_results = []
        for result in search_results["results"]:
            formatted_result = {
                "id": result["id"],
                "title": result["title"],
                "description": result["description"],
                "url": result["url"],
                "category": result["category_name"],
                "category_icon": result["category_icon"],
                "relevance_score": result["relevance_score"],
                "tags": result["tags"],
                "metadata": result["metadata"],
            }
            formatted_results.append(formatted_result)

        return JsonResponse(
            {
                "results": formatted_results,
                "total_count": search_results["total_count"],
                "query": search_results["query"],
                "categories": search_results["categories"],
                "suggestions": search_results["suggestions"],
            }
        )

    except Exception as e:
        return JsonResponse(
            {"error": f"Search error: {str(e)}", "results": [], "total_count": 0},
            status=500,
        )


def search_suggestions(request):
    """API endpoint for search suggestions"""
    if not request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse({"error": "Invalid request"}, status=400)

    query = request.GET.get("q", "").strip()

    if len(query) < 2:
        # Return popular searches for empty/short queries
        suggestions = [
            {"text": term, "type": "popular"}
            for term in search_engine.get_popular_searches(8)
        ]
    else:
        # Get search suggestions based on query
        search_results = search_engine.search(query=query, limit=10)
        suggestions = search_results["suggestions"][:8]

    return JsonResponse({"query": query, "suggestions": suggestions})


@method_decorator(cache_page(60 * 15), name="dispatch")  # Cache for 15 minutes
class TagCloudView(TemplateView):
    """Tag cloud view showing popular tags"""

    template_name = "search/tag_cloud.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        # Collect tags from all searchable models
        tag_data = self._collect_all_tags()

        # Generate tag cloud data
        tag_cloud = self._generate_tag_cloud(tag_data)

        context.update(
            {
                "tag_cloud": tag_cloud,
                "total_tags": len(tag_cloud),
                "categories": self._get_tag_categories(tag_data),
            }
        )

        return context

    def _collect_all_tags(self):  # noqa: C901
        """
        Collect tags from all models.

        Refactored to use collector registry pattern.
        Complexity: C=2 (was 25)
        """
        return get_tag_registry().collect_all_tags()

    def _generate_tag_cloud(self, tag_data):
        """Generate tag cloud with size classes"""
        # Sort tags by count
        sorted_tags = sorted(
            tag_data.items(), key=lambda x: x[1]["count"], reverse=True
        )

        # Calculate size classes based on count
        if not sorted_tags:
            return []

        max_count = sorted_tags[0][1]["count"]
        min_count = min(tag[1]["count"] for _, tag in sorted_tags)

        tag_cloud = []
        for tag_key, tag_info in sorted_tags[:100]:  # Limit to top 100 tags
            # Calculate relative size (1-5)
            if max_count == min_count:
                size = 3
            else:
                size = 1 + int(
                    4 * (tag_info["count"] - min_count) / (max_count - min_count)
                )

            tag_cloud.append(
                {
                    "name": tag_info["name"],
                    "count": tag_info["count"],
                    "size": size,
                    "categories": list(tag_info["categories"]),
                    "items": tag_info["items"][:5],  # Limit to 5 example items
                }
            )

        return tag_cloud

    def _get_tag_categories(self, tag_data):
        """Get tag categories with counts"""
        categories = {}
        for tag_info in tag_data.values():
            for category in tag_info["categories"]:
                categories[category] = categories.get(category, 0) + tag_info["count"]

        return [
            {
                "name": cat,
                "count": count,
                "display_name": {
                    "blog": "Blog Posts",
                    "project": "Projects",
                    "tool": "Tools",
                    "ai": "AI Tools",
                }.get(cat, cat.title()),
            }
            for cat, count in sorted(
                categories.items(), key=lambda x: x[1], reverse=True
            )
        ]


def search_by_tag(request, tag):
    """Search by specific tag"""
    search_results = search_engine.search(query=tag, limit=50)

    # Filter results to only those that actually contain the tag
    filtered_results = []
    for result in search_results["results"]:
        if any(
            tag.lower() in result_tag.lower() for result_tag in result.get("tags", [])
        ):
            filtered_results.append(result)

    # Paginate results
    page = request.GET.get("page", 1)
    paginator = Paginator(filtered_results, 12)
    page_obj = paginator.get_page(page)

    context = {
        "tag": tag,
        "search_results": {
            "results": filtered_results,
            "total_count": len(filtered_results),
            "query": tag,
        },
        "page_obj": page_obj,
        "has_results": len(filtered_results) > 0,
    }

    return render(request, "search/tag_results.html", context)
