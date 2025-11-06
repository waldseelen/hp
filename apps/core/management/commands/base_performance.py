"""
Base performance monitoring command with template method pattern.

This abstract base class provides a framework for performance monitoring commands.
Subclasses can override specific methods to customize behavior while maintaining
a consistent interface.
"""

import json
from abc import ABC, abstractmethod
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand


class BasePerformanceCommand(BaseCommand, ABC):
    """
    Abstract base class for performance monitoring commands.

    Implements Template Method Pattern:
    - handle() defines the algorithm skeleton
    - Subclasses implement hook methods for customization

    Cyclomatic Complexity: 3 (Target: ≤7)
    """

    def add_arguments(self, parser):
        """Add common command-line arguments."""
        parser.add_argument(
            "--duration",
            type=int,
            default=60,
            help="Monitoring duration in seconds (default: 60)",
        )
        parser.add_argument(
            "--interval",
            type=int,
            default=5,
            help="Sampling interval in seconds (default: 5)",
        )
        parser.add_argument(
            "--output",
            type=str,
            default="reports/performance_metrics.json",
            help="Output file for metrics (default: reports/performance_metrics.json)",
        )

    def handle(self, *args, **options):
        """
        Template method - defines the algorithm skeleton.

        This method orchestrates the performance monitoring workflow:
        1. Initialize monitoring
        2. Collect metrics over time
        3. Save results
        4. Display summary
        """
        duration = options["duration"]
        interval = options["interval"]
        output_file = options["output"]

        self.on_start(duration)

        metrics = self.collect_metrics_loop(duration, interval)

        self.save_metrics(metrics, output_file)

        report = self.generate_report(metrics)

        self.display_report(report)

    def on_start(self, duration):
        """Hook: Called when monitoring starts."""
        self.stdout.write(
            self.style.SUCCESS(
                f"\n🔍 Starting performance monitoring for {duration} seconds...\n"
            )
        )

    @abstractmethod
    def collect_metrics_loop(self, duration, interval):
        """
        Hook: Implement metrics collection loop.

        Args:
            duration: Total monitoring duration in seconds
            interval: Sampling interval in seconds

        Returns:
            list: Collected metrics over time
        """
        pass

    @abstractmethod
    def generate_report(self, metrics):
        """
        Hook: Generate performance report from collected metrics.

        Args:
            metrics: List of metric dictionaries

        Returns:
            dict: Formatted performance report
        """
        pass

    def save_metrics(self, metrics, output_file):
        """Save metrics to JSON file."""
        output_path = Path(output_file)
        output_path.parent.mkdir(parents=True, exist_ok=True)

        with open(output_path, "w") as f:
            json.dump(metrics, f, indent=2)

        self.stdout.write(self.style.SUCCESS(f"\n✅ Metrics saved to {output_file}"))

    def display_report(self, report):
        """
        Hook: Display the generated report.

        Default implementation prints JSON. Override for custom formatting.
        """
        self.stdout.write(self.style.SUCCESS("\n📊 PERFORMANCE REPORT\n"))
        self.stdout.write(json.dumps(report, indent=2))
