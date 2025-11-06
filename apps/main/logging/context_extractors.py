"""
Log Context Extractors

Extracts various context information for structured logging.
Complexity: ≤5 per extractor
"""

import logging
from typing import Any, Dict


class LogContextExtractor:
    """Base class for context extraction"""

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract context from log record"""
        raise NotImplementedError


class ModuleContextExtractor(LogContextExtractor):
    """
    Extracts module/function/line information

    Complexity: 3
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract module context"""
        context = {}

        if hasattr(record, "module"):
            context["module"] = record.module
        if hasattr(record, "funcName"):
            context["function"] = record.funcName
        if hasattr(record, "lineno"):
            context["line_number"] = record.lineno

        return context


class ExceptionContextExtractor(LogContextExtractor):
    """
    Extracts exception information

    Complexity: 2
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract exception context"""
        import traceback

        if not record.exc_info:
            return {}

        return {
            "exception": {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": traceback.format_exception(*record.exc_info),
            }
        }


class RequestContextExtractor(LogContextExtractor):
    """
    Extracts request-related context

    Complexity: 5
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract request context"""
        context = {}

        if hasattr(record, "request_id"):
            context["request_id"] = record.request_id
        if hasattr(record, "user_id"):
            context["user_id"] = record.user_id
        if hasattr(record, "ip_address"):
            context["ip_address"] = record.ip_address
        if hasattr(record, "user_agent"):
            context["user_agent"] = record.user_agent

        return context


class PerformanceContextExtractor(LogContextExtractor):
    """
    Extracts performance metrics

    Complexity: 4
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract performance context"""
        context = {}

        if hasattr(record, "duration"):
            context["duration"] = record.duration
        if hasattr(record, "query_count"):
            context["query_count"] = record.query_count
        if hasattr(record, "cache_hits"):
            context["cache_hits"] = record.cache_hits

        return context


class TemplateContextExtractor(LogContextExtractor):
    """
    Extracts template error context

    Complexity: 4
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract template context"""
        context = {}

        if hasattr(record, "template_name"):
            context["template_name"] = record.template_name
        if hasattr(record, "template_error_type"):
            context["template_error_type"] = record.template_error_type
        if hasattr(record, "template_line"):
            context["template_line"] = record.template_line

        return context


class SecurityContextExtractor(LogContextExtractor):
    """
    Extracts security context

    Complexity: 3
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract security context"""
        context = {}

        if hasattr(record, "security_event"):
            context["security_event"] = record.security_event
        if hasattr(record, "threat_level"):
            context["threat_level"] = record.threat_level

        return context


class ServerContextExtractor(LogContextExtractor):
    """
    Extracts server management context

    Complexity: 4
    """

    def extract(self, record: logging.LogRecord) -> Dict[str, Any]:
        """Extract server context"""
        context = {}

        if hasattr(record, "server_event"):
            context["server_event"] = record.server_event
        if hasattr(record, "process_id"):
            context["process_id"] = record.process_id
        if hasattr(record, "restart_count"):
            context["restart_count"] = record.restart_count

        return context
