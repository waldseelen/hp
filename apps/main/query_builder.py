"""
QueryBuilder Pattern for MeiliSearch Query Construction

Provides a clean, composable way to build complex MeiliSearch queries with:
- Filter building
- Sort parameter construction
- Highlight configuration
- Facet management
- Parameter validation

Example:
    builder = QueryBuilder("django")
    builder.filter_by_model("BlogPost")
    builder.filter_by_visibility(True)
    builder.sort_by("date", "desc")
    builder.add_highlights(["title", "content"])
    params = builder.build()

    results = search_index_manager.index.search(**params)
"""

from typing import Any, Dict, List, Optional, Tuple


class QueryBuilder:
    """
    Builder pattern for constructing MeiliSearch query parameters.

    Complexity target: C ≤ 5 per method, overall orchestration ≤ 7
    """

    def __init__(self, query: str):
        """
        Initialize QueryBuilder with search query.

        Args:
            query: Search query string
        """
        self.query = query
        self._filters: List[str] = []
        self._sort: List[str] = []
        self._highlight_fields: List[str] = []
        self._facets: List[str] = []
        self._page = 1
        self._per_page = 20
        self._sort_map = {
            "date": "metadata.published_at",
            "rating": "metadata.rating",
            "views": "metadata.view_count",
            "title": "title",
            "relevance": None,  # Default sort
        }

    def filter_by_model(self, model_name: str) -> "QueryBuilder":
        """
        Add model type filter.

        Args:
            model_name: Model class name (e.g., 'BlogPost')

        Returns:
            Self for chaining
        """
        self._add_filter(f'model_type = "{model_name}"')
        return self

    def filter_by_models(self, model_names: List[str]) -> "QueryBuilder":
        """
        Add multiple model type filters (OR logic).

        Args:
            model_names: List of model class names

        Returns:
            Self for chaining
        """
        if model_names:
            models_filter = " OR ".join(f'model_type = "{m}"' for m in model_names)
            self._add_filter(f"({models_filter})")
        return self

    def filter_by_visibility(self, is_visible: bool = True) -> "QueryBuilder":
        """
        Add visibility filter.

        Args:
            is_visible: Whether to show only visible items

        Returns:
            Self for chaining
        """
        value = "true" if is_visible else "false"
        self._add_filter(f"metadata.is_visible = {value}")
        return self

    def filter_by_category(self, category: str) -> "QueryBuilder":
        """
        Add search category filter.

        Args:
            category: Category name

        Returns:
            Self for chaining
        """
        self._add_filter(f'search_category = "{category}"')
        return self

    def filter_by_content_type(self, content_type: str) -> "QueryBuilder":
        """
        Add content type filter.

        Args:
            content_type: Content type (e.g., 'tutorial', 'article')

        Returns:
            Self for chaining
        """
        self._add_filter(f'metadata.type = "{content_type}"')
        return self

    def sort_by(self, field: str, direction: str = "asc") -> "QueryBuilder":
        """
        Add sort parameter.

        Args:
            field: Field to sort by ('date', 'rating', 'views', 'title', 'relevance')
            direction: Sort direction ('asc', 'desc')

        Returns:
            Self for chaining

        Raises:
            ValueError: If invalid field or direction
        """
        if field not in self._sort_map:
            raise ValueError(f"Invalid sort field: {field}")
        if direction not in ["asc", "desc"]:
            raise ValueError(f"Invalid sort direction: {direction}")

        if field != "relevance":
            sort_field = self._sort_map[field]
            sort_str = f"{sort_field}:{direction}"
            self._sort.append(sort_str)

        return self

    def add_highlights(self, fields: Optional[List[str]] = None) -> "QueryBuilder":
        """
        Add fields to highlight in results.

        Args:
            fields: List of field names to highlight (default: title, excerpt)

        Returns:
            Self for chaining
        """
        if fields:
            self._highlight_fields = fields
        else:
            self._highlight_fields = ["title", "excerpt", "description"]

        return self

    def add_facets(self, facets: Optional[List[str]] = None) -> "QueryBuilder":
        """
        Add facet fields for aggregation.

        Args:
            facets: List of field names for faceting

        Returns:
            Self for chaining
        """
        if facets:
            self._facets = facets
        else:
            self._facets = ["model_type", "search_category"]

        return self

    def paginate(self, page: int = 1, per_page: int = 20) -> "QueryBuilder":
        """
        Set pagination parameters.

        Args:
            page: Page number (1-indexed, default: 1)
            per_page: Results per page (default: 20, max: 100)

        Returns:
            Self for chaining

        Raises:
            ValueError: If invalid pagination parameters
        """
        if page < 1:
            raise ValueError("Page must be >= 1")
        if per_page < 1 or per_page > 100:
            raise ValueError("Per page must be between 1 and 100")

        self._page = page
        self._per_page = per_page
        return self

    def build(self) -> Dict[str, Any]:
        """
        Build final MeiliSearch query parameters.

        Returns:
            Dict of MeiliSearch parameters
        """
        params = {
            "q": self.query,
            "limit": self._per_page,
            "offset": (self._page - 1) * self._per_page,
        }

        # Add filters if present
        if self._filters:
            params["filter"] = " AND ".join(self._filters)

        # Add sort if specified
        if self._sort:
            params["sort"] = self._sort

        # Add highlights if configured
        if self._highlight_fields:
            params["attributesToHighlight"] = self._highlight_fields
            params["highlightPreTag"] = "<mark>"
            params["highlightPostTag"] = "</mark>"

        # Add facets if configured
        if self._facets:
            params["facets"] = self._facets

        return params

    def _add_filter(self, filter_expr: str) -> None:
        """
        Internal method to add filter expression.

        Args:
            filter_expr: Filter expression string
        """
        if filter_expr and filter_expr not in self._filters:
            self._filters.append(filter_expr)

    def __repr__(self) -> str:
        """String representation of builder state."""
        return (
            f"QueryBuilder(query='{self.query}', "
            f"filters={len(self._filters)}, "
            f"sort={len(self._sort)}, "
            f"page={self._page}, "
            f"per_page={self._per_page})"
        )
