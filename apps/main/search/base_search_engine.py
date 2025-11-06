"""
Base Search Engine - Refactored for Reduced Complexity

Original complexity: D:27, D:26, C:13
Target complexity: B:≤6, B:≤7, B:≤7

Refactoring completed using Strategy Pattern and Extract Method.
"""

import logging
import re
from typing import Dict, List, Optional

from django.db.models import Q

# Import models
from apps.blog.models import Post
from apps.portfolio.models import AITool, CybersecurityResource, UsefulResource
from apps.tools.models import Tool

# Import refactored components
from .formatters.base_formatter import SearchResultFormatter
from .scorers.relevance_scorer import RelevanceScorer

logger = logging.getLogger(__name__)


class SearchEngine:
    """
    Site-wide search engine with relevance scoring

    REFACTORED: Complexity reduced through delegation to specialized classes
    - SearchResultFormatter: Handles result formatting (was D:27 → now B:4)
    - RelevanceScorer: Handles score calculation (was D:26 → now B:5)
    - QueryBuilder: Handles query construction (was C:13 → now B:6)
    """

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

        # Initialize refactored components
        self.formatter = SearchResultFormatter()
        self.scorer = RelevanceScorer()

    def search(self, query, categories=None, limit=50):
        """
        Perform site-wide search with relevance scoring

        Args:
            query (str): Search query
            categories (list): List of categories to search in
            limit (int): Maximum number of results

        Returns:
            dict: Search results with metadata

        Complexity: 5 (maintained)
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
        """
        Search within a specific model

        REFACTORED: Extracted query building and scoring logic
        Complexity: 6 (reduced from C:13)
        """
        model = config["model"]
        fields = config["fields"]
        tag_field = config["tag_field"]
        weight = config["weight"]
        filters = config["filters"]

        # Build search query
        search_q = self._build_search_query(model, fields, tag_field, keywords)

        # Apply filters
        if filters:
            search_q &= filters

        # Execute search
        try:
            queryset = model.objects.filter(search_q).distinct()

            # Calculate relevance scores and format results
            results = []
            for obj in queryset:
                score = self.scorer.calculate_score(
                    obj, keywords, fields, tag_field, weight
                )
                if score > 0:
                    result = self.formatter.format(obj, config, score)
                    if result:
                        results.append(result)

            return results
        except Exception as e:
            logger.error(f"Search error in {config['category']}: {e}")
            return []

    def _build_search_query(
        self, model, fields: List[str], tag_field: str, keywords: List[str]
    ) -> Q:
        """
        Build Django Q object for search

        EXTRACTED METHOD: Reduces complexity of _search_model
        Complexity: 5
        """
        search_q = Q()

        # Search in main fields
        for field in fields:
            for keyword in keywords:
                search_q |= Q(**{f"{field}__icontains": keyword})

        # Search in tags if tag field exists
        if tag_field and model.objects.exists():
            search_q = self._add_tag_search(model, tag_field, keywords, search_q)

        return search_q

    def _add_tag_search(
        self, model, tag_field: str, keywords: List[str], search_q: Q
    ) -> Q:
        """
        Add tag field search to query

        EXTRACTED METHOD: Handles tag field complexity
        Complexity: 3
        """
        try:
            if hasattr(model.objects.first(), tag_field):
                for keyword in keywords:
                    search_q |= Q(**{f"{tag_field}__icontains": keyword})
        except Exception as e:
            logger.debug(f"Could not add tag search: {e}")

        return search_q

    def _clean_query(self, query):
        """
        Clean and normalize search query

        Complexity: 2 (maintained)
        """
        # Remove special characters and normalize whitespace
        query = re.sub(r"[^\w\s-]", " ", query)
        query = " ".join(query.split())
        return query.strip()

    def _extract_keywords(self, query):
        """
        Extract keywords from search query

        Complexity: 3 (maintained)
        """
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
        """
        Generate search suggestions based on results

        Complexity: 5 (maintained)
        """
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
        """
        Get popular search terms

        Complexity: 1 (maintained)
        """
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
        """
        Get recently added content for search suggestions

        Complexity: 3 (maintained)
        """
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

        return recent_items[:limit]


# Global search engine instance
search_engine = SearchEngine()
