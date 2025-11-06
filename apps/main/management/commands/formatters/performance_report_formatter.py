"""
Performance Report Formatter

Handles console output formatting for performance analysis.
Complexity: ≤6
"""

from typing import Any, Dict, List

from django.core.management.base import BaseCommand


class PerformanceReportFormatter:
    """
    Formats performance analysis results for console output

    Complexity Target: ≤6
    """

    def __init__(self, command: BaseCommand):
        self.command = command
        self.stdout = command.stdout
        self.style = command.style

    def show_header(self, url: str, strategy: str, fetch_time: str):
        """
        Display report header

        Complexity: 1
        """
        self.stdout.write(self.style.SUCCESS("\n=== Performance Analysis Results ==="))
        self.stdout.write(f"URL: {url}")
        self.stdout.write(f"Strategy: {strategy.title()}")
        self.stdout.write(f"Analysis Time: {fetch_time}")

    def show_category_scores(self, scores: Dict[str, Dict[str, Any]]):
        """
        Display category scores with color coding

        Complexity: 4
        """
        self.stdout.write("\n--- Category Scores ---")

        for category_data in scores.values():
            score = category_data["score"]
            title = category_data["title"]

            # Color code based on score
            if score >= 90:
                style = self.style.SUCCESS
            elif score >= 50:
                style = self.style.WARNING
            else:
                style = self.style.ERROR

            self.stdout.write(f"{style(title)}: {score:.0f}/100")

    def show_core_web_vitals(self, vitals: Dict[str, Dict[str, Any]]):
        """
        Display Core Web Vitals metrics

        Complexity: 5
        """
        self.stdout.write("\n--- Core Web Vitals ---")

        for vital_data in vitals.values():
            title = vital_data["title"]
            display_value = vital_data["display_value"]
            score = vital_data["score"]

            if score is not None:
                # Color code based on score
                if score >= 90:
                    style = self.style.SUCCESS
                elif score >= 50:
                    style = self.style.WARNING
                else:
                    style = self.style.ERROR

                self.stdout.write(f"{style(title)}: {display_value} ({score:.0f}/100)")
            else:
                self.stdout.write(f"{title}: {display_value}")

    def show_opportunities(self, opportunities: List[Dict[str, str]]):
        """
        Display improvement opportunities

        Complexity: 4
        """
        if not opportunities:
            return

        self.stdout.write("\n--- Opportunities for Improvement ---")

        for opp in opportunities:
            self.stdout.write(f'\n{self.style.WARNING(opp["title"])}')

            if opp["display_value"]:
                self.stdout.write(f'  Current: {opp["display_value"]}')

            if opp["description"]:
                # Truncate long descriptions
                desc = opp["description"]
                if len(desc) > 200:
                    desc = desc[:200] + "..."
                self.stdout.write(f"  {desc}")

    def show_recommendations(self, performance_score: float):
        """
        Display recommendations based on performance score

        Complexity: 4
        """
        self.stdout.write("\n--- Recommendations ---")

        if performance_score < 50:
            self.stdout.write(
                self.style.ERROR("Performance needs immediate attention:")
            )
            self.stdout.write("• Optimize images and use WebP format")
            self.stdout.write("• Enable compression and caching")
            self.stdout.write("• Minimize CSS and JavaScript")
            self.stdout.write("• Consider using a CDN")
        elif performance_score < 90:
            self.stdout.write(self.style.WARNING("Performance can be improved:"))
            self.stdout.write("• Review and optimize large resources")
            self.stdout.write("• Consider lazy loading for images")
            self.stdout.write("• Review third-party scripts")
        else:
            self.stdout.write(
                self.style.SUCCESS("Great performance! Keep monitoring regularly.")
            )

    def show_footer(self, url: str):
        """
        Display footer with link to detailed analysis

        Complexity: 1
        """
        self.stdout.write(
            f"\nFor detailed analysis, visit: "
            f"https://pagespeed.web.dev/analysis?url={url}"
        )
