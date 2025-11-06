"""
Database Performance Summary Generator

Generates performance summaries from query results.
Complexity: ≤6
"""

from typing import Any, Dict, List

from django.core.management.base import BaseCommand


class PerformanceSummaryGenerator:
    """
    Generates performance summaries and recommendations

    Complexity Target: ≤6
    """

    def __init__(self, command: BaseCommand):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style

    def show_summary(self, results: List[Dict[str, Any]]):
        """
        Display complete performance summary

        Complexity: 4 (reduced from D:22)
        """
        self.stdout.write("\n" + "=" * 40)
        self.stdout.write("PERFORMANCE SUMMARY")
        self.stdout.write("=" * 40)

        successful_results = [r for r in results if r["status"] == "SUCCESS"]

        if not successful_results:
            self.stdout.write(self.style.ERROR("No successful queries to analyze"))
            return

        # Show statistics
        stats = self._calculate_statistics(successful_results)
        self._show_statistics(stats)

        # Show performance grade
        grade_info = self._calculate_grade(stats)
        self._show_grade(grade_info)

        # Show recommendations
        self._show_recommendations(stats, successful_results)

    def _calculate_statistics(self, results: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Calculate performance statistics

        Complexity: 4
        """
        total_queries = len(results)
        execution_times = [r["execution_time"] for r in results]

        avg_time = sum(execution_times) / total_queries
        max_time = max(execution_times)
        min_time = min(execution_times)

        fast_queries = len([r for r in results if r["execution_time"] < 100])
        slow_queries = len([r for r in results if r["execution_time"] > 500])

        return {
            "total_queries": total_queries,
            "avg_time": avg_time,
            "max_time": max_time,
            "min_time": min_time,
            "fast_queries": fast_queries,
            "slow_queries": slow_queries,
        }

    def _show_statistics(self, stats: Dict[str, Any]):
        """
        Display statistics

        Complexity: 1
        """
        self.stdout.write(f"Total Queries Tested: {stats['total_queries']}")
        self.stdout.write(f"Average Execution Time: {stats['avg_time']:.2f}ms")
        self.stdout.write(f"Fastest Query: {stats['min_time']:.2f}ms")
        self.stdout.write(f"Slowest Query: {stats['max_time']:.2f}ms")
        self.stdout.write(f"Fast Queries (<100ms): {stats['fast_queries']}")
        self.stdout.write(f"Slow Queries (>500ms): {stats['slow_queries']}")

    def _calculate_grade(self, stats: Dict[str, Any]) -> Dict[str, Any]:
        """
        Calculate performance grade

        Complexity: 6
        """
        avg_time = stats["avg_time"]
        slow_queries = stats["slow_queries"]

        if avg_time < 50 and slow_queries == 0:
            return {"grade": "A+ (Excellent)", "style": self.style.SUCCESS}
        elif avg_time < 100 and slow_queries <= 1:
            return {"grade": "A (Very Good)", "style": self.style.SUCCESS}
        elif avg_time < 200 and slow_queries <= 2:
            return {"grade": "B (Good)", "style": self.style.WARNING}
        elif avg_time < 500:
            return {"grade": "C (Acceptable)", "style": self.style.WARNING}
        else:
            return {"grade": "D (Needs Optimization)", "style": self.style.ERROR}

    def _show_grade(self, grade_info: Dict[str, Any]):
        """
        Display performance grade

        Complexity: 1
        """
        grade = grade_info["grade"]
        style = grade_info["style"]
        self.stdout.write("Performance Grade: " + style(grade))

    def _show_recommendations(
        self, stats: Dict[str, Any], results: List[Dict[str, Any]]
    ):
        """
        Display recommendations

        Complexity: 4
        """
        self.stdout.write("\nRECOMMENDATIONS:")

        # Check for slow queries
        if stats["slow_queries"] > 0:
            self.stdout.write(
                "- Consider adding more specific indexes for slow queries"
            )

        # Check average time
        if stats["avg_time"] > 100:
            self.stdout.write("- Review query patterns and add composite indexes")

        # Check for N+1 issues
        if any(r["query_count"] > 5 for r in results):
            self.stdout.write("- Check for N+1 query issues in complex views")

        # General recommendations
        self.stdout.write("- Enable query optimization in production")
        self.stdout.write("- Monitor query performance with APM tools")
