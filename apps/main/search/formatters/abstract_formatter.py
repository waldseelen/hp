"""
Abstract Base Formatter for Search Results

Handles common formatting operations with reduced complexity.
Provides interface for all concrete formatter implementations.

Complexity Target: ≤5
"""

import logging
import re
from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

from django.utils.html import strip_tags

logger = logging.getLogger(__name__)


class AbstractFormatter(ABC):
    """
    Abstract base class for all search result formatters.

    Provides common utility methods and defines interface for subclasses.

    Design Pattern: Strategy Pattern
    Complexity Target: ≤5 (this class)
    """

    def __init__(self):
        """Initialize formatter with default settings."""
        self.max_description_length = 200
        self.max_title_length = 255
        self.max_tags = 5

    # ============================================================================
    # ABSTRACT METHODS - MUST BE IMPLEMENTED BY SUBCLASSES
    # ============================================================================

    @abstractmethod
    def format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Format search result object for display.

        Args:
            obj: Django model instance
            config: Search configuration dict
            score: Relevance score

        Returns:
            Formatted result dict or None on error
        """
        pass

    # ============================================================================
    # COMMON UTILITY METHODS - USED BY ALL SUBCLASSES
    # ============================================================================

    def _get_title(self, obj: Any) -> str:
        """
        Extract title/name from object.

        Tries multiple common field names:
        - title (primary)
        - name (fallback)
        - Defaults to 'Untitled'

        Complexity: 1
        """
        return getattr(obj, "title", None) or getattr(obj, "name", "Untitled")

    def _get_description(self, obj: Any) -> str:
        """
        Extract and format description from object.

        Steps:
        1. Try multiple description fields
        2. Clean HTML tags
        3. Truncate if needed

        Complexity: 4
        """
        # Try multiple description fields
        description = (
            getattr(obj, "excerpt", None)
            or getattr(obj, "description", None)
            or getattr(obj, "meta_description", "")
        )

        if not description:
            return ""

        # Clean HTML tags
        description = self._clean_html(str(description))

        # Truncate if needed
        if len(description) > self.max_description_length:
            return self._truncate_text(description, self.max_description_length)

        return description

    def _clean_html(self, text: str) -> str:
        """
        Remove HTML tags from text.

        Complexity: 1
        """
        if not text:
            return ""
        return strip_tags(str(text)).strip()

    def _truncate_text(self, text: str, max_length: int = None) -> str:
        """
        Truncate text to max length and add ellipsis.

        Args:
            text: Text to truncate
            max_length: Maximum length (default: self.max_description_length)

        Returns:
            Truncated text with ellipsis

        Complexity: 2
        """
        if max_length is None:
            max_length = self.max_description_length

        if not text or len(text) <= max_length:
            return text

        return text[:max_length].rstrip() + "..."

    def _extract_field(self, obj: Any, field_name: str, default: Any = None) -> Any:
        """
        Safely extract field from object with default fallback.

        Args:
            obj: Object to extract from
            field_name: Field name to extract
            default: Default value if field missing

        Returns:
            Field value or default

        Complexity: 2
        """
        try:
            return getattr(obj, field_name, default)
        except Exception as e:
            logger.debug(f"Error extracting field {field_name}: {e}")
            return default

    def _normalize_tags(self, tags: Any, max_count: int = None) -> list:  # noqa: C901
        """
        Normalize and limit tags.

        Handles multiple formats:
        - List of tag objects with 'name' attribute
        - List of strings
        - Comma-separated string

        Args:
            tags: Tags in various formats
            max_count: Maximum number of tags (default: self.max_tags)

        Returns:
            List of tag strings (limited and deduplicated)

        Complexity: 5 -> Reduced by extracting helpers
        """
        if max_count is None:
            max_count = self.max_tags

        if not tags:
            return []

        # Parse tags into list
        tag_list = self._parse_tags_to_list(tags)

        # Deduplicate and limit
        return self._deduplicate_and_limit_tags(tag_list, max_count)

    def _parse_tags_to_list(self, tags: Any) -> list:
        """Parse tags from various formats into a list."""
        # Handle comma-separated string
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",") if tag.strip()]

        # Handle list/tuple
        if isinstance(tags, (list, tuple)):
            tag_list = []
            for tag in tags:
                # Handle tag objects with 'name' attribute
                if hasattr(tag, "name"):
                    tag_list.append(tag.name)
                # Handle string tags
                elif isinstance(tag, str):
                    tag_list.append(tag)
            return tag_list

        return []

    def _deduplicate_and_limit_tags(self, tag_list: list, max_count: int) -> list:
        """Deduplicate tags (case-insensitive) and limit count."""
        seen = set()
        unique_tags = []
        for tag in tag_list:
            tag_lower = str(tag).lower()
            if tag_lower not in seen:
                unique_tags.append(str(tag))
                seen.add(tag_lower)
                if len(unique_tags) >= max_count:
                    break

        return unique_tags

    def _build_result_dict(self, **kwargs) -> Dict:
        """
        Build standardized result dictionary.

        Ensures consistent structure across all formatters.

        Args:
            **kwargs: Fields to include in result

        Returns:
            Standardized result dict

        Complexity: 2
        """
        result = {
            "id": kwargs.get("id"),
            "title": kwargs.get("title", "Untitled"),
            "description": kwargs.get("description", ""),
            "url": kwargs.get("url", ""),
            "relevance_score": kwargs.get("relevance_score", 0),
        }

        # Add optional fields if provided
        if "metadata" in kwargs:
            result["metadata"] = kwargs["metadata"]
        if "category" in kwargs:
            result["category"] = kwargs["category"]
        if "tags" in kwargs:
            result["tags"] = kwargs["tags"]
        if "highlights" in kwargs:
            result["highlights"] = kwargs["highlights"]

        return result

    def _safe_convert(self, value: Any, target_type: type, default: Any = None) -> Any:
        """
        Safely convert value to target type.

        Args:
            value: Value to convert
            target_type: Target type (int, float, str, bool)
            default: Default if conversion fails

        Returns:
            Converted value or default

        Complexity: 3
        """
        if value is None:
            return default

        try:
            if target_type == bool:
                if isinstance(value, bool):
                    return value
                if isinstance(value, str):
                    return value.lower() in ("true", "1", "yes", "on")
                return bool(value)

            return target_type(value)
        except (ValueError, TypeError):
            logger.debug(f"Could not convert {value} to {target_type.__name__}")
            return default

    def _get_tag_field(self, obj: Any, tag_field: str) -> Any:
        """
        Extract tag field from object.

        Handles various tag field types:
        - ManyToMany relationships
        - List fields
        - String fields

        Args:
            obj: Object to extract from
            tag_field: Field name containing tags

        Returns:
            Tags or empty list

        Complexity: 3
        """
        try:
            tags = getattr(obj, tag_field, None)
            if not tags:
                return []

            # Handle ManyToMany
            if hasattr(tags, "all"):
                return list(tags.all())

            # Handle list/tuple/string
            return tags if isinstance(tags, (list, tuple, str)) else []
        except Exception as e:
            logger.debug(f"Error getting tag field {tag_field}: {e}")
            return []

    # ============================================================================
    # COMMON FORMATTING WORKFLOW
    # ============================================================================

    def _safe_format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Safely format with error handling.

        Wraps format() call with exception handling.

        Args:
            obj: Django model instance
            config: Search configuration dict
            score: Relevance score

        Returns:
            Formatted result dict or None on error

        Complexity: 2
        """
        try:
            return self.format(obj, config, score)
        except Exception as e:
            logger.error(f"Error in {self.__class__.__name__}.format(): {e}")
            return None


