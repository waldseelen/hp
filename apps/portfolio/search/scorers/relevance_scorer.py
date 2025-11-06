"""
Relevance Scorer for Search Results

Calculates relevance scores with modular, testable logic.
Complexity: ≤7 (reduced from D:26)
"""

import logging
import re
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


class RelevanceScorer:
    """
    Calculates relevance scores for search results

    Strategy Pattern: Breaks scoring into specialized methods
    for field matching, tag matching, and boost factors.

    Complexity Target: ≤7 (reduced from D:26)
    """

    # Field weights for relevance calculation
    FIELD_WEIGHTS = {
        "title": 10,
        "name": 10,
        "excerpt": 5,
        "description": 5,
        "content": 3,
        "detailed_description": 3,
        "meta_description": 2,
    }

    def calculate_score(
        self,
        obj: Any,
        keywords: List[str],
        fields: List[str],
        tag_field: str,
        base_weight: int,
    ) -> float:
        """
        Calculate overall relevance score

        Args:
            obj: Django model instance
            keywords: Search keywords
            fields: Fields to search in
            tag_field: Tag field name
            base_weight: Base model weight

        Returns:
            Calculated relevance score

        Complexity: 5 (reduced from D:26)
        """
        # Calculate base score from field matches
        field_score = self._score_field_matches(obj, keywords, fields)

        # Add tag match bonus
        tag_score = self._score_tag_matches(obj, keywords, tag_field)

        # Calculate total before boosts
        total_score = (field_score + tag_score) * (base_weight / 10)

        # Apply boost factors
        boosted_score = self._apply_boosts(obj, total_score)

        return round(boosted_score, 2)

    def _score_field_matches(
        self, obj: Any, keywords: List[str], fields: List[str]
    ) -> float:
        """
        Score matches in object fields

        Complexity: 6
        """
        score = 0

        for field in fields:
            try:
                value = getattr(obj, field, "") or ""
                if not isinstance(value, str):
                    continue

                value_lower = value.lower()
                field_weight = self._get_field_weight(field)

                for keyword in keywords:
                    keyword_lower = keyword.lower()

                    if keyword_lower in value_lower:
                        match_score = self._calculate_match_score(
                            field, value_lower, keyword_lower, field_weight
                        )
                        score += match_score

            except (AttributeError, TypeError):
                continue

        return score

    def _get_field_weight(self, field: str) -> int:
        """
        Get weight for field

        Complexity: 1
        """
        field_name = field.split("_")[-1]
        return self.FIELD_WEIGHTS.get(field_name, 1)

    def _calculate_match_score(
        self, field: str, value: str, keyword: str, weight: int
    ) -> float:
        """
        Calculate score for a single keyword match

        Complexity: 4
        """
        # Exact match in title/name
        if field in ["title", "name"] and keyword == value:
            return weight * 20

        # Partial match in title/name
        elif field in ["title", "name"]:
            return weight * 10

        # Word boundary match
        elif re.search(rf"\b{re.escape(keyword)}\b", value):
            return weight * 5

        # Partial match
        else:
            return weight * 2

    def _score_tag_matches(
        self, obj: Any, keywords: List[str], tag_field: str
    ) -> float:
        """
        Score matches in tags

        Complexity: 4 (reduced from C:11)
        """
        if not tag_field:
            return 0

        try:
            tags = self._get_normalized_tags(obj, tag_field)
            return self._calculate_tag_score(tags, keywords)
        except (AttributeError, TypeError):
            return 0

    def _get_normalized_tags(self, obj: Any, tag_field: str) -> List[str]:
        """
        Get normalized tag list

        Complexity: 3
        """
        tags = getattr(obj, tag_field, [])

        if not tags:
            return []

        # String tags (comma-separated)
        if isinstance(tags, str):
            return [tag.strip() for tag in tags.split(",")]

        # List tags
        if isinstance(tags, list):
            return tags

        return []

    def _calculate_tag_score(self, tags: List[str], keywords: List[str]) -> float:
        """
        Calculate score for tag matches

        Complexity: 2
        """
        score = 0
        for keyword in keywords:
            for tag in tags:
                if isinstance(tag, str) and keyword.lower() in tag.lower():
                    score += 8
        return score

    def _apply_boosts(self, obj: Any, score: float) -> float:
        """
        Apply boost factors to score

        Complexity: 4
        """
        # Featured item boost
        if hasattr(obj, "is_featured") and obj.is_featured:
            score *= 1.5

        # Recency boost
        if hasattr(obj, "created_at"):
            from django.utils import timezone

            days_old = (timezone.now() - obj.created_at).days

            if days_old < 30:
                score *= 1.2
            elif days_old < 90:
                score *= 1.1

        return score
