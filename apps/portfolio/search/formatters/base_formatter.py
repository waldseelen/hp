"""
Search Result Formatter Base Class

Handles formatting of search results with reduced complexity.
Complexity: ≤6 (reduced from D:27)
"""

import logging
from typing import Any, Dict, Optional

from django.utils.html import strip_tags

from .metadata_collector import MetadataCollector
from .url_builder import URLBuilder

logger = logging.getLogger(__name__)


class SearchResultFormatter:
    """
    Formats search results for display

    Strategy Pattern: Delegates URL building and metadata collection
    to specialized classes.

    Complexity Target: ≤6 (reduced from D:27)
    """

    def __init__(self):
        self.url_builder = URLBuilder()
        self.metadata_collector = MetadataCollector()

    def format(self, obj: Any, config: dict, score: float) -> Optional[Dict]:
        """
        Format search result object for display

        Args:
            obj: Django model instance
            config: Search configuration dict
            score: Relevance score

        Returns:
            Formatted result dict or None on error

        Complexity: 4 (reduced from D:27)
        """
        try:
            title = self._get_title(obj)
            description = self._get_description(obj)
            url = self.url_builder.build_url(obj, config)
            metadata = self.metadata_collector.collect_metadata(obj, config)

            return {
                "id": getattr(obj, "id", None),
                "title": title,
                "description": description,
                "url": url,
                "relevance_score": score,
                "metadata": metadata["date"],
                "category": metadata["category"],
                "tags": metadata["tags"],
                "object": obj,  # Include original object for template access
            }

        except Exception as e:
            logger.error(f"Error formatting search result: {e}")
            return None

    def _get_title(self, obj: Any) -> str:
        """
        Extract title/name from object

        Complexity: 1
        """
        return getattr(obj, "title", None) or getattr(obj, "name", "Untitled")

    def _get_description(self, obj: Any) -> str:
        """
        Extract and format description

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
        description = strip_tags(str(description))

        # Truncate if needed
        if len(description) > 200:
            return description[:200] + "..."

        return description
