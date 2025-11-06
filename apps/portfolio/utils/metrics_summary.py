"""
Performance Metrics Summary Generators
=====================================

Helper classes for generating performance metrics summaries
using Extract Class refactoring pattern.

Complexity reduced: C:16 → A:1 (main method)
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List

logger = logging.getLogger(__name__)


@dataclass
class MetricStatistics:
    """Container for calculated metric statistics"""

    count: int
    average: float
    min: float
    max: float
    latest: float
    p50: float
    p75: float
    p95: float
    score: float = 0
    status: str = "unknown"


class MetricStatsCalculator:
    """
    Calculate statistics for metric values

    Complexity: A:4
    """

    def __init__(self, percentile_func):
        self._percentile = percentile_func

    def calculate(self, values: List[float]) -> Dict[str, Any]:
        """
        Calculate basic statistics for values

        Complexity: A:4
        """
        if not values:
            return self._empty_stats()

        sorted_values = sorted(values)

        return {
            "count": len(values),
            "average": sum(values) / len(values),
            "min": min(values),
            "max": max(values),
            "latest": values[-1],
            "p50": self._percentile(sorted_values, 50),
            "p75": self._percentile(sorted_values, 75),
            "p95": self._percentile(sorted_values, 95),
        }

    def _empty_stats(self) -> Dict[str, Any]:
        """Return empty statistics structure"""
        return {
            "count": 0,
            "average": 0,
            "min": 0,
            "max": 0,
            "latest": 0,
            "p50": 0,
            "p75": 0,
            "p95": 0,
        }


class MetricScoreCalculator:
    """
    Calculate performance scores and status

    Complexity: A:5
    """

    def __init__(self, thresholds: Dict, calculate_score_func, get_status_func):
        self.thresholds = thresholds
        self._calculate_score = calculate_score_func
        self._get_status = get_status_func

    def enhance_stats(
        self, metric_type: str, stats: Dict[str, Any]
    ) -> tuple[Dict[str, Any], float]:
        """
        Add score and status to statistics

        Returns:
            (enhanced_stats, score)

        Complexity: A:3
        """
        if metric_type not in self.thresholds:
            return stats, 0

        score = self._calculate_score(metric_type, stats["p75"])
        stats["score"] = score
        stats["status"] = self._get_status(metric_type, stats["p75"])

        return stats, score


class HealthScoreCalculator:
    """
    Calculate overall health score from individual metric scores

    Complexity: B:6
    """

    def calculate(self, total_score_sum: float, scored_metrics: int) -> str:
        """
        Calculate health grade based on average score

        Complexity: B:6
        """
        if scored_metrics == 0:
            return "A"

        avg_score = total_score_sum / scored_metrics

        if avg_score >= 90:
            return "A"
        elif avg_score >= 75:
            return "B"
        elif avg_score >= 60:
            return "C"
        elif avg_score >= 40:
            return "D"
        else:
            return "F"


class MetricsSummaryGenerator:
    """
    Generate comprehensive metrics summary with statistics and health score

    Main orchestrator using helper classes.
    Complexity: A:5
    """

    def __init__(
        self,
        stats_calculator: MetricStatsCalculator,
        score_calculator: MetricScoreCalculator,
        health_calculator: HealthScoreCalculator,
    ):
        self.stats_calculator = stats_calculator
        self.score_calculator = score_calculator
        self.health_calculator = health_calculator

    def generate(
        self,
        metrics_data: Dict[str, List],
        hours: int,
        timestamp_generator,
    ) -> Dict[str, Any]:
        """
        Generate complete metrics summary

        Args:
            metrics_data: Dict of metric_type -> list of entries
            hours: Time period in hours
            timestamp_generator: Function to get current timestamp

        Returns:
            Complete summary dictionary

        Complexity: A:5
        """
        summary = {
            "period_hours": hours,
            "generated_at": timestamp_generator().isoformat(),
            "metrics": {},
            "health_score": "A",
            "total_entries": 0,
        }

        total_score_sum = 0
        scored_metrics = 0

        # Process each metric type
        for metric_type, entries in metrics_data.items():
            if not entries:
                continue

            values = [entry.value for entry in entries]

            # Calculate statistics
            stats = self.stats_calculator.calculate(values)

            # Add score and status if applicable
            enhanced_stats, score = self.score_calculator.enhance_stats(
                metric_type, stats
            )

            if score > 0:
                total_score_sum += score
                scored_metrics += 1

            summary["metrics"][metric_type] = enhanced_stats
            summary["total_entries"] += len(values)

        # Calculate overall health score
        summary["health_score"] = self.health_calculator.calculate(
            total_score_sum, scored_metrics
        )

        return summary


def create_summary_generator(
    percentile_func,
    thresholds: Dict,
    calculate_score_func,
    get_status_func,
) -> MetricsSummaryGenerator:
    """
    Factory function to create configured MetricsSummaryGenerator

    Complexity: A:1
    """
    stats_calc = MetricStatsCalculator(percentile_func)
    score_calc = MetricScoreCalculator(
        thresholds, calculate_score_func, get_status_func
    )
    health_calc = HealthScoreCalculator()

    return MetricsSummaryGenerator(stats_calc, score_calc, health_calc)
