"""
Log Aggregation and Analysis System
==================================

Centralized log processing, aggregation, and analysis utilities
for efficient log management and alerting.
"""

import gzip
import json
import logging
import re
import threading
from collections import Counter, defaultdict
from dataclasses import dataclass
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, Iterator, List, Optional

from django.conf import settings
from django.core.cache import cache
from django.utils import timezone


@dataclass
class LogEntry:
    """Structured log entry data class"""

    timestamp: datetime
    level: str
    logger: str
    message: str
    service: str
    environment: str
    trace_id: Optional[str] = None
    request_id: Optional[str] = None
    source: Optional[Dict[str, Any]] = None
    exception: Optional[Dict[str, Any]] = None
    extra: Optional[Dict[str, Any]] = None
    django: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    security: Optional[Dict[str, Any]] = None


@dataclass
class LogStats:
    """Log statistics data class"""

    total_entries: int
    by_level: Dict[str, int]
    by_logger: Dict[str, int]
    error_count: int
    warning_count: int
    time_range: Dict[str, datetime]
    top_errors: List[Dict[str, Any]]
    performance_issues: List[Dict[str, Any]]
    security_events: List[Dict[str, Any]]


class LogAggregator:
    """
    Centralized log aggregation and analysis system
    """

    def __init__(self):
        from django.conf import settings

        base_dir = getattr(
            settings, "BASE_DIR", Path(__file__).resolve().parent.parent.parent.parent
        )
        self.log_directory = Path(base_dir) / "logs"
        self.cache_timeout = 300  # 5 minutes
        self.alert_thresholds = {
            "error_rate_per_minute": 10,
            "critical_errors_per_hour": 5,
            "warning_rate_per_minute": 50,
            "performance_issues_per_hour": 20,
        }
        self._lock = threading.Lock()

    def parse_log_file(self, file_path: Path) -> Iterator[LogEntry]:
        """Parse log file and yield structured log entries"""
        try:
            # Handle gzipped files
            if file_path.suffix == ".gz":
                open_func = gzip.open
                mode = "rt"
            else:
                open_func = open
                mode = "r"

            with open_func(file_path, mode, encoding="utf-8", errors="ignore") as f:
                for line_num, line in enumerate(f, 1):
                    try:
                        # Try to parse as JSON first
                        if line.strip().startswith("{"):
                            log_data = json.loads(line.strip())
                            yield self._json_to_log_entry(log_data)
                        else:
                            # Parse traditional log format
                            yield self._parse_traditional_log(
                                line, file_path.name, line_num
                            )
                    except (json.JSONDecodeError, ValueError) as e:
                        # Log parsing error
                        logging.getLogger(__name__).warning(
                            f"Failed to parse log line {line_num} in {file_path}: {e}"
                        )
                        continue

        except Exception as e:
            logging.getLogger(__name__).error(
                f"Failed to read log file {file_path}: {e}"
            )

    def _json_to_log_entry(self, log_data: Dict[str, Any]) -> LogEntry:
        """Convert JSON log data to LogEntry object"""
        timestamp_str = log_data.get("timestamp", "")
        try:
            # Handle different timestamp formats
            if timestamp_str.endswith("Z"):
                timestamp = datetime.fromisoformat(timestamp_str[:-1])
            else:
                timestamp = datetime.fromisoformat(timestamp_str)
        except ValueError:
            timestamp = datetime.now()

        return LogEntry(
            timestamp=timestamp,
            level=log_data.get("level", "INFO"),
            logger=log_data.get("logger", "unknown"),
            message=log_data.get("message", ""),
            service=log_data.get("service", "unknown"),
            environment=log_data.get("environment", "unknown"),
            trace_id=log_data.get("trace_id"),
            request_id=log_data.get("request_id"),
            source=log_data.get("source"),
            exception=log_data.get("exception"),
            extra=log_data.get("extra"),
            django=log_data.get("django"),
            performance=log_data.get("performance"),
            security=log_data.get("security"),
        )

    def _parse_traditional_log(
        self, line: str, filename: str, line_num: int
    ) -> LogEntry:
        """Parse traditional log format"""
        # Basic regex pattern for Django log format
        pattern = r"(\w+)\s+(\d{4}-\d{2}-\d{2}\s+\d{2}:\d{2}:\d{2},\d+)\s+(\w+)\s+(\d+)\s+(\d+)\s+(.*)"
        match = re.match(pattern, line.strip())

        if match:
            level, timestamp_str, module, process_id, thread_id, message = (
                match.groups()
            )
            try:
                timestamp = datetime.strptime(timestamp_str, "%Y-%m-%d %H:%M:%S,%f")
            except ValueError:
                timestamp = datetime.now()
        else:
            # Fallback parsing
            level = "INFO"
            timestamp = datetime.now()
            message = line.strip()
            module = filename

        return LogEntry(
            timestamp=timestamp,
            level=level,
            logger=module,
            message=message,
            service="portfolio_site",
            environment=getattr(settings, "ENVIRONMENT", "development"),
            source={"filename": filename, "line": line_num},
        )

    def aggregate_logs(self, hours_back: int = 24) -> LogStats:  # noqa: C901
        """Aggregate logs from the specified time period"""
        cache_key = f"log_stats_{hours_back}h"
        cached_stats = cache.get(cache_key)
        if cached_stats:
            return LogStats(**cached_stats)

        with self._lock:
            end_time = datetime.now()
            start_time = end_time - timedelta(hours=hours_back)

            stats = {
                "total_entries": 0,
                "by_level": defaultdict(int),
                "by_logger": defaultdict(int),
                "error_count": 0,
                "warning_count": 0,
                "time_range": {"start": start_time, "end": end_time},
                "top_errors": [],
                "performance_issues": [],
                "security_events": [],
            }

            error_messages = Counter()
            performance_issues = []
            security_events = []

            # Process all log files
            for log_file in self._get_log_files():
                try:
                    for entry in self.parse_log_file(log_file):
                        # Filter by time range
                        if not (start_time <= entry.timestamp <= end_time):
                            continue

                        stats["total_entries"] += 1
                        stats["by_level"][entry.level] += 1
                        stats["by_logger"][entry.logger] += 1

                        # Count errors and warnings
                        if entry.level == "ERROR":
                            stats["error_count"] += 1
                            error_messages[entry.message] += 1

                        elif entry.level == "WARNING":
                            stats["warning_count"] += 1

                        # Collect performance issues
                        if entry.performance:
                            performance_issues.append(
                                {
                                    "timestamp": entry.timestamp.isoformat(),
                                    "message": entry.message,
                                    "performance": entry.performance,
                                    "trace_id": entry.trace_id,
                                }
                            )

                        # Collect security events
                        if entry.security:
                            security_events.append(
                                {
                                    "timestamp": entry.timestamp.isoformat(),
                                    "message": entry.message,
                                    "security": entry.security,
                                    "trace_id": entry.trace_id,
                                }
                            )

                except Exception as e:
                    logging.getLogger(__name__).error(
                        f"Error processing log file {log_file}: {e}"
                    )

            # Process top errors
            stats["top_errors"] = [
                {"message": message, "count": count}
                for message, count in error_messages.most_common(10)
            ]

            # Sort performance issues by severity
            stats["performance_issues"] = sorted(
                performance_issues,
                key=lambda x: x.get("performance", {}).get("response_time", 0),
                reverse=True,
            )[:20]

            # Recent security events
            stats["security_events"] = sorted(
                security_events, key=lambda x: x["timestamp"], reverse=True
            )[:20]

            # Convert defaultdicts to regular dicts
            stats["by_level"] = dict(stats["by_level"])
            stats["by_logger"] = dict(stats["by_logger"])

            # Cache results
            cache.set(cache_key, stats, self.cache_timeout)

            return LogStats(**stats)

    def _get_log_files(self) -> List[Path]:
        """Get all log files sorted by modification time"""
        log_files = []

        # Find all log files
        patterns = ["*.log", "*.log.*", "*.log.gz"]
        for pattern in patterns:
            log_files.extend(self.log_directory.glob(pattern))

        # Sort by modification time (newest first)
        log_files.sort(key=lambda f: f.stat().st_mtime, reverse=True)

        return log_files

    def search_logs(
        self,
        query: str,
        level: str = None,
        logger: str = None,
        hours_back: int = 24,
        limit: int = 100,
    ) -> List[LogEntry]:
        """Search logs with filters"""
        results = []
        end_time = datetime.now()
        start_time = end_time - timedelta(hours=hours_back)

        for log_file in self._get_log_files():
            if len(results) >= limit:
                break

            for entry in self.parse_log_file(log_file):
                if len(results) >= limit:
                    break

                # Time filter
                if not (start_time <= entry.timestamp <= end_time):
                    continue

                # Level filter
                if level and entry.level != level:
                    continue

                # Logger filter
                if logger and entry.logger != logger:
                    continue

                # Text search
                if query and query.lower() not in entry.message.lower():
                    continue

                results.append(entry)

        return results

    def check_alert_conditions(self) -> List[Dict[str, Any]]:
        """Check for alert conditions based on log patterns"""
        alerts = []
        stats = self.aggregate_logs(hours_back=1)  # Last hour

        # Error rate alerts
        error_rate = stats.error_count
        if error_rate > self.alert_thresholds["error_rate_per_minute"]:
            alerts.append(
                {
                    "type": "high_error_rate",
                    "severity": "warning",
                    "message": f"High error rate detected: {error_rate} errors in the last hour",
                    "metrics": {
                        "error_count": error_rate,
                        "threshold": self.alert_thresholds["error_rate_per_minute"],
                    },
                    "timestamp": timezone.now().isoformat(),
                }
            )

        # Critical error alerts
        critical_count = stats.by_level.get("CRITICAL", 0)
        if critical_count > self.alert_thresholds["critical_errors_per_hour"]:
            alerts.append(
                {
                    "type": "critical_errors",
                    "severity": "critical",
                    "message": f"Critical errors detected: {critical_count} in the last hour",
                    "metrics": {
                        "critical_count": critical_count,
                        "threshold": self.alert_thresholds["critical_errors_per_hour"],
                    },
                    "timestamp": timezone.now().isoformat(),
                }
            )

        # Performance issues
        if (
            len(stats.performance_issues)
            > self.alert_thresholds["performance_issues_per_hour"]
        ):
            alerts.append(
                {
                    "type": "performance_degradation",
                    "severity": "warning",
                    "message": f"Performance issues detected: {len(stats.performance_issues)} slow operations",
                    "metrics": {
                        "issue_count": len(stats.performance_issues),
                        "threshold": self.alert_thresholds[
                            "performance_issues_per_hour"
                        ],
                    },
                    "timestamp": timezone.now().isoformat(),
                }
            )

        # Security events
        if stats.security_events:
            alerts.append(
                {
                    "type": "security_events",
                    "severity": "warning",
                    "message": f"Security events detected: {len(stats.security_events)} events",
                    "metrics": {"event_count": len(stats.security_events)},
                    "timestamp": timezone.now().isoformat(),
                }
            )

        return alerts

    def generate_report(self, hours_back: int = 24) -> Dict[str, Any]:
        """Generate comprehensive log analysis report"""
        stats = self.aggregate_logs(hours_back)
        alerts = self.check_alert_conditions()

        return {
            "report_generated": timezone.now().isoformat(),
            "time_period": f"{hours_back} hours",
            "summary": {
                "total_log_entries": stats.total_entries,
                "error_count": stats.error_count,
                "warning_count": stats.warning_count,
                "error_rate": round(
                    (stats.error_count / max(stats.total_entries, 1)) * 100, 2
                ),
            },
            "breakdown": {
                "by_level": stats.by_level,
                "by_logger": stats.by_logger,
            },
            "top_errors": stats.top_errors,
            "performance_issues": stats.performance_issues[:5],  # Top 5
            "security_events": stats.security_events[:5],  # Recent 5
            "alerts": alerts,
            "recommendations": self._generate_recommendations(stats, alerts),
        }

    def _generate_recommendations(
        self, stats: LogStats, alerts: List[Dict[str, Any]]
    ) -> List[str]:
        """Generate recommendations based on log analysis"""
        recommendations = []

        # Error rate recommendations
        if stats.error_count > 0:
            error_rate = (stats.error_count / max(stats.total_entries, 1)) * 100
            if error_rate > 5:
                recommendations.append(
                    f"High error rate ({error_rate:.1f}%) - investigate top errors"
                )

        # Performance recommendations
        if len(stats.performance_issues) > 10:
            recommendations.append(
                "Multiple performance issues detected - consider optimization"
            )

        # Security recommendations
        if stats.security_events:
            recommendations.append(
                "Security events detected - review authentication and authorization logs"
            )

        # Log volume recommendations
        if stats.total_entries > 100000:  # 100k entries
            recommendations.append(
                "High log volume - consider implementing log sampling or filtering"
            )

        return recommendations


# Global log aggregator instance
log_aggregator = LogAggregator()
