"""
Advanced Performance Monitoring (APM) Middleware
===============================================

Custom middleware for enhanced transaction tracking and distributed tracing
with Sentry APM integration.
"""

import logging
import time
from typing import Callable, Optional

from django.conf import settings
from django.http import HttpRequest, HttpResponse
from django.utils.deprecation import MiddlewareMixin

try:
    from sentry_sdk import set_context, set_tag, start_transaction

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger("main.performance")


class APMMiddleware(MiddlewareMixin):
    """
    Advanced Performance Monitoring middleware for custom transaction tracking
    """

    def __init__(self, get_response: Callable):
        super().__init__(get_response)
        self.get_response = get_response

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Start custom transaction tracking"""
        if not SENTRY_AVAILABLE:
            return None

        # Start timing
        request._apm_start_time = time.time()

        # Create custom transaction name based on URL pattern
        transaction_name = self._get_transaction_name(request)

        # Start Sentry transaction with custom context
        transaction = start_transaction(
            name=transaction_name,
            op="http.server",
            description=f"{request.method} {request.path}",
        )

        # Add custom tags and context
        set_tag("http.method", request.method)
        set_tag("http.path", request.path)
        set_tag(
            "user.authenticated",
            request.user.is_authenticated if hasattr(request, "user") else False,
        )

        # Add request context
        set_context(
            "request",
            {
                "url": request.build_absolute_uri(),
                "method": request.method,
                "headers": dict(request.headers),
                "query_params": dict(request.GET),
                "user_agent": request.META.get("HTTP_USER_AGENT", ""),
                "remote_addr": self._get_client_ip(request),
            },
        )

        # Store transaction in request for later use
        request._apm_transaction = transaction

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Complete transaction tracking and add performance metrics"""
        if not SENTRY_AVAILABLE or not hasattr(request, "_apm_transaction"):
            return response

        # Calculate response time
        if hasattr(request, "_apm_start_time"):
            response_time = time.time() - request._apm_start_time

            # Add response context
            set_context(
                "response",
                {
                    "status_code": response.status_code,
                    "content_type": response.get("Content-Type", ""),
                    "content_length": (
                        len(response.content) if hasattr(response, "content") else 0
                    ),
                    "response_time_ms": round(response_time * 1000, 2),
                },
            )

            # Add performance tags
            set_tag("http.status_code", response.status_code)
            set_tag("performance.response_time_ms", round(response_time * 1000, 2))

            # Check performance budgets
            self._check_performance_budgets(request, response, response_time)

            # Log performance metrics
            logger.info(
                f"APM Transaction: {request.method} {request.path} "
                f"- {response.status_code} - {response_time:.3f}s",
                extra={
                    "transaction_name": getattr(
                        request, "_apm_transaction_name", "unknown"
                    ),
                    "method": request.method,
                    "path": request.path,
                    "status_code": response.status_code,
                    "response_time": response_time,
                    "content_length": (
                        len(response.content) if hasattr(response, "content") else 0
                    ),
                },
            )

        # Finish the transaction
        request._apm_transaction.finish()

        return response

    def process_exception(
        self, request: HttpRequest, exception: Exception
    ) -> Optional[HttpResponse]:
        """Handle exceptions in transaction tracking"""
        if SENTRY_AVAILABLE and hasattr(request, "_apm_transaction"):
            # Add exception context
            set_context(
                "exception",
                {
                    "type": type(exception).__name__,
                    "message": str(exception),
                    "module": exception.__class__.__module__,
                },
            )

            # Add error tags
            set_tag("error", True)
            set_tag("exception.type", type(exception).__name__)

            # Finish transaction with error
            request._apm_transaction.finish()

        return None

    def _get_transaction_name(self, request: HttpRequest) -> str:
        """Generate a meaningful transaction name"""
        # Try to get URL pattern name if available
        if hasattr(request, "resolver_match") and request.resolver_match:
            if request.resolver_match.url_name:
                namespace = request.resolver_match.namespace
                url_name = request.resolver_match.url_name
                if namespace:
                    transaction_name = f"{namespace}:{url_name}"
                else:
                    transaction_name = url_name
            else:
                transaction_name = f"{request.method} {request.resolver_match.route}"
        else:
            # Fallback to path with parameter normalization
            path = request.path
            # Normalize common patterns
            import re

            path = re.sub(r"/\d+/", "/{id}/", path)  # Replace numeric IDs
            path = re.sub(r"/[a-f0-9-]{36}/", "/{uuid}/", path)  # Replace UUIDs
            transaction_name = f"{request.method} {path}"

        # Store for later use
        request._apm_transaction_name = transaction_name
        return transaction_name

    def _get_client_ip(self, request: HttpRequest) -> str:
        """Get client IP address considering proxies"""
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            ip = x_forwarded_for.split(",")[0].strip()
        else:
            ip = request.META.get("REMOTE_ADDR", "")
        return ip

    def _check_performance_budgets(
        self, request: HttpRequest, response: HttpResponse, response_time: float
    ):
        """Check if response time exceeds performance budgets"""
        if not hasattr(settings, "PERFORMANCE_BUDGETS"):
            return

        budgets = settings.PERFORMANCE_BUDGETS

        # Check API response threshold
        if request.path.startswith("/api/"):
            threshold = budgets.get("API_RESPONSE_THRESHOLD", 1.0)
            if response_time > threshold:
                set_tag("budget_exceeded", "api_slow")
                logger.warning(
                    f"API response time exceeded budget: {response_time:.3f}s > {threshold}s",
                    extra={
                        "path": request.path,
                        "response_time": response_time,
                        "threshold": threshold,
                        "budget_type": "api_response",
                    },
                )

        # Check general slow transaction threshold
        slow_threshold = budgets.get("SLOW_TRANSACTION_THRESHOLD", 2.0)
        very_slow_threshold = budgets.get("VERY_SLOW_THRESHOLD", 5.0)

        if response_time > very_slow_threshold:
            set_tag("performance_issue", "very_slow")
            set_tag("budget_exceeded", "critical")
        elif response_time > slow_threshold:
            set_tag("performance_issue", "slow")
            set_tag("budget_exceeded", "warning")


