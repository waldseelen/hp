"""
Unit Tests for QueryBuilder Pattern

Tests covering:
- Query building with different filters
- Sort parameter construction
- Pagination handling
- Highlight configuration
- Facet management
- Method chaining
- Parameter validation
"""

import pytest

from apps.main.query_builder import QueryBuilder


class TestQueryBuilderInitialization:
    """Test QueryBuilder initialization"""

    def test_basic_initialization(self):
        """Should initialize with query string"""
        builder = QueryBuilder("django")
        assert builder.query == "django"
        assert builder.build()["q"] == "django"

    def test_repr(self):
        """Should have meaningful string representation"""
        builder = QueryBuilder("test query")
        repr_str = repr(builder)
        assert "test query" in repr_str
        assert "QueryBuilder" in repr_str


class TestQueryBuilderFiltering:
    """Test filter methods"""

    def test_filter_by_model(self):
        """Should add model type filter"""
        builder = QueryBuilder("test")
        builder.filter_by_model("BlogPost")
        params = builder.build()

        assert "filter" in params
        assert 'model_type = "BlogPost"' in params["filter"]

    def test_filter_by_multiple_models(self):
        """Should add multiple model filters with OR logic"""
        builder = QueryBuilder("test")
        builder.filter_by_models(["BlogPost", "AITool"])
        params = builder.build()

        assert "filter" in params
        assert "BlogPost" in params["filter"]
        assert "AITool" in params["filter"]
        assert "OR" in params["filter"]

    def test_filter_by_visibility(self):
        """Should add visibility filter"""
        builder = QueryBuilder("test")
        builder.filter_by_visibility(True)
        params = builder.build()

        assert "metadata.is_visible = true" in params["filter"]

    def test_filter_by_visibility_false(self):
        """Should add visibility = false filter"""
        builder = QueryBuilder("test")
        builder.filter_by_visibility(False)
        params = builder.build()

        assert "metadata.is_visible = false" in params["filter"]

    def test_filter_by_category(self):
        """Should add search category filter"""
        builder = QueryBuilder("test")
        builder.filter_by_category("Blog")
        params = builder.build()

        assert 'search_category = "Blog"' in params["filter"]

    def test_filter_by_content_type(self):
        """Should add content type filter"""
        builder = QueryBuilder("test")
        builder.filter_by_content_type("tutorial")
        params = builder.build()

        assert 'metadata.type = "tutorial"' in params["filter"]

    def test_multiple_filters_combined(self):
        """Should combine multiple filters with AND"""
        builder = QueryBuilder("test")
        builder.filter_by_model("BlogPost")
        builder.filter_by_visibility(True)
        builder.filter_by_category("Tech")
        params = builder.build()

        filter_str = params["filter"]
        assert filter_str.count("AND") >= 2


class TestQueryBuilderSorting:
    """Test sort methods"""

    def test_sort_by_date_desc(self):
        """Should add date sort in descending order"""
        builder = QueryBuilder("test")
        builder.sort_by("date", "desc")
        params = builder.build()

        assert "sort" in params
        assert "metadata.published_at:desc" in params["sort"]

    def test_sort_by_rating_asc(self):
        """Should add rating sort in ascending order"""
        builder = QueryBuilder("test")
        builder.sort_by("rating", "asc")
        params = builder.build()

        assert "metadata.rating:asc" in params["sort"]

    def test_sort_by_views(self):
        """Should add views sort"""
        builder = QueryBuilder("test")
        builder.sort_by("views", "desc")
        params = builder.build()

        assert "metadata.view_count:desc" in params["sort"]

    def test_sort_by_title(self):
        """Should add title sort"""
        builder = QueryBuilder("test")
        builder.sort_by("title", "asc")
        params = builder.build()

        assert "title:asc" in params["sort"]

    def test_sort_by_relevance_ignored(self):
        """Relevance sort should be ignored (default)"""
        builder = QueryBuilder("test")
        builder.sort_by("relevance", "asc")
        params = builder.build()

        # Relevance is default, no sort field should be added
        assert "sort" not in params or params["sort"] == []

    def test_invalid_sort_field_raises_error(self):
        """Should raise ValueError for invalid field"""
        builder = QueryBuilder("test")

        with pytest.raises(ValueError, match="Invalid sort field"):
            builder.sort_by("invalid_field", "asc")

    def test_invalid_sort_direction_raises_error(self):
        """Should raise ValueError for invalid direction"""
        builder = QueryBuilder("test")

        with pytest.raises(ValueError, match="Invalid sort direction"):
            builder.sort_by("date", "invalid")


