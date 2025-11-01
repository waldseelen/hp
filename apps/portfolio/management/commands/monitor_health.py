"""
Health Monitoring Management Command
Continuous monitoring of system health with alerts
"""

import logging
import signal
import sys
import time

from django.core.management.base import BaseCommand
from django.utils import timezone

from apps.main.health_checks import health_checker

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """
    Continuous health monitoring command
    Usage: python manage.py monitor_health [--interval=60] [--daemon]
    """

    help = "Monitor system health continuously"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.monitoring = True
        self.stats = {
            "checks_run": 0,
            "healthy_count": 0,
            "warning_count": 0,
            "unhealthy_count": 0,
            "error_count": 0,
            "started_at": None,
        }

    def add_arguments(self, parser):
        parser.add_argument(
            "--interval",
            type=int,
            default=300,  # 5 minutes
            help="Health check interval in seconds (default: 300)",
        )

        parser.add_argument(
            "--daemon",
            action="store_true",
            help="Run as daemon (continue until stopped)",
        )

        parser.add_argument(
            "--once", action="store_true", help="Run health check once and exit"
        )

        parser.add_argument("--verbose", action="store_true", help="Verbose output")

    def handle(self, *args, **options):
        """Main command handler"""
        self.options = options
        self.interval = options["interval"]
        self.daemon_mode = options["daemon"]
        self.once_mode = options["once"]
        self.verbose = options["verbose"]

        # Set up signal handlers for graceful shutdown
        signal.signal(signal.SIGINT, self._signal_handler)
        signal.signal(signal.SIGTERM, self._signal_handler)

        self.stats["started_at"] = timezone.now()

        if self.once_mode:
            self.stdout.write("Running single health check...")
            self._run_single_check()
        elif self.daemon_mode:
            self.stdout.write(
                f"Starting health monitoring daemon (interval: {self.interval}s)"
            )
            self._run_daemon()
        else:
            self.stdout.write(
                f"Running health monitoring for {self.interval}s intervals. Press Ctrl+C to stop."
            )
            self._run_continuous()

    def _run_single_check(self):
        """Run a single health check"""
        try:
            results = health_checker.run_all_checks()
            self._display_results(results)
            self._update_stats(results)

            # Exit with appropriate code
            if results["overall_status"] == "healthy":
                sys.exit(0)
            elif results["overall_status"] == "warning":
                sys.exit(1)
            else:
                sys.exit(2)

        except Exception as e:
            self.stderr.write(f"Health check failed: {e}")
            sys.exit(3)

    def _run_daemon(self):
        """Run as daemon"""
        self.stdout.write("Health monitoring daemon started. Use 'kill' to stop.")

        while self.monitoring:
            try:
                self._perform_health_check()
                time.sleep(self.interval)
            except KeyboardInterrupt:
                break
            except Exception as e:
                logger.error(f"Health monitoring error: {e}")
                if self.verbose:
                    self.stderr.write(f"Error during monitoring: {e}")
                time.sleep(min(self.interval, 60))  # Wait at least 60s on error

        self._show_final_stats()

    def _run_continuous(self):
        """Run continuously until interrupted"""
        try:
            while self.monitoring:
                self._perform_health_check()

                if not self.monitoring:
                    break

                # Show countdown if verbose
                if self.verbose:
                    self.stdout.write(f"Next check in {self.interval} seconds...")

                for i in range(self.interval):
                    if not self.monitoring:
                        break
                    time.sleep(1)

        except KeyboardInterrupt:
            pass

        self._show_final_stats()

    def _perform_health_check(self):
        """Perform a single health check cycle"""
        try:
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")

            if self.verbose:
                self.stdout.write(f"[{timestamp}] Running health check...")

            results = health_checker.run_all_checks()

            self._update_stats(results)

            if self.verbose or results["overall_status"] != "healthy":
                self._display_results(results)

            # Log results
            logger.info(
                f"Health check completed: {results['overall_status']} "
                f"({results['summary']['passed']}/{results['summary']['total_checks']} passed)"
            )

        except Exception as e:
            self.stats["error_count"] += 1
            logger.error(f"Health check failed: {e}")
            if self.verbose:
                self.stderr.write(f"Health check error: {e}")

    def _display_results(self, results):
        """Display health check results"""
        timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S")
        status = results["overall_status"].upper()

        # Choose color based on status
        if status == "HEALTHY":
            status_style = self.style.SUCCESS(status)
        elif status == "WARNING":
            status_style = self.style.WARNING(status)
        else:
            status_style = self.style.ERROR(status)

        self.stdout.write(f"\n[{timestamp}] System Status: {status_style}")

        # Summary
        summary = results["summary"]
        self.stdout.write(
            f"Checks: {summary['total_checks']} total, "
            f"{summary['passed']} passed, "
            f"{summary['warnings']} warnings, "
            f"{summary['failed']} failed"
        )

        # Details for non-healthy checks
        if results["overall_status"] != "healthy":
            self.stdout.write("\nIssues detected:")

            for check_name, check_result in results["checks"].items():
                if check_result["status"] != "healthy":
                    status_icon = (
                        "WARN" if check_result["status"] == "warning" else "FAIL"
                    )
                    self.stdout.write(
                        f"  {status_icon} {check_name}: {check_result.get('message', 'No message')}"
                    )

                    # Show additional details if available
                    if (
                        "details" in check_result
                        and "issues" in check_result["details"]
                    ):
                        for issue in check_result["details"]["issues"]:
                            self.stdout.write(f"    - {issue}")

        self.stdout.write("-" * 50)

    def _update_stats(self, results):
        """Update monitoring statistics"""
        self.stats["checks_run"] += 1

        if results["overall_status"] == "healthy":
            self.stats["healthy_count"] += 1
        elif results["overall_status"] == "warning":
            self.stats["warning_count"] += 1
        elif results["overall_status"] == "unhealthy":
            self.stats["unhealthy_count"] += 1
        else:
            self.stats["error_count"] += 1

    def _show_final_stats(self):
        """Show final monitoring statistics"""
        if self.stats["checks_run"] == 0:
            return

        duration = timezone.now() - self.stats["started_at"]
        duration_str = str(duration).split(".")[0]  # Remove microseconds

        self.stdout.write("\nHealth Monitoring Summary:")
        self.stdout.write(f"Duration: {duration_str}")
        self.stdout.write(f"Total checks: {self.stats['checks_run']}")
        self.stdout.write(f"Healthy: {self.stats['healthy_count']}")
        self.stdout.write(f"Warnings: {self.stats['warning_count']}")
        self.stdout.write(f"Unhealthy: {self.stats['unhealthy_count']}")
        self.stdout.write(f"Errors: {self.stats['error_count']}")

        if self.stats["checks_run"] > 0:
            uptime_percent = (
                self.stats["healthy_count"] / self.stats["checks_run"]
            ) * 100
            self.stdout.write(f"Uptime: {uptime_percent:.1f}%")

        self.stdout.write("Health monitoring stopped.")

    def _signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        self.stdout.write(f"\nReceived signal {signum}. Shutting down gracefully...")
        self.monitoring = False
