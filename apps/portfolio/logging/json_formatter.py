"""
Advanced JSON Logging Formatter
==============================

Structured JSON logging formatter for centralized log aggregation
with enhanced metadata and search capabilities.
"""

import json
import logging
import traceback
import uuid
from datetime import datetime
from typing import Any, Dict, Optional

from django.conf import settings


class StructuredJSONFormatter(logging.Formatter):
    """
    Advanced JSON formatter for structured logging with enhanced metadata
    """

    def __init__(self, *args, **kwargs):
        self.include_extra_fields = kwargs.pop("include_extra_fields", True)
        self.service_name = kwargs.pop(
            "service_name", getattr(settings, "SERVICE_NAME", "portfolio_site")
        )
        self.environment = kwargs.pop(
            "environment", getattr(settings, "ENVIRONMENT", "development")
        )
        super().__init__(*args, **kwargs)

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        # Base log structure
        log_entry = {
            # Core fields
            "timestamp": datetime.utcfromtimestamp(record.created).isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            # Service identification
            "service": self.service_name,
            "environment": self.environment,
            "version": getattr(settings, "APP_VERSION", "1.0.0"),
            # Request/trace context
            "trace_id": self._get_trace_id(record),
            "request_id": self._get_request_id(record),
            # Source location
            "source": {
                "module": record.module,
                "filename": record.filename,
                "function": record.funcName,
                "line": record.lineno,
                "pathname": record.pathname,
            },
            # Process information
            "process": {
                "pid": record.process,
                "thread": record.thread,
                "thread_name": record.threadName,
            },
        }

        # Add exception information if present
        if record.exc_info:
            log_entry["exception"] = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": self.formatException(record.exc_info),
                "stack_trace": traceback.format_exception(*record.exc_info),
            }

        # Add extra fields from record
        if self.include_extra_fields:
            extra_fields = self._extract_extra_fields(record)
            if extra_fields:
                log_entry["extra"] = extra_fields

        # Add Django-specific context
        django_context = self._get_django_context(record)
        if django_context:
            log_entry["django"] = django_context

        # Add performance metrics if available
        performance_data = self._get_performance_data(record)
        if performance_data:
            log_entry["performance"] = performance_data

        # Add security context for security-related logs
        security_context = self._get_security_context(record)
        if security_context:
            log_entry["security"] = security_context

        return json.dumps(log_entry, ensure_ascii=False, default=str)

    def _extract_extra_fields(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract additional fields from log record"""
        # Fields to exclude from extra
        reserved_fields = {
            "name",
            "msg",
            "args",
            "levelname",
            "levelno",
            "pathname",
            "filename",
            "module",
            "exc_info",
            "exc_text",
            "stack_info",
            "lineno",
            "funcName",
            "created",
            "msecs",
            "relativeCreated",
            "thread",
            "threadName",
            "processName",
            "process",
            "getMessage",
            "message",
        }

        extra = {}
        for key, value in record.__dict__.items():
            if key not in reserved_fields and not key.startswith("_"):
                extra[key] = value

        return extra

    def _get_trace_id(self, record: logging.LogRecord) -> Optional[str]:
        """Extract trace ID from Sentry or custom context"""
        # Try to get Sentry trace ID
        try:
            import sentry_sdk

            with sentry_sdk.configure_scope() as scope:
                if scope.transaction:
                    return scope.transaction.trace_id
        except Exception:
            # Sentry may not be configured
            pass

        # Try to get from record extra fields
        return getattr(record, "trace_id", None)

    def _get_request_id(self, record: logging.LogRecord) -> Optional[str]:
        """Extract request ID from context"""
        # Check record extra fields first
        request_id = getattr(record, "request_id", None)
        if request_id:
            return request_id

        # Try to get from Django request
        try:
            from django.core.context_processors import request

            if hasattr(request, "META"):
                return request.META.get("HTTP_X_REQUEST_ID")
        except Exception:
            pass

        return None

    def _get_django_context(
        self, record: logging.LogRecord
    ) -> Optional[Dict[str, Any]]:
        """Extract Django-specific context"""
        context = {}

        # Request information
        request_data = getattr(record, "request", None)
        if request_data:
            if isinstance(request_data, dict):
                context["request"] = request_data
            else:
                # Try to extract from Django request object
                try:
                    context["request"] = {
                        "method": getattr(request_data, "method", None),
                        "path": getattr(request_data, "path", None),
                        "user": str(getattr(request_data, "user", None)),
                        "remote_addr": (
                            request_data.META.get("REMOTE_ADDR")
                            if hasattr(request_data, "META")
                            else None
                        ),
                    }
                except Exception:
                    pass

        # User information
        user_data = getattr(record, "user", None)
        if user_data:
            context["user"] = user_data

        # Database query information
        if hasattr(record, "query_count") or hasattr(record, "query_time"):
            context["database"] = {
                "query_count": getattr(record, "query_count", None),
                "query_time": getattr(record, "query_time", None),
            }

        return context if context else None

    def _get_performance_data(
        self, record: logging.LogRecord
    ) -> Optional[Dict[str, Any]]:
        """Extract performance-related data"""
        performance = {}

        # Response time
        if hasattr(record, "response_time"):
            performance["response_time"] = record.response_time

        # Execution time
        if hasattr(record, "execution_time"):
            performance["execution_time"] = record.execution_time

        # Memory usage
        if hasattr(record, "memory_usage"):
            performance["memory_usage"] = record.memory_usage

        # Cache hit/miss
        if hasattr(record, "cache_hit"):
            performance["cache_hit"] = record.cache_hit

        # Database metrics
        if hasattr(record, "db_queries"):
            performance["db_queries"] = record.db_queries

        return performance if performance else None

    def _get_security_context(
        self, record: logging.LogRecord
    ) -> Optional[Dict[str, Any]]:
        """Extract security-related context"""
        security = {}

        # Security event type
        if hasattr(record, "security_event"):
            security["event_type"] = record.security_event

        # IP address
        if hasattr(record, "ip_address"):
            security["ip_address"] = record.ip_address

        # User agent
        if hasattr(record, "user_agent"):
            security["user_agent"] = record.user_agent

        # Session ID
        if hasattr(record, "session_id"):
            security["session_id"] = record.session_id

        # Authentication failure details
        if hasattr(record, "auth_failure_reason"):
            security["auth_failure_reason"] = record.auth_failure_reason

        return security if security else None


class RequestContextFilter(logging.Filter):
    """
    Filter to add request context to log records
    """

    def filter(self, record):
        # Try to get current request from thread local
        try:
            pass

            # This is a placeholder - in real implementation you'd use
            # threading.local() to store request context
        except Exception:
            pass

        # Add request ID if not present
        if not hasattr(record, "request_id"):
            record.request_id = str(uuid.uuid4())[:8]

        return True


class PerformanceFilter(logging.Filter):
    """
    Filter to add performance metrics to log records
    """

    def filter(self, record):
        # Add performance tags
        if record.levelname in ["ERROR", "CRITICAL"]:
            record.performance_impact = "high"
        elif record.levelname == "WARNING":
            record.performance_impact = "medium"
        else:
            record.performance_impact = "low"

        return True


class SecurityFilter(logging.Filter):
    """
    Filter to identify and tag security-related log entries
    """

    SECURITY_KEYWORDS = [
        "authentication",
        "authorization",
        "login",
        "logout",
        "permission",
        "csrf",
        "xss",
        "sql injection",
        "brute force",
        "unauthorized",
        "forbidden",
        "access denied",
        "security",
        "breach",
        "intrusion",
    ]

    def filter(self, record):
        message = record.getMessage().lower()

        # Check if this is a security-related log
        is_security_log = any(keyword in message for keyword in self.SECURITY_KEYWORDS)

        if is_security_log:
            record.log_category = "security"
            record.requires_attention = True

        # Tag authentication events
        if "login" in message or "authentication" in message:
            record.security_event = "authentication"

        # Tag authorization events
        if "permission" in message or "authorization" in message:
            record.security_event = "authorization"

        return True
