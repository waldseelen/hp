"""
Enhanced Site-wide Search System for Portfolio
Provides comprehensive search functionality with advanced features like:
- Real-time search suggestions
- Faceted search and filtering
- Relevance scoring and ranking
- Search analytics and logging
- Multiple output formats (HTML, JSON, XML)
"""

import logging
import re

from django.db.models import Q
from django.utils.html import strip_tags

# Import models
from apps.blog.models import Post
from apps.tools.models import Tool

from .models import AITool, CybersecurityResource, UsefulResource

# Setup logging
logger = logging.getLogger(__name__)


class SearchEngine:
    """Site-wide search engine with relevance scoring"""

    def __init__(self):
        self.models = {
            "blog_posts": {
                "model": Post,
                "fields": ["title", "content", "excerpt", "meta_description"],
                "tag_field": "tags",
                "weight": 10,
                "filters": Q(status="published"),
                "url_name": "blog:detail",
                "url_field": "slug",
                "category": "Blog Posts",
                "icon": "📝",
            },
            "tools": {
                "model": Tool,
                "fields": ["title", "description"],
                "tag_field": "tags",
                "weight": 8,
                "filters": Q(is_visible=True),
                "url_name": "tools:tool_list",
                "url_field": None,
                "category": "Tools",
                "icon": "🔧",
            },
            "ai_tools": {
                "model": AITool,
                "fields": ["name", "description"],
                "tag_field": "tags",
                "weight": 7,
                "filters": Q(is_visible=True),
                "url_name": "main:ai",
                "url_field": None,
                "category": "AI Tools",
                "icon": "🤖",
            },
            "cybersecurity": {
                "model": CybersecurityResource,
                "fields": ["title", "description", "content"],
                "tag_field": "tags",
                "weight": 7,
                "filters": Q(is_visible=True),
                "url_name": "main:cybersecurity",
                "url_field": None,
                "category": "Cybersecurity",
                "icon": "🔒",
            },
            "useful_resources": {
                "model": UsefulResource,
                "fields": ["name", "description"],
                "tag_field": "tags",
                "weight": 6,
                "filters": Q(is_visible=True),
                "url_name": "main:useful",
                "url_field": None,
                "category": "Useful Resources",
                "icon": "🔗",
            },
        }

    def search(self, query, categories=None, limit=50):
        """
        Perform site-wide search with relevance scoring

        Args:
            query (str): Search query
            categories (list): List of categories to search in
            limit (int): Maximum number of results

        Returns:
            dict: Search results with metadata
        """
        if not query or len(query.strip()) < 2:
            return {
                "results": [],
                "total_count": 0,
                "query": query,
                "categories": {},
                "suggestions": [],
            }

        # Clean and prepare query
        clean_query = self._clean_query(query)
        keywords = self._extract_keywords(clean_query)

        all_results = []
        category_counts = {}

        # Search through each model
        models_to_search = self.models
        if categories:
            models_to_search = {k: v for k, v in self.models.items() if k in categories}

        for model_key, config in models_to_search.items():
            results = self._search_model(config, keywords, clean_query)

            # Add metadata to results
            for result in results:
                result["search_category"] = model_key
                result["category_name"] = config["category"]
                result["category_icon"] = config["icon"]
                result["model_weight"] = config["weight"]

            all_results.extend(results)
            category_counts[model_key] = len(results)

        # Sort by relevance score
        all_results.sort(key=lambda x: x["relevance_score"], reverse=True)

        # Limit results
        if limit:
            all_results = all_results[:limit]

        # Generate search suggestions
        suggestions = self._generate_suggestions(clean_query, all_results)

        return {
            "results": all_results,
            "total_count": len(all_results),
            "query": query,
            "clean_query": clean_query,
            "keywords": keywords,
            "categories": category_counts,
            "suggestions": suggestions,
        }

    def _search_model(self, config, keywords, query):  # noqa: C901
        """Search within a specific model"""
        model = config["model"]
        fields = config["fields"]
        tag_field = config["tag_field"]
        weight = config["weight"]
        filters = config["filters"]

        # Build search query
        search_q = Q()

        # Search in main fields
        for field in fields:
            for keyword in keywords:
                search_q |= Q(**{f"{field}__icontains": keyword})

        # Search in tags if tag field exists
        if tag_field:
            for keyword in keywords:
                # Handle different tag field types
                if (
                    hasattr(model.objects.first(), tag_field)
                    if model.objects.exists()
                    else False
                ):
                    field_type = model._meta.get_field(tag_field)
                    if hasattr(field_type, "base_field"):  # JSONField
                        search_q |= Q(**{f"{tag_field}__icontains": keyword})
                    else:  # CharField or TextField
                        search_q |= Q(**{f"{tag_field}__icontains": keyword})

        # Apply filters
        if filters:
            search_q &= filters

        # Execute search
        try:
            queryset = model.objects.filter(search_q).distinct()

            # Calculate relevance scores
            results = []
            for obj in queryset:
                score = self._calculate_relevance_score(
                    obj, keywords, fields, tag_field, weight
                )
                if score > 0:
                    result = self._format_search_result(obj, config, score)
                    if result:
                        results.append(result)

            return results
        except Exception as e:
            # Log error but don't break search
            print(f"Search error in {config['category']}: {e}")
            return []

    def _calculate_relevance_score(
        self, obj, keywords, fields, tag_field, base_weight
    ):  # noqa: C901
        """Calculate relevance score for a search result"""
        score = 0

        # Score for matches in different fields
        field_weights = {
            "title": 10,
            "name": 10,
            "excerpt": 5,
            "description": 5,
            "content": 3,
            "detailed_description": 3,
            "meta_description": 2,
        }

        for field in fields:
            try:
                value = getattr(obj, field, "") or ""
                if isinstance(value, str):
                    value = value.lower()

                    for keyword in keywords:
                        keyword_lower = keyword.lower()

                        # Exact match bonus
                        if keyword_lower in value:
                            weight = field_weights.get(field.split("_")[-1], 1)

                            # Title/name exact match gets high score
                            if field in ["title", "name"] and keyword_lower == value:
                                score += weight * 20
                            # Partial match in title/name
                            elif field in ["title", "name"]:
                                score += weight * 10
                            # Word boundary matches
                            elif re.search(rf"\b{re.escape(keyword_lower)}\b", value):
                                score += weight * 5
                            # Partial matches
                            else:
                                score += weight * 2
            except (AttributeError, TypeError):
                continue

        # Bonus for tag matches
        if tag_field:
            try:
                tags = getattr(obj, tag_field, [])
                if tags:
                    if isinstance(tags, str):
                        tags = [tag.strip() for tag in tags.split(",")]
                    elif isinstance(tags, list):
                        pass  # Already a list
                    else:
                        tags = []

                    for keyword in keywords:
                        for tag in tags:
                            if isinstance(tag, str) and keyword.lower() in tag.lower():
                                score += 8
            except (AttributeError, TypeError):
                pass

        # Apply base model weight
        score *= base_weight / 10

        # Boost for featured items
        if hasattr(obj, "is_featured") and obj.is_featured:
            score *= 1.5

        # Boost for recent items
        if hasattr(obj, "created_at"):
            from django.utils import timezone  # noqa: F811

            days_old = (timezone.now() - obj.created_at).days
            if days_old < 30:
                score *= 1.2
            elif days_old < 90:
                score *= 1.1

        return round(score, 2)

    def _format_search_result(self, obj, config, score):  # noqa: C901
        """Format search result for display"""
        try:
            # Get title/name
            title = getattr(obj, "title", None) or getattr(obj, "name", "Untitled")

            # Get description
            description = (
                getattr(obj, "excerpt", None)
                or getattr(obj, "description", None)
                or getattr(obj, "meta_description", "")
            )

            # Clean and truncate description
            if description:
                description = (
                    strip_tags(str(description))[:200] + "..."
                    if len(str(description)) > 200
                    else description
                )

            # Get URL
            url = None
            if config["url_name"] and config["url_field"]:
                try:
                    from django.urls import reverse  # noqa: F811

                    url_value = getattr(obj, config["url_field"])
                    url = reverse(config["url_name"], args=[url_value])
                except Exception:
                    pass
            elif config["url_name"]:
                try:
                    from django.urls import reverse  # noqa: F811

                    url = reverse(config["url_name"])
                    if hasattr(obj, "id"):
                        url += f"#{obj.id}"
                except Exception:
                    pass

            # Get additional metadata
            metadata = {}

            # Date information
            if hasattr(obj, "published_at") and obj.published_at:
                metadata["date"] = obj.published_at.strftime("%Y-%m-%d")
            elif hasattr(obj, "created_at"):
                metadata["date"] = obj.created_at.strftime("%Y-%m-%d")

            # Category/type information
            if hasattr(obj, "category") and hasattr(obj.category, "display_name"):
                metadata["category"] = obj.category.display_name
            elif hasattr(obj, "get_category_display"):
                metadata["category"] = obj.get_category_display()
            elif hasattr(obj, "get_type_display"):
                metadata["category"] = obj.get_type_display()

            # Tags
            tags = []
            tag_field = config["tag_field"]
            if tag_field:
                tag_data = getattr(obj, tag_field, [])
                if isinstance(tag_data, str):
                    tags = [tag.strip() for tag in tag_data.split(",") if tag.strip()]
                elif isinstance(tag_data, list):
                    tags = [str(tag) for tag in tag_data if tag]

            return {
                "id": getattr(obj, "id", None),
                "title": title,
                "description": description,
                "url": url,
                "relevance_score": score,
                "metadata": metadata,
                "tags": tags[:5],  # Limit to 5 tags
                "object": obj,  # Include original object for template access
            }
        except Exception as e:
            print(f"Error formatting search result: {e}")
            return None

    def _clean_query(self, query):
        """Clean and normalize search query"""
        # Remove special characters and normalize whitespace
        query = re.sub(r"[^\w\s-]", " ", query)
        query = " ".join(query.split())
        return query.strip()

    def _extract_keywords(self, query):
        """Extract keywords from search query"""
        # Split query into keywords
        keywords = []
        words = query.split()

        for word in words:
            if len(word) >= 2:  # Ignore single characters
                keywords.append(word)

        # Add the full query as a phrase
        if len(keywords) > 1:
            keywords.append(query)

        return keywords

    def _generate_suggestions(self, query, results):
        """Generate search suggestions based on results"""
        suggestions = []

        # Extract popular tags from results
        tag_counts = {}
        for result in results[:10]:  # Only consider top 10 results
            for tag in result.get("tags", []):
                tag_lower = tag.lower()
                if tag_lower not in query.lower():
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1

        # Sort tags by frequency and add as suggestions
        sorted_tags = sorted(tag_counts.items(), key=lambda x: x[1], reverse=True)
        for tag, count in sorted_tags[:5]:
            suggestions.append(
                {"text": f"{query} {tag}", "type": "tag", "count": count}
            )

        # Add category suggestions if multiple categories have results
        category_counts = {}
        for result in results:
            cat = result.get("category_name", "")
            if cat:
                category_counts[cat] = category_counts.get(cat, 0) + 1

        if len(category_counts) > 1:
            for category, count in list(category_counts.items())[:3]:
                suggestions.append(
                    {
                        "text": f"{query} in {category}",
                        "type": "category",
                        "count": count,
                    }
                )

        return suggestions

    def get_popular_searches(self, limit=10):
        """Get popular search terms (could be implemented with search logging)"""
        # This would typically come from search logs
        # For now, return some example popular terms
        return [
            "django",
            "python",
            "javascript",
            "react",
            "cybersecurity",
            "ai",
            "machine learning",
            "web development",
            "api",
            "database",
        ][:limit]

    def get_recent_content(self, limit=5):
        """Get recently added content for search suggestions"""
        recent_items = []

        # Recent blog posts
        try:
            recent_posts = Post.objects.filter(status="published").order_by(
                "-published_at"
            )[: limit // 2]
            for post in recent_posts:
                recent_items.append(
                    {
                        "title": post.title,
                        "type": "Blog Post",
                        "url": post.get_absolute_url(),
                        "icon": "📝",
                    }
                )
        except Exception:
            pass

        # Recent projects - disabled (no Project model)
        # Projects functionality will be added in a future phase

        return recent_items[:limit]


# Global search engine instance
search_engine = SearchEngine()
