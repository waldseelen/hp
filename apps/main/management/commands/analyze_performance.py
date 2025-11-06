"""
Django management command for Page Speed Insights integration

REFACTORED: Complexity reduced from D:27 to B:6
Using Strategy Pattern and Extract Method refactoring.
"""

import json

from django.conf import settings
from django.core.management.base import BaseCommand, CommandError

import requests

from .analyzers import PageSpeedAnalyzer
from .formatters import PerformanceReportFormatter


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

    def handle(self, *args, **options):
        """
        Main orchestrator method

        REFACTORED: Complexity reduced from D:27 to B:6
        """
        # Validate and get API configuration
        api_key = self._get_api_key(options)
        url = self._get_target_url(options)
        strategy = options["strategy"]

        # Fetch performance data
        self.stdout.write(f"Analyzing {url} for {strategy} performance...")
        data = self._fetch_pagespeed_data(url, strategy, api_key)

        # Analyze results
        analyzer = PageSpeedAnalyzer(data)
        formatter = PerformanceReportFormatter(self)

        # Display results
        self._display_results(analyzer, formatter, url, strategy)

        # Save report if requested
        if options["save_report"]:
            self._save_report(data, url, strategy)

        # Show final link
        formatter.show_footer(url)

    def _get_api_key(self, options):
        """
        Get API key from options or settings

        Complexity: 2
        """
        api_key = options.get("api_key") or getattr(settings, "PAGESPEED_API_KEY", None)

        if not api_key:
            raise CommandError(
                "PageSpeed Insights API key is required. "
                "Set PAGESPEED_API_KEY in settings or use --api-key option."
            )

        return api_key

    def _get_target_url(self, options):
        """
        Get target URL from options or settings

        Complexity: 2
        """
        if options.get("url"):
            return options["url"]

        # Default to site URL or placeholder
        if hasattr(settings, "SITE_URL"):
            return settings.SITE_URL

        return "https://your-domain.com"

    def _fetch_pagespeed_data(self, url, strategy, api_key):
        """
        Fetch data from PageSpeed Insights API

        Complexity: 2
        """
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
            return response.json()
        except requests.RequestException as e:
            raise CommandError(f"Failed to analyze URL: {e}")

    def _display_results(self, analyzer, formatter, url, strategy):
        """
        Display analysis results using formatter

        Complexity: 3
        """
        # Show header
        fetch_time = analyzer.lighthouse_result.get("fetchTime", "Unknown")
        formatter.show_header(url, strategy, fetch_time)

        # Show category scores
        scores = analyzer.get_category_scores()
        formatter.show_category_scores(scores)

        # Show Core Web Vitals
        vitals = analyzer.get_core_web_vitals()
        formatter.show_core_web_vitals(vitals)

        # Show improvement opportunities
        opportunities = analyzer.get_improvement_opportunities(max_count=5)
        formatter.show_opportunities(opportunities)

        # Show recommendations
        performance_score = analyzer.get_performance_score()
        formatter.show_recommendations(performance_score)

    def _save_report(self, data, url, strategy):
        """
        Save detailed report to JSON file

        Complexity: 2
        """
        # Generate safe filename
        safe_url = url.replace("/", "_").replace(":", "")
        filename = f"pagespeed_report_{strategy}_{safe_url}.json"

        try:
            with open(filename, "w") as f:
                json.dump(data, f, indent=2)
            self.stdout.write(f"\nDetailed report saved to: {filename}")
        except IOError as e:
            self.stdout.write(self.style.ERROR(f"Failed to save report: {e}"))
