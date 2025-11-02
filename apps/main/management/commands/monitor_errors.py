import json
import os
import threading
import time
from datetime import datetime, timedelta

from django.conf import settings
from django.core.management.base import BaseCommand

from apps.main.logging.json_formatter import (
    server_management_logger,
    template_error_logger,
)


class Command(BaseCommand):
    help = "Monitor Django errors and implement recovery actions from fix all.yml"

    def add_arguments(self, parser):
        parser.add_argument(
            "--watch-logs",
            action="store_true",
            help="Watch log files for real-time error monitoring",
        )
        parser.add_argument(
            "--auto-recovery",
            action="store_true",
            help="Enable automatic recovery actions",
        )
        parser.add_argument(
            "--report-interval",
            type=int,
            default=300,  # 5 minutes
            help="Report interval in seconds (default: 300)",
        )
        parser.add_argument(
            "--error-threshold",
            type=int,
            default=10,
            help="Error threshold for triggering recovery actions",
        )
        parser.add_argument(
            "--check-templates",
            action="store_true",
            help="Check all templates for errors on startup",
        )
        parser.add_argument(
            "--daemon",
            action="store_true",
            help="Run as daemon process",
        )

    def handle(self, *args, **options):
        self.auto_recovery = options["auto_recovery"]
        self.report_interval = options["report_interval"]
        self.error_threshold = options["error_threshold"]

        # Initialize error tracking
        self.error_counts = {
            "TemplateDoesNotExist": 0,
            "TemplateSyntaxError": 0,
            "NoReverseMatch": 0,
            "ImproperlyConfigured": 0,
            "ServerCrash": 0,
            "DatabaseError": 0,
        }

        self.last_report = datetime.now()

        self.stdout.write(self.style.SUCCESS("Starting Django Error Monitor"))
        self.stdout.write(f"Auto-recovery: {self.auto_recovery}")
        self.stdout.write(f"Report interval: {self.report_interval}s")
        self.stdout.write(f"Error threshold: {self.error_threshold}")

        if options["check_templates"]:
            self.check_all_templates()

        if options["watch_logs"]:
            self.watch_log_files()
        elif options["daemon"]:
            self.run_daemon()
        else:
            self.run_single_check()

    def check_all_templates(self):
        """Check all templates for errors on startup"""
        self.stdout.write("Checking all templates for errors...")

        # Use the existing validate_templates command
        from django.core.management import call_command

        try:
            call_command("validate_templates", "--strict")
            self.stdout.write(
                self.style.SUCCESS("All templates validated successfully")
            )
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Template validation failed: {e}"))
            if self.auto_recovery:
                self.recover_template_errors()

    def watch_log_files(self):
        """Watch log files for real-time error monitoring"""
        log_files = self.get_log_files()

        if not log_files:
            self.stdout.write(self.style.WARNING("No log files found to monitor"))
            return

        self.stdout.write(f"Watching {len(log_files)} log files...")

        # Start file watchers in separate threads
        threads = []
        for log_file in log_files:
            thread = threading.Thread(target=self.tail_file, args=(log_file,))
            thread.daemon = True
            thread.start()
            threads.append(thread)

        try:
            # Main monitoring loop
            while True:
                time.sleep(self.report_interval)
                self.generate_error_report()

                # Check if recovery actions are needed
                if self.auto_recovery:
                    self.check_recovery_triggers()

        except KeyboardInterrupt:
            self.stdout.write("\nStopping error monitor...")

    def run_daemon(self):
        """Run as daemon process for continuous monitoring"""
        self.stdout.write("Running in daemon mode...")

        try:
            while True:
                self.run_single_check()
                time.sleep(self.report_interval)
        except KeyboardInterrupt:
            self.stdout.write("\nDaemon stopped")

    def run_single_check(self):
        """Run a single error check cycle"""
        # Check for recent errors in logs
        recent_errors = self.scan_recent_logs()

        # Update error counts
        for error_type, count in recent_errors.items():
            self.error_counts[error_type] += count

        # Generate report if interval has passed
        if datetime.now() - self.last_report >= timedelta(seconds=self.report_interval):
            self.generate_error_report()

        # Check for recovery triggers
        if self.auto_recovery:
            self.check_recovery_triggers()

    def get_log_files(self):
        """Get list of log files to monitor"""
        logs_dir = settings.BASE_DIR / "logs"
        log_files = []

        if logs_dir.exists():
            # Monitor key log files
            for log_file in ["django.log", "errors.log", "structured.log"]:
                log_path = logs_dir / log_file
                if log_path.exists():
                    log_files.append(log_path)

        return log_files

    def tail_file(self, file_path):
        """Tail a log file and process new lines"""
        try:
            with open(file_path, "r") as f:
                # Go to end of file
                f.seek(0, 2)

                while True:
                    line = f.readline()
                    if line:
                        self.process_log_line(line.strip(), file_path)
                    else:
                        time.sleep(0.1)
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Error tailing {file_path}: {e}"))

    def process_log_line(self, line, source_file):
        """Process a single log line for error patterns"""
        try:
            # Try to parse as JSON first
            try:
                log_data = json.loads(line)
                self.process_json_log(log_data)
            except json.JSONDecodeError:
                # Process as text log
                self.process_text_log(line)

        except Exception:
            # Ignore processing errors to avoid log spam
            pass

    def process_json_log(self, log_data):
        """Process structured JSON log entry"""
        if log_data.get("level") in ["ERROR", "CRITICAL"]:
            # Check for template errors
            if "template_error_type" in log_data:
                error_type = log_data["template_error_type"]
                self.error_counts[error_type] = self.error_counts.get(error_type, 0) + 1

                if self.auto_recovery:
                    self.handle_template_error(error_type, log_data)

            # Check for server errors
            elif "server_event" in log_data:
                if log_data["server_event"] == "crash":
                    self.error_counts["ServerCrash"] += 1
                    if self.auto_recovery:
                        self.handle_server_crash(log_data)

    def process_text_log(self, line):
        """Process text-based log line"""
        line_lower = line.lower()

        # Check for error patterns from fix all.yml
        error_patterns = {
            "templatedoesnotexist": "TemplateDoesNotExist",
            "templatesyntaxerror": "TemplateSyntaxError",
            "noreversematch": "NoReverseMatch",
            "improperlyconfigured": "ImproperlyConfigured",
        }

        for pattern, error_type in error_patterns.items():
            if pattern in line_lower:
                self.error_counts[error_type] += 1
                if self.auto_recovery:
                    self.handle_error_pattern(error_type, line)
                break

    def scan_recent_logs(self):
        """Scan recent log entries for errors"""
        recent_errors = {}
        # TODO: Implement time-based filtering using report_interval

        for log_file in self.get_log_files():
            try:
                with open(log_file, "r") as f:
                    for line in f:
                        # Basic time-based filtering (simplified)
                        if "ERROR" in line or "CRITICAL" in line:
                            # Count errors (simplified pattern matching)
                            for pattern, error_type in [
                                ("TemplateDoesNotExist", "TemplateDoesNotExist"),
                                ("TemplateSyntaxError", "TemplateSyntaxError"),
                                ("NoReverseMatch", "NoReverseMatch"),
                                ("ImproperlyConfigured", "ImproperlyConfigured"),
                            ]:
                                if pattern in line:
                                    recent_errors[error_type] = (
                                        recent_errors.get(error_type, 0) + 1
                                    )

            except Exception as e:
                self.stdout.write(self.style.WARNING(f"Could not scan {log_file}: {e}"))

        return recent_errors

    def generate_error_report(self):
        """Generate error report"""
        self.stdout.write("\n" + "=" * 50)
        self.stdout.write(
            f'Error Report - {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}'
        )
        self.stdout.write("=" * 50)

        total_errors = sum(self.error_counts.values())
        self.stdout.write(f"Total errors in period: {total_errors}")

        for error_type, count in self.error_counts.items():
            if count > 0:
                status = (
                    self.style.ERROR
                    if count >= self.error_threshold
                    else self.style.WARNING
                )
                self.stdout.write(status(f"{error_type}: {count}"))

        self.last_report = datetime.now()

        # Reset counts for next period
        self.error_counts = dict.fromkeys(self.error_counts, 0)

    def check_recovery_triggers(self):
        """Check if recovery actions should be triggered"""
        for error_type, count in self.error_counts.items():
            if count >= self.error_threshold:
                self.stdout.write(
                    self.style.WARNING(
                        f"Triggering recovery for {error_type} (count: {count})"
                    )
                )
                self.trigger_recovery(error_type)

    def trigger_recovery(self, error_type):
        """Trigger recovery actions based on error type"""
        recovery_actions = {
            "TemplateDoesNotExist": self.recover_template_not_found,
            "TemplateSyntaxError": self.recover_template_syntax,
            "NoReverseMatch": self.recover_url_patterns,
            "ImproperlyConfigured": self.recover_configuration,
            "ServerCrash": self.recover_server_crash,
        }

        recovery_func = recovery_actions.get(error_type)
        if recovery_func:
            try:
                recovery_func()
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f"Recovery failed for {error_type}: {e}")
                )

    def recover_template_not_found(self):
        """Recovery action for template not found errors"""
        self.stdout.write("Executing template path recovery...")

        # Check template paths
        from django.core.management import call_command

        call_command("validate_templates", "--fix-common")

        template_error_logger.log_template_error(
            "Recovery", "system", "Template path recovery executed"
        )

    def recover_template_syntax(self):
        """Recovery action for template syntax errors"""
        self.stdout.write("Executing template syntax recovery...")

        # Auto-fix template syntax
        from django.core.management import call_command

        try:
            call_command("validate_templates", "--auto-fix")
            self.stdout.write(self.style.SUCCESS("Template auto-fix completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Template auto-fix failed: {e}"))

    def recover_url_patterns(self):
        """Recovery action for URL pattern errors"""
        self.stdout.write("Checking URL patterns...")

        # Validate URL configuration
        try:
            from django.core.management import call_command

            call_command("check", "--tag=urls")
            self.stdout.write(self.style.SUCCESS("URL patterns check completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"URL pattern check failed: {e}"))

    def recover_configuration(self):
        """Recovery action for configuration errors"""
        self.stdout.write("Validating Django configuration...")

        try:
            from django.core.management import call_command

            call_command("check")
            self.stdout.write(self.style.SUCCESS("Configuration check completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Configuration check failed: {e}"))

    def recover_server_crash(self):
        """Recovery action for server crashes"""
        self.stdout.write("Executing server crash recovery...")

        # Kill orphaned processes and restart
        try:
            from django.core.management import call_command

            call_command("manage_server", "--kill-orphans")

            server_management_logger.log_recovery(os.getpid(), time.time())

            self.stdout.write(self.style.SUCCESS("Server crash recovery completed"))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Server crash recovery failed: {e}"))

    def handle_template_error(self, error_type, log_data):
        """Handle specific template error"""
        template_name = log_data.get("template_name", "unknown")
        self.stdout.write(f"Handling template error: {error_type} in {template_name}")

    def handle_server_crash(self, log_data):
        """Handle server crash"""
        process_id = log_data.get("process_id", "unknown")
        self.stdout.write(f"Handling server crash for process: {process_id}")

    def handle_error_pattern(self, error_type, line):
        """Handle error pattern found in logs"""
        self.stdout.write(f"Found error pattern: {error_type}")
        if error_type in ["TemplateDoesNotExist", "TemplateSyntaxError"]:
            self.recover_template_errors()

    def recover_template_errors(self):
        """General template error recovery"""
        try:
            from django.core.management import call_command

            call_command("validate_templates", "--auto-fix")
        except Exception as e:
            self.stdout.write(self.style.ERROR(f"Template recovery failed: {e}"))