# ============================================================================
# CONCRETE FORMATTER IMPLEMENTATIONS
# ============================================================================


class APIResultFormatter(AbstractFormatter):
    """
    Formats search results for JSON API responses.

    Includes all fields needed for API clients:
    - Highlights for query term highlighting
    - Full metadata
    - Tags

    Complexity Target: ≤4
    """

    def format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Format search result for API response.

        Returns comprehensive result with highlights and metadata.

        Complexity: 4
        """
        try:
            title = self._get_title(obj)
            description = self._get_description(obj)

            result = self._build_result_dict(
                id=getattr(obj, "id", None),
                title=title,
                description=description,
                url=getattr(obj, "url", None) or "",
                relevance_score=score,
            )

            # Add metadata if available
            if hasattr(obj, "category"):
                result["category"] = getattr(obj, "category", "")

            # Add tags if tag field specified
            if config.get("tag_field"):
                tags = self._get_tag_field(obj, config["tag_field"])
                result["tags"] = self._normalize_tags(tags)
            else:
                result["tags"] = []

            # Add additional metadata for API
            result["model_type"] = config.get("category", "Unknown")
            result["icon"] = config.get("icon", "📄")

            return result
        except Exception as e:
            logger.error(f"Error formatting for API: {e}")
            return None


class DisplayResultFormatter(AbstractFormatter):
    """
    Formats search results for HTML template display.

    Includes display-specific fields:
    - Category information
    - Tags
    - Metadata

    Complexity Target: ≤4
    """

    def format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Format search result for template display.

        Complexity: 3
        """
        try:
            title = self._get_title(obj)
            description = self._get_description(obj)

            result = self._build_result_dict(
                id=getattr(obj, "id", None),
                title=title,
                description=description,
                url=getattr(obj, "url", None) or "",
                relevance_score=score,
            )

            # Add category
            result["category"] = config.get("category", "Unknown")
            result["category_icon"] = config.get("icon", "📄")

            # Add tags if available
            if config.get("tag_field"):
                tags = self._get_tag_field(obj, config["tag_field"])
                result["tags"] = self._normalize_tags(tags)
            else:
                result["tags"] = []

            # Add object reference for template access
            result["object"] = obj

            return result
        except Exception as e:
            logger.error(f"Error formatting for display: {e}")
            return None


