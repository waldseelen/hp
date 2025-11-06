"""
URL Builder for Search Results

Handles URL generation with proper error handling.
Complexity: ≤3 (previously part of D:27 method)
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)


class URLBuilder:
    """
    Builds URLs for search results based on configuration

    Complexity Target: ≤3
    """

    def build_url(self, obj: Any, config: dict) -> Optional[str]:
        """
        Build URL for search result object

        Args:
            obj: Django model instance
            config: Search configuration dict with url_name and url_field

        Returns:
            URL string or None if URL cannot be built

        Complexity: 3
        """
        url_name = config.get("url_name")
        url_field = config.get("url_field")

        if url_name and url_field:
            return self._build_url_with_field(obj, url_name, url_field)
        elif url_name:
            return self._build_url_with_anchor(obj, url_name)

        return None

    def _build_url_with_field(
        self, obj: Any, url_name: str, url_field: str
    ) -> Optional[str]:
        """
        Build URL using reverse with field value

        Complexity: 2
        """
        try:
            from django.urls import reverse

            url_value = getattr(obj, url_field)
            return reverse(url_name, args=[url_value])
        except Exception as e:
            logger.debug(f"Could not build URL with field: {e}")
            return None

    def _build_url_with_anchor(self, obj: Any, url_name: str) -> Optional[str]:
        """
        Build URL with anchor tag

        Complexity: 2
        """
        try:
            from django.urls import reverse

            url = reverse(url_name)
            if hasattr(obj, "id"):
                url += f"#{obj.id}"
            return url
        except Exception as e:
            logger.debug(f"Could not build URL with anchor: {e}")
            return None