class TestQueryBuilderHighlights:
    """Test highlight methods"""

    def test_add_highlights_default(self):
        """Should add default highlight fields"""
        builder = QueryBuilder("test")
        builder.add_highlights()
        params = builder.build()

        assert "attributesToHighlight" in params
        assert "title" in params["attributesToHighlight"]
        assert "excerpt" in params["attributesToHighlight"]
        assert "highlightPreTag" in params
        assert "<mark>" in params["highlightPreTag"]

    def test_add_highlights_custom(self):
        """Should add custom highlight fields"""
        builder = QueryBuilder("test")
        builder.add_highlights(["title", "description"])
        params = builder.build()

        assert params["attributesToHighlight"] == ["title", "description"]

    def test_highlight_tags(self):
        """Should add highlight pre and post tags"""
        builder = QueryBuilder("test")
        builder.add_highlights()
        params = builder.build()

        assert params["highlightPreTag"] == "<mark>"
        assert params["highlightPostTag"] == "</mark>"


class TestQueryBuilderFacets:
    """Test facet methods"""

    def test_add_facets_default(self):
        """Should add default facets"""
        builder = QueryBuilder("test")
        builder.add_facets()
        params = builder.build()

        assert "facets" in params
        assert "model_type" in params["facets"]
        assert "search_category" in params["facets"]

    def test_add_facets_custom(self):
        """Should add custom facets"""
        builder = QueryBuilder("test")
        builder.add_facets(["custom_facet", "another_facet"])
        params = builder.build()

        assert params["facets"] == ["custom_facet", "another_facet"]


class TestQueryBuilderPagination:
    """Test pagination methods"""

    def test_default_pagination(self):
        """Should use default pagination"""
        builder = QueryBuilder("test")
        params = builder.build()

        assert params["limit"] == 20
        assert params["offset"] == 0

    def test_custom_pagination(self):
        """Should apply custom pagination"""
        builder = QueryBuilder("test")
        builder.paginate(page=2, per_page=50)
        params = builder.build()

        assert params["limit"] == 50
        assert params["offset"] == 50  # (page-1) * per_page

    def test_pagination_page_1(self):
        """Should calculate offset correctly for page 1"""
        builder = QueryBuilder("test")
        builder.paginate(page=1, per_page=25)
        params = builder.build()

        assert params["offset"] == 0

    def test_pagination_page_3(self):
        """Should calculate offset correctly for page 3"""
        builder = QueryBuilder("test")
        builder.paginate(page=3, per_page=25)
        params = builder.build()

        assert params["offset"] == 50

    def test_invalid_page_number(self):
        """Should raise ValueError for page < 1"""
        builder = QueryBuilder("test")

        with pytest.raises(ValueError, match="Page must be >= 1"):
            builder.paginate(page=0)

    def test_invalid_per_page_zero(self):
        """Should raise ValueError for per_page < 1"""
        builder = QueryBuilder("test")

        with pytest.raises(ValueError, match="Per page must be between 1 and 100"):
            builder.paginate(page=1, per_page=0)

    def test_invalid_per_page_too_large(self):
        """Should raise ValueError for per_page > 100"""
        builder = QueryBuilder("test")

        with pytest.raises(ValueError, match="Per page must be between 1 and 100"):
            builder.paginate(page=1, per_page=101)


class TestQueryBuilderChaining:
    """Test method chaining"""

    def test_method_chaining(self):
        """Should support method chaining"""
        builder = QueryBuilder("test")
        result = (
            builder.filter_by_model("BlogPost")
            .filter_by_visibility(True)
            .sort_by("date", "desc")
            .add_highlights()
            .add_facets()
            .paginate(page=1, per_page=20)
        )

        assert result is builder
        params = builder.build()
        assert "filter" in params
        assert "sort" in params
        assert "attributesToHighlight" in params

    def test_chaining_returns_self(self):
        """Each method should return self"""
        builder = QueryBuilder("test")

        assert builder.filter_by_model("BlogPost") is builder
        assert builder.filter_by_visibility(True) is builder
        assert builder.sort_by("date", "desc") is builder
        assert builder.add_highlights() is builder
        assert builder.add_facets() is builder
        assert builder.paginate() is builder


class TestQueryBuilderCompleteExample:
    """Test complete real-world examples"""

    def test_complete_search_query(self):
        """Test building a complete search query"""
        builder = QueryBuilder("django tutorial")
        builder.filter_by_models(["BlogPost", "AITool"])
        builder.filter_by_visibility(True)
        builder.sort_by("date", "desc")
        builder.add_highlights(["title", "excerpt", "content"])
        builder.add_facets(["model_type", "search_category"])
        builder.paginate(page=1, per_page=20)

        params = builder.build()

        # Verify all components
        assert params["q"] == "django tutorial"
        assert params["limit"] == 20
        assert params["offset"] == 0
        assert "filter" in params
        assert "sort" in params
        assert "attributesToHighlight" in params
        assert "facets" in params

    def test_complex_filtering(self):
        """Test complex filtering with multiple conditions"""
        builder = QueryBuilder("security")
        builder.filter_by_category("Cybersecurity")
        builder.filter_by_content_type("resource")
        builder.filter_by_visibility(True)
        builder.paginate(page=2, per_page=10)

        params = builder.build()

        # Should have offset for page 2
        assert params["offset"] == 10

        # Should have multiple filters
        assert params["filter"].count("AND") >= 2
