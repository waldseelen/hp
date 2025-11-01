"""
Django management command for Page Speed Insights integration
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import requests


class Command(BaseCommand):
    help = "Analyze website performance using Google PageSpeed Insights API"

    def add_arguments(self, parser):
        parser.add_argument(
            "--url",
            type=str,
            help="Specific URL to analyze (default: homepage)",
        )
        parser.add_argument(
            "--strategy",
            choices=["mobile", "desktop"],
            default="mobile",
            help="Analysis strategy (mobile or desktop)",
        )
        parser.add_argument(
            "--api-key",
            type=str,
            help="Google PageSpeed Insights API key",
        )
        parser.add_argument(
            "--save-report",
            action="store_true",
            help="Save detailed report to file",
        )

    def handle(self, *args, **options):  # noqa: C901
        api_key = options.get("api_key") or getattr(settings, "PAGESPEED_API_KEY", None)

        if not api_key:
            raise CommandError(
                "PageSpeed Insights API key is required. "
                "Set PAGESPEED_API_KEY in settings or use --api-key option."
            )

        # Default to homepage if no URL provided
        base_url = "https://your-domain.com"  # Replace with actual domain
        if hasattr(settings, "SITE_URL"):
            base_url = settings.SITE_URL

        url = options.get("url") or base_url
        strategy = options["strategy"]

        self.stdout.write(f"Analyzing {url} for {strategy} performance...")

        # Call PageSpeed Insights API
        api_url = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"
        params = {
            "url": url,
            "key": api_key,
            "strategy": strategy,
            "category": ["PERFORMANCE", "SEO", "BEST_PRACTICES", "ACCESSIBILITY"],
        }

        try:
            response = requests.get(api_url, params=params)
            response.raise_for_status()
            data = response.json()
        except requests.RequestException as e:
            raise CommandError(f"Failed to analyze URL: {e}")

        # Extract key metrics
        lighthouse_result = data.get("lighthouseResult", {})
        categories = lighthouse_result.get("categories", {})

        self.stdout.write(self.style.SUCCESS("\n=== Performance Analysis Results ==="))
        self.stdout.write(f"URL: {url}")
        self.stdout.write(f"Strategy: {strategy.title()}")
        self.stdout.write(
            f'Analysis Time: {lighthouse_result.get("fetchTime", "Unknown")}'
        )

        # Display category scores
        self.stdout.write("\n--- Category Scores ---")
        for category_name, category_data in categories.items():
            score = (
                category_data.get("score", 0) * 100
                if category_data.get("score") is not None
                else 0
            )
            title = category_data.get("title", category_name)

            if score >= 90:
                style = self.style.SUCCESS
            elif score >= 50:
                style = self.style.WARNING
            else:
                style = self.style.ERROR

            self.stdout.write(f"{style(title)}: {score:.0f}/100")

        # Core Web Vitals
        audits = lighthouse_result.get("audits", {})
        core_vitals = {
            "first-contentful-paint": "First Contentful Paint",
            "largest-contentful-paint": "Largest Contentful Paint",
            "first-input-delay": "First Input Delay",
            "cumulative-layout-shift": "Cumulative Layout Shift",
            "speed-index": "Speed Index",
            "total-blocking-time": "Total Blocking Time",
        }

        self.stdout.write("\n--- Core Web Vitals ---")
        for audit_id, audit_title in core_vitals.items():
            audit = audits.get(audit_id, {})
            if audit:
                display_value = audit.get("displayValue", "N/A")
                score = audit.get("score", 0)

                if score is not None:
                    score_pct = score * 100
                    if score_pct >= 90:
                        style = self.style.SUCCESS
                    elif score_pct >= 50:
                        style = self.style.WARNING
                    else:
                        style = self.style.ERROR

                    self.stdout.write(
                        f"{style(audit_title)}: {display_value} ({score_pct:.0f}/100)"
                    )
                else:
                    self.stdout.write(f"{audit_title}: {display_value}")

        # Opportunities for improvement
        self.stdout.write("\n--- Opportunities for Improvement ---")
        opportunities_shown = 0
        for audit_id, audit in audits.items():
            if (
                audit.get("scoreDisplayMode") == "numeric"
                and audit.get("score", 1) < 0.9
            ):
                details = audit.get("details", {})
                if details and opportunities_shown < 5:  # Show top 5 opportunities
                    title = audit.get("title", audit_id)
                    description = audit.get("description", "")
                    display_value = audit.get("displayValue", "")

                    self.stdout.write(f"\n{self.style.WARNING(title)}")
                    if display_value:
                        self.stdout.write(f"  Current: {display_value}")
                    if description:
                        # Truncate long descriptions
                        desc = (
                            description[:200] + "..."
                            if len(description) > 200
                            else description
                        )
                        self.stdout.write(f"  {desc}")

                    opportunities_shown += 1

        # Save detailed report if requested
        if options["save_report"]:
            report_filename = f'pagespeed_report_{strategy}_{url.replace("/", "_").replace(":", "")}.json'
            try:
                with open(report_filename, "w") as f:
                    json.dump(data, f, indent=2)
                self.stdout.write(f"\nDetailed report saved to: {report_filename}")
            except IOError as e:
                self.stdout.write(self.style.ERROR(f"Failed to save report: {e}"))

        # Recommendations
        self.stdout.write("\n--- Recommendations ---")
        performance_score = categories.get("performance", {}).get("score", 0) * 100

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

        self.stdout.write(
            f"\nFor detailed analysis, visit: https://pagespeed.web.dev/analysis?url={url}"
        )