class MetadataFormatter(AbstractFormatter):
    """
    Formats metadata extracted from search results.

    Handles all metadata types:
    - Dates
    - Author/Category
    - Metrics (rating, views, reading time)
    - Status flags

    Complexity Target: ≤3
    """

    def format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Not used for MetadataFormatter - use format_metadata instead.

        Complexity: 1
        """
        # MetadataFormatter uses format_metadata() instead
        return None

    def format_metadata(self, metadata: Dict) -> Dict:  # noqa: C901
        """
        Format metadata dictionary for display.

        Extracts and formats:
        - Published date
        - Author
        - Category
        - Metrics
        - Status flags

        Args:
            metadata: Raw metadata dict

        Returns:
            Formatted metadata dict

        Complexity: 4 -> Reduced by extracting helper methods
        """
        display_meta = {}

        # Extract different metadata groups
        self._extract_date_fields(metadata, display_meta)
        self._extract_author_category(metadata, display_meta)
        self._extract_metrics(metadata, display_meta)
        self._extract_flags(metadata, display_meta)
        self._extract_severity(metadata, display_meta)

        return display_meta

    def _extract_date_fields(self, metadata: Dict, display_meta: Dict) -> None:
        """Extract and format date fields."""
        if metadata.get("published_at"):
            try:
                from datetime import datetime

                dt = datetime.fromtimestamp(metadata["published_at"])
                display_meta["published_date"] = dt.strftime("%Y-%m-%d")
            except (ValueError, TypeError, OSError):
                pass

    def _extract_author_category(self, metadata: Dict, display_meta: Dict) -> None:
        """Extract author and category information."""
        if metadata.get("author"):
            display_meta["author"] = metadata.get("author_display", metadata["author"])
        if metadata.get("category_display"):
            display_meta["category"] = metadata["category_display"]

    def _extract_metrics(self, metadata: Dict, display_meta: Dict) -> None:
        """Extract metrics like rating, views, reading time."""
        if metadata.get("rating"):
            display_meta["rating"] = metadata["rating"]
        if metadata.get("view_count"):
            display_meta["views"] = metadata["view_count"]
        if metadata.get("reading_time"):
            display_meta["reading_time"] = f"{metadata['reading_time']} min"

    def _extract_flags(self, metadata: Dict, display_meta: Dict) -> None:
        """Extract boolean flags like featured, free, difficulty."""
        if metadata.get("is_featured"):
            display_meta["featured"] = True
        if "is_free" in metadata:
            display_meta["free"] = metadata["is_free"]
        if metadata.get("difficulty"):
            display_meta["difficulty"] = metadata["difficulty"]

    def _extract_severity(self, metadata: Dict, display_meta: Dict) -> None:
        """Extract and map severity level."""
        if metadata.get("severity_level"):
            severity_map = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
            display_meta["severity"] = severity_map.get(
                metadata["severity_level"], "Unknown"
            )


# ============================================================================
# FORMATTER FACTORY
# ============================================================================


class FormatterFactory:
    """
    Factory for creating appropriate formatter instances.

    Routes to correct formatter based on format type.

    Complexity Target: ≤2
    """

    _formatters = {
        "api": APIResultFormatter,
        "display": DisplayResultFormatter,
        "metadata": MetadataFormatter,
    }

    @classmethod
    def create_formatter(cls, format_type: str = "display") -> AbstractFormatter:
        """
        Create formatter instance for specified format type.

        Args:
            format_type: Type of formatter ('api', 'display', 'metadata')

        Returns:
            Formatter instance

        Raises:
            ValueError: If format_type not recognized

        Complexity: 2
        """
        formatter_class = cls._formatters.get(format_type.lower())

        if not formatter_class:
            raise ValueError(
                f"Unknown format type: {format_type}. "
                f"Supported types: {', '.join(cls._formatters.keys())}"
            )

        return formatter_class()

    @classmethod
    def register_formatter(cls, format_type: str, formatter_class: type) -> None:
        """
        Register custom formatter for a format type.

        Args:
            format_type: Type identifier
            formatter_class: Formatter class (must inherit from AbstractFormatter)

        Complexity: 1
        """
        if not issubclass(formatter_class, AbstractFormatter):
            raise TypeError("Formatter must inherit from AbstractFormatter")

        cls._formatters[format_type.lower()] = formatter_class
