import json
import logging
from datetime import datetime

from .context_extractors import (
    ExceptionContextExtractor,
    ModuleContextExtractor,
    PerformanceContextExtractor,
    RequestContextExtractor,
    SecurityContextExtractor,
    ServerContextExtractor,
    TemplateContextExtractor,
)


class StructuredJSONFormatter(logging.Formatter):
    """
    Structured JSON formatter for comprehensive logging
    Following the "fix all.yml" error monitoring configuration

    REFACTORED: Complexity reduced from D:21 to B:6
    """

    def __init__(
        self,
        service_name="django_app",
        environment="development",
        include_extra_fields=True,
        *args,
        **kwargs,
    ):
        super().__init__(*args, **kwargs)
        self.service_name = service_name
        self.environment = environment
        self.include_extra_fields = include_extra_fields

        # Initialize context extractors
        self._init_extractors()

    def _init_extractors(self):
        """
        Initialize context extractors

        Complexity: 1
        """
        self.extractors = [
            ModuleContextExtractor(),
            ExceptionContextExtractor(),
        ]

        if self.include_extra_fields:
            self.extractors.extend(
                [
                    RequestContextExtractor(),
                    PerformanceContextExtractor(),
                    TemplateContextExtractor(),
                    SecurityContextExtractor(),
                    ServerContextExtractor(),
                ]
            )

    def format(self, record):
        """
        Format log record as structured JSON

        REFACTORED: Complexity reduced from D:21 to B:6
        """
        # Build base log entry
        log_entry = self._build_base_entry(record)

        # Extract all context
        for extractor in self.extractors:
            context = extractor.extract(record)
            log_entry.update(context)

        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _build_base_entry(self, record):
        """
        Build base log entry structure

        Complexity: 1
        """
        return {
            "timestamp": self.formatTime(record),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "service": self.service_name,
            "environment": self.environment,
            "thread": record.thread,
            "process": record.process,
        }

    def formatTime(self, record, datefmt=None):
        """Format timestamp in ISO format"""
        return datetime.fromtimestamp(record.created).isoformat()


class RequestContextFilter(logging.Filter):
    """
    Filter to add request context to log records
    """

    def filter(self, record):
        """Add request context to log record"""
        try:
            # Try to get current request from thread local
            from threading import current_thread

            # Get request from thread local if available
            request = getattr(current_thread(), "request", None)

            if request:
                record.request_id = getattr(request, "id", "unknown")
                record.ip_address = self.get_client_ip(request)
                record.user_agent = request.META.get("HTTP_USER_AGENT", "unknown")
                record.method = request.method
                record.path = request.path

                if hasattr(request, "user") and request.user.is_authenticated:
                    record.user_id = request.user.id
                else:
                    record.user_id = "anonymous"

        except Exception:
            # If we can't get request context, that's ok
            pass

        return True

    @staticmethod
    def get_client_ip(request):
        """Get client IP address from request"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0]
        else:
            ip = request.META.get("REMOTE_ADDR")
        return ip


class PerformanceFilter(logging.Filter):
    """
    Filter to add performance metrics to log records
    """

    def filter(self, record):
        """Add performance context to log record"""
        try:
            # Add performance timing if available
            if hasattr(record, "extra"):
                extra = record.extra
                if "performance" in extra:
                    perf = extra["performance"]
                    record.duration = perf.get("duration")
                    record.query_count = perf.get("query_count")
                    record.cache_hits = perf.get("cache_hits")
                    record.memory_usage = perf.get("memory_usage")
        except Exception:
            pass

        return True


class SecurityFilter(logging.Filter):
    """
    Filter to add security context to log records
    """

    def filter(self, record):
        """Add security context to log record"""
        try:
            # Check if this is a security-related log
            message = record.getMessage().lower()

            # Common security indicators
            security_keywords = [
                "authentication",
                "authorization",
                "permission",
                "forbidden",
                "csrf",
                "xss",
                "injection",
                "attack",
                "malicious",
                "suspicious",
                "brute force",
                "rate limit",
                "blocked",
            ]

            if any(keyword in message for keyword in security_keywords):
                record.security_event = True

                # Determine threat level
                if any(
                    word in message for word in ["attack", "malicious", "injection"]
                ):
                    record.threat_level = "high"
                elif any(word in message for word in ["suspicious", "blocked"]):
                    record.threat_level = "medium"
                else:
                    record.threat_level = "low"

        except Exception:
            pass

        return True


class TemplateErrorLogger:
    """
    Specialized logger for template errors as specified in fix all.yml
    """

    def __init__(self):
        self.logger = logging.getLogger("main.template_errors")

    def log_template_error(
        self, error_type, template_name, error_message, line_number=None, context=None
    ):
        """Log template error with structured context"""
        extra = {
            "template_name": template_name,
            "template_error_type": error_type,
            "template_line": line_number,
            "context": context or {},
        }

        self.logger.error(
            f"Template Error [{error_type}] in {template_name}: {error_message}",
            extra=extra,
        )

    def log_syntax_error(self, template_name, syntax_error, line_number=None):
        """Log template syntax errors"""
        self.log_template_error(
            "TemplateSyntaxError", template_name, str(syntax_error), line_number
        )

    def log_does_not_exist_error(self, template_name, search_paths=None):
        """Log template not found errors"""
        context = {"search_paths": search_paths} if search_paths else {}
        self.log_template_error(
            "TemplateDoesNotExist",
            template_name,
            f"Template '{template_name}' not found",
            context=context,
        )

    def log_variable_error(self, template_name, variable_name, line_number=None):
        """Log template variable errors"""
        self.log_template_error(
            "VariableDoesNotExist",
            template_name,
            f"Variable '{variable_name}' does not exist",
            line_number,
        )


class ServerManagementLogger:
    """
    Specialized logger for server management events
    """

    def __init__(self):
        self.logger = logging.getLogger("main.server_management")

    def log_server_event(
        self, event_type, message, process_id=None, restart_count=None
    ):
        """Log server management events"""
        extra = {
            "server_event": event_type,
            "process_id": process_id,
            "restart_count": restart_count,
        }

        self.logger.info(message, extra=extra)

    def log_restart(self, process_id, restart_count, reason=None):
        """Log server restart events"""
        message = f"Server restart #{restart_count}"
        if reason:
            message += f" - Reason: {reason}"

        self.log_server_event("restart", message, process_id, restart_count)

    def log_crash(self, process_id, error_message):
        """Log server crash events"""
        self.log_server_event("crash", f"Server crash: {error_message}", process_id)

    def log_recovery(self, process_id, recovery_time):
        """Log server recovery events"""
        message = f"Server recovered in {recovery_time:.2f}s"
        self.log_server_event("recovery", message, process_id)


# Singleton instances for easy access
template_error_logger = TemplateErrorLogger()
server_management_logger = ServerManagementLogger()