class DatabaseQueryTrackingMiddleware(MiddlewareMixin):
    """
    Middleware to track database query performance
    """

    def process_request(self, request: HttpRequest) -> Optional[HttpResponse]:
        """Initialize query tracking"""
        if (
            SENTRY_AVAILABLE
            and hasattr(settings, "PERFORMANCE_MONITORING")
            and settings.PERFORMANCE_MONITORING.get("TRACK_SQL_QUERIES", False)
        ):
            from django.db import connection

            request._apm_initial_queries = len(connection.queries)
            request._apm_query_start_time = time.time()

        return None

    def process_response(
        self, request: HttpRequest, response: HttpResponse
    ) -> HttpResponse:
        """Track database query metrics"""
        if (
            SENTRY_AVAILABLE
            and hasattr(request, "_apm_initial_queries")
            and hasattr(request, "_apm_query_start_time")
        ):

            from django.db import connection

            query_count = len(connection.queries) - request._apm_initial_queries
            query_time = sum(
                float(query["time"])
                for query in connection.queries[request._apm_initial_queries :]
            )

            # Add database context
            set_context(
                "database",
                {
                    "query_count": query_count,
                    "query_time_ms": round(query_time * 1000, 2),
                    "queries": (
                        connection.queries[request._apm_initial_queries :]
                        if settings.DEBUG
                        else []
                    ),
                },
            )

            # Add database performance tags
            set_tag("db.query_count", query_count)
            set_tag("db.query_time_ms", round(query_time * 1000, 2))

            # Check database performance budgets
            if hasattr(settings, "PERFORMANCE_BUDGETS"):
                db_threshold = settings.PERFORMANCE_BUDGETS.get(
                    "DATABASE_QUERY_THRESHOLD", 0.1
                )
                if query_time > db_threshold:
                    set_tag("db.slow_queries", True)
                    set_tag("budget_exceeded", "db_slow")

            # Log database metrics
            logger.info(
                f"Database metrics: {query_count} queries in {query_time:.3f}s",
                extra={
                    "query_count": query_count,
                    "query_time": query_time,
                    "path": request.path,
                },
            )

        return response
