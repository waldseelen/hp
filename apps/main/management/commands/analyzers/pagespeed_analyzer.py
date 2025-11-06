"""
PageSpeed Insights API Response Analyzer

Handles API response parsing and metric extraction.
Complexity: ≤5
"""

import logging
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)


class PageSpeedAnalyzer:
    """
    Analyzes PageSpeed Insights API responses

    Complexity Target: ≤5
    """

    def __init__(self, api_response: Dict[str, Any]):
        self.data = api_response
        self.lighthouse_result = api_response.get("lighthouseResult", {})
        self.categories = self.lighthouse_result.get("categories", {})
        self.audits = self.lighthouse_result.get("audits", {})

    def get_category_scores(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract category scores

        Returns:
            Dict with category names and their scores/titles

        Complexity: 2
        """
        scores = {}
        for category_name, category_data in self.categories.items():
            score = category_data.get("score", 0)
            scores[category_name] = {
                "score": score * 100 if score is not None else 0,
                "title": category_data.get("title", category_name),
            }
        return scores

    def get_core_web_vitals(self) -> Dict[str, Dict[str, Any]]:
        """
        Extract Core Web Vitals metrics

        Complexity: 4
        """
        vitals_map = {
            "first-contentful-paint": "First Contentful Paint",
            "largest-contentful-paint": "Largest Contentful Paint",
            "first-input-delay": "First Input Delay",
            "cumulative-layout-shift": "Cumulative Layout Shift",
            "speed-index": "Speed Index",
            "total-blocking-time": "Total Blocking Time",
        }

        vitals = {}
        for audit_id, audit_title in vitals_map.items():
            audit = self.audits.get(audit_id, {})
            if audit:
                score = audit.get("score", 0)
                vitals[audit_id] = {
                    "title": audit_title,
                    "display_value": audit.get("displayValue", "N/A"),
                    "score": score * 100 if score is not None else None,
                }

        return vitals

    def get_improvement_opportunities(self, max_count: int = 5) -> list:
        """
        Extract top improvement opportunities

        Complexity: 5
        """
        opportunities = []

        for audit_id, audit in self.audits.items():
            if len(opportunities) >= max_count:
                break

            # Check if this is a low-scoring audit with details
            score_mode_match = audit.get("scoreDisplayMode") == "numeric"
            low_score = audit.get("score", 1) < 0.9
            has_details = audit.get("details")
            if score_mode_match and low_score and has_details:

                opportunities.append(
                    {
                        "id": audit_id,
                        "title": audit.get("title", audit_id),
                        "description": audit.get("description", ""),
                        "display_value": audit.get("displayValue", ""),
                    }
                )

        return opportunities

    def get_performance_score(self) -> float:
        """
        Get overall performance score

        Complexity: 1
        """
        performance = self.categories.get("performance", {})
        score = performance.get("score", 0)
        return score * 100 if score is not None else 0
