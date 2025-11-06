"""
Metadata Collector for Search Results

Extracts and formats metadata from search result objects.
Complexity: ≤4 (previously part of D:27 method)
"""

import logging
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class MetadataCollector:
    """
    Collects metadata from search result objects

    Complexity Target: ≤4
    """

    def collect_metadata(self, obj: Any, config: dict) -> Dict[str, Any]:
        """
        Collect all metadata for search result

        Args:
            obj: Django model instance
            config: Search configuration dict

        Returns:
            Dictionary with date, category, and tags

        Complexity: 2
        """
        return {
            "date": self._get_date(obj),
            "category": self._get_category(obj),
            "tags": self._get_tags(obj, config.get("tag_field")),
        }

    def _get_date(self, obj: Any) -> Optional[str]:
        """
        Extract date from object

        Complexity: 2
        """
        if hasattr(obj, "published_at") and obj.published_at:
            return obj.published_at.strftime("%Y-%m-%d")
        elif hasattr(obj, "created_at") and obj.created_at:
            return obj.created_at.strftime("%Y-%m-%d")
        return None

    def _get_category(self, obj: Any) -> Optional[str]:
        """
        Extract category from object

        Complexity: 4
        """
        # Try category with display_name
        if hasattr(obj, "category"):
            category = obj.category
            if hasattr(category, "display_name"):
                return category.display_name

        # Try get_category_display method
        if hasattr(obj, "get_category_display"):
            return obj.get_category_display()

        # Try get_type_display method
        if hasattr(obj, "get_type_display"):
            return obj.get_type_display()

        return None

    def _get_tags(self, obj: Any, tag_field: Optional[str]) -> List[str]:
        """
        Extract tags from object

        Complexity: 3 (reduced from B:9)
        """
        if not tag_field:
            return []

        try:
            tag_data = getattr(obj, tag_field, [])
            return self._normalize_tags(tag_data)
        except (AttributeError, TypeError) as e:
            logger.debug(f"Could not extract tags: {e}")
            return []

    def _normalize_tags(self, tag_data: Any) -> List[str]:
        """
        Normalize tag data to list

        Complexity: 2
        """
        # String tags (comma-separated)
        if isinstance(tag_data, str):
            return [tag.strip() for tag in tag_data.split(",") if tag.strip()][
                :5
            ]  # Limit to 5 tags

        # List tags
        if isinstance(tag_data, list):
            return [str(tag) for tag in tag_data if tag][:5]

        return []
