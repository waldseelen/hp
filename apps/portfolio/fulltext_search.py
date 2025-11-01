"""
PostgreSQL Full-Text Search Implementation
Advanced search capabilities using PostgreSQL's full-text search features
"""

import logging
from typing import Any, Dict, List, Optional

from django.contrib.postgres.search import (
    SearchHeadline,
    SearchQuery,
    SearchRank,
    SearchVector,
    TrigramSimilarity,
)
from django.core.cache import cache
from django.db.models import F, Q
from django.db.models.functions import Greatest
from django.utils import timezone

from apps.blog.models import Post
from apps.tools.models import Tool

from .models import AITool

logger = logging.getLogger(__name__)


class PostgreSQLSearchEngine:
    """
    Advanced PostgreSQL Full-Text Search Engine with:
    - Vector-based search with ranking
    - Trigram similarity matching
    - Search highlighting
    - Auto-complete suggestions
    - Search analytics
    """

    def __init__(self):
        self.search_config = "english"  # PostgreSQL text search configuration
        self.min_similarity = 0.3  # Minimum trigram similarity threshold

        # Search weights for different content types
        self.search_weights = {
            "title": "A",  # Highest weight
            "heading": "B",  # High weight
            "content": "C",  # Medium weight
            "metadata": "D",  # Lowest weight
        }

    def full_text_search(
        self,
        query: str,
        models: Optional[List[str]] = None,
        limit: int = 50,
        highlight: bool = True,
        use_trigrams: bool = True,
    ) -> Dict[str, Any]:
        """
        Perform full-text search across multiple models

        Args:
            query: Search query string
            models: List of model names to search (None = all models)
            limit: Maximum number of results
            highlight: Whether to include search result highlighting
            use_trigrams: Whether to use trigram similarity for fuzzy matching

        Returns:
            Dictionary with search results and metadata
        """
        if not query or len(query.strip()) < 2:
            return self._empty_result(query)

        search_query = SearchQuery(query, config=self.search_config)

        results = []
        total_count = 0

        # Search in blog posts
        if not models or "blog" in models:
            blog_results = self._search_blog_posts(
                query, search_query, highlight, use_trigrams
            )
            results.extend(blog_results)
            total_count += len(blog_results)

        # Search in tools
        if not models or "tools" in models:
            tool_results = self._search_tools(
                query, search_query, highlight, use_trigrams
            )
            results.extend(tool_results)
            total_count += len(tool_results)

        # Search in AI tools
        if not models or "ai_tools" in models:
            ai_results = self._search_ai_tools(
                query, search_query, highlight, use_trigrams
            )
            results.extend(ai_results)
            total_count += len(ai_results)

        # Sort by relevance score
        results.sort(key=lambda x: x["rank"], reverse=True)

        # Apply limit
        if limit:
            results = results[:limit]

        # Generate suggestions
        suggestions = self._generate_autocomplete_suggestions(query)

        # Log search for analytics
        self._log_search(query, total_count, models)

        return {
            "query": query,
            "results": results,
            "total_count": total_count,
            "suggestions": suggestions,
            "search_time": timezone.now(),
        }

    def _search_blog_posts(
        self,
        query: str,
        search_query: SearchQuery,
        highlight: bool = True,
        use_trigrams: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search in blog posts using full-text search"""
        try:
            # Create search vector with weighted fields
            search_vector = (
                SearchVector(
                    "title",
                    weight=self.search_weights["title"],
                    config=self.search_config,
                )
                + SearchVector(
                    "excerpt",
                    weight=self.search_weights["heading"],
                    config=self.search_config,
                )
                + SearchVector(
                    "content",
                    weight=self.search_weights["content"],
                    config=self.search_config,
                )
                + SearchVector(
                    "meta_description",
                    weight=self.search_weights["metadata"],
                    config=self.search_config,
                )
            )

            # Base queryset
            queryset = (
                Post.objects.filter(status="published")
                .annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query)
                )
                .filter(Q(search=search_query) | Q(rank__gte=0.3))
            )

            # Add trigram similarity if enabled
            if use_trigrams:
                queryset = queryset.annotate(
                    title_similarity=TrigramSimilarity("title", query),
                    content_similarity=TrigramSimilarity("content", query),
                    combined_similarity=Greatest(
                        "title_similarity", "content_similarity"
                    ),
                ).filter(
                    Q(rank__gte=0.1) | Q(combined_similarity__gte=self.min_similarity)
                )

                # Boost rank with similarity
                queryset = queryset.annotate(
                    final_rank=F("rank") + (F("combined_similarity") * 0.5)
                )
            else:
                queryset = queryset.annotate(final_rank=F("rank"))

            # Add search highlighting
            if highlight:
                queryset = queryset.annotate(
                    title_highlight=SearchHeadline(
                        "title",
                        search_query,
                        config=self.search_config,
                        start_sel="<mark>",
                        stop_sel="</mark>",
                    ),
                    content_highlight=SearchHeadline(
                        "content",
                        search_query,
                        config=self.search_config,
                        start_sel="<mark>",
                        stop_sel="</mark>",
                        max_words=50,
                        min_words=15,
                    ),
                )

            # Execute query and format results
            results = []
            for post in queryset.order_by("-final_rank")[:20]:
                result = {
                    "id": post.id,
                    "title": post.title,
                    "title_highlight": (
                        getattr(post, "title_highlight", post.title)
                        if highlight
                        else post.title
                    ),
                    "description": post.excerpt or post.meta_description or "",
                    "content_highlight": (
                        getattr(post, "content_highlight", "") if highlight else ""
                    ),
                    "url": post.get_absolute_url(),
                    "rank": float(getattr(post, "final_rank", 0)),
                    "similarity": (
                        float(getattr(post, "combined_similarity", 0))
                        if use_trigrams
                        else 0
                    ),
                    "type": "blog_post",
                    "category": "Blog Posts",
                    "icon": "📝",
                    "date": post.published_at,
                    "tags": post.tags or [],
                    "author": post.author.name if post.author else "",
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in blog post search: {e}")
            return []

    def _search_tools(
        self,
        query: str,
        search_query: SearchQuery,
        highlight: bool = True,
        use_trigrams: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search in tools"""
        try:
            search_vector = SearchVector(
                "title", weight=self.search_weights["title"], config=self.search_config
            ) + SearchVector(
                "description",
                weight=self.search_weights["content"],
                config=self.search_config,
            )

            queryset = (
                Tool.objects.filter(is_visible=True)
                .annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query)
                )
                .filter(rank__gte=0.1)
            )

            if use_trigrams:
                queryset = queryset.annotate(
                    title_similarity=TrigramSimilarity("title", query),
                    desc_similarity=TrigramSimilarity("description", query),
                    combined_similarity=Greatest("title_similarity", "desc_similarity"),
                    final_rank=F("rank") + (F("combined_similarity") * 0.5),
                ).filter(
                    Q(rank__gte=0.1) | Q(combined_similarity__gte=self.min_similarity)
                )
            else:
                queryset = queryset.annotate(final_rank=F("rank"))

            results = []
            for tool in queryset.order_by("-final_rank")[:15]:
                result = {
                    "id": tool.id,
                    "title": tool.title,
                    "description": tool.description,
                    "url": tool.url,
                    "rank": float(getattr(tool, "final_rank", 0)),
                    "similarity": (
                        float(getattr(tool, "combined_similarity", 0))
                        if use_trigrams
                        else 0
                    ),
                    "type": "tool",
                    "category": "Tools",
                    "icon": "🔧",
                    "tags": tool.tags or [],
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in tools search: {e}")
            return []

    def _search_ai_tools(
        self,
        query: str,
        search_query: SearchQuery,
        highlight: bool = True,
        use_trigrams: bool = True,
    ) -> List[Dict[str, Any]]:
        """Search in AI tools"""
        try:
            search_vector = SearchVector(
                "name", weight=self.search_weights["title"], config=self.search_config
            ) + SearchVector(
                "description",
                weight=self.search_weights["content"],
                config=self.search_config,
            )

            queryset = (
                AITool.objects.filter(is_visible=True)
                .annotate(
                    search=search_vector, rank=SearchRank(search_vector, search_query)
                )
                .filter(rank__gte=0.1)
            )

            if use_trigrams:
                queryset = queryset.annotate(
                    name_similarity=TrigramSimilarity("name", query),
                    desc_similarity=TrigramSimilarity("description", query),
                    combined_similarity=Greatest("name_similarity", "desc_similarity"),
                    final_rank=F("rank") + (F("combined_similarity") * 0.5),
                ).filter(
                    Q(rank__gte=0.1) | Q(combined_similarity__gte=self.min_similarity)
                )
            else:
                queryset = queryset.annotate(final_rank=F("rank"))

            results = []
            for tool in queryset.order_by("-final_rank")[:15]:
                result = {
                    "id": tool.id,
                    "title": tool.name,
                    "description": tool.description,
                    "url": tool.url,
                    "rank": float(getattr(tool, "final_rank", 0)),
                    "similarity": (
                        float(getattr(tool, "combined_similarity", 0))
                        if use_trigrams
                        else 0
                    ),
                    "type": "ai_tool",
                    "category": "AI Tools",
                    "icon": "🤖",
                    "tags": tool.tags or [],
                }
                results.append(result)

            return results

        except Exception as e:
            logger.error(f"Error in AI tools search: {e}")
            return []

    def _generate_autocomplete_suggestions(
        self, query: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Generate autocomplete suggestions based on query"""
        cache_key = f"search_suggestions_{query.lower()}"
        cached_suggestions = cache.get(cache_key)

        if cached_suggestions:
            return cached_suggestions

        suggestions = []

        try:
            # Get popular search terms that start with or contain the query
            # This would typically come from a search analytics table

            # For now, generate suggestions from existing content
            if len(query) >= 2:
                # Title-based suggestions from blog posts
                blog_titles = Post.objects.filter(
                    status="published", title__icontains=query
                ).values_list("title", flat=True)[:5]

                for title in blog_titles:
                    suggestions.append(
                        {
                            "text": title,
                            "type": "title",
                            "category": "Blog Posts",
                            "score": 0.9,
                        }
                    )

                # Tag-based suggestions
                # This would work better with a proper tags table
                common_tech_terms = [
                    "django",
                    "python",
                    "javascript",
                    "react",
                    "vue",
                    "nodejs",
                    "api",
                    "database",
                    "security",
                    "ai",
                    "machine learning",
                    "web development",
                    "css",
                    "html",
                ]

                matching_terms = [
                    term
                    for term in common_tech_terms
                    if query.lower() in term.lower() and term.lower() != query.lower()
                ][:3]

                for term in matching_terms:
                    suggestions.append(
                        {
                            "text": term,
                            "type": "term",
                            "category": "Popular",
                            "score": 0.7,
                        }
                    )

        except Exception as e:
            logger.error(f"Error generating suggestions: {e}")

        # Sort by score and limit
        suggestions.sort(key=lambda x: x["score"], reverse=True)
        suggestions = suggestions[:limit]

        # Cache for 5 minutes
        cache.set(cache_key, suggestions, 300)

        return suggestions

    def get_search_filters(self) -> Dict[str, List[str]]:
        """Get available search filters and facets"""
        cache_key = "search_filters"
        cached_filters = cache.get(cache_key)

        if cached_filters:
            return cached_filters

        filters = {
            "categories": [
                {"id": "blog", "name": "Blog Posts", "icon": "📝"},
                {"id": "tools", "name": "Tools", "icon": "🔧"},
                {"id": "ai_tools", "name": "AI Tools", "icon": "🤖"},
            ],
            "date_ranges": [
                {"id": "week", "name": "Past Week"},
                {"id": "month", "name": "Past Month"},
                {"id": "year", "name": "Past Year"},
            ],
            "popular_tags": self._get_popular_tags(),
        }

        # Cache for 1 hour
        cache.set(cache_key, filters, 3600)

        return filters

    def _get_popular_tags(self) -> List[str]:
        """Get most popular tags across all content"""
        try:
            # This is a simplified version - in production you'd aggregate tags properly
            popular_tags = [
                "django",
                "python",
                "javascript",
                "ai",
                "security",
                "web development",
                "api",
                "database",
                "react",
                "css",
            ]
            return popular_tags[:10]
        except Exception:
            return []

    def _log_search(self, query: str, result_count: int, models: Optional[List[str]]):
        """Log search query for analytics"""
        try:
            # TODO: Store search_data in SearchLog model for analytics
            # search_data = {
            #     "query": query,
            #     "result_count": result_count,
            #     "models_searched": models or "all",
            #     "timestamp": timezone.now().isoformat(),
            # }

            # For now, just log to console
            logger.info(f"Search: {query} -> {result_count} results")

            # TODO: Send to analytics endpoint
            # requests.post('/api/search/log/', json=search_data)

        except Exception as e:
            logger.error(f"Error logging search: {e}")

    def _empty_result(self, query: str) -> Dict[str, Any]:
        """Return empty search result structure"""
        return {
            "query": query,
            "results": [],
            "total_count": 0,
            "suggestions": [],
            "search_time": timezone.now(),
        }

    def get_search_analytics(self, days: int = 30) -> Dict[str, Any]:
        """Get search analytics for the past N days"""
        # This would query a SearchLog model in production
        return {
            "total_searches": 0,
            "unique_queries": 0,
            "average_results": 0,
            "popular_queries": [],
            "no_result_queries": [],
            "search_trends": {},
        }


# Global PostgreSQL search engine instance
postgresql_search = PostgreSQLSearchEngine()
