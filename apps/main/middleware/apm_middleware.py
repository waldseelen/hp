"""
APM (Application Performance Monitoring) Middleware

Provides transaction tracking and database query monitoring for performance analysis.
"""

import logging
import time

from django.conf import settings
from django.db import connection
from django.utils.deprecation import MiddlewareMixin

logger = logging.getLogger("apm")


class APMMiddleware(MiddlewareMixin):
    """
    APM transaction tracking middleware.

    Monitors request/response cycles and logs slow transactions
    based on PERFORMANCE_BUDGETS configuration.
    """

    def process_request(self, request):
        """Start transaction tracking"""
        request._apm_start_time = time.time()
        request._apm_transaction_name = f"{request.method} {request.path}"
        return None

    def process_response(self, request, response):
        """End transaction tracking and log if needed"""
        if not hasattr(request, "_apm_start_time"):
            return response

        duration = time.time() - request._apm_start_time
        transaction_name = getattr(request, "_apm_transaction_name", "unknown")

        # Get performance budgets from settings
        perf_budgets = getattr(settings, "PERFORMANCE_BUDGETS", {})
        slow_threshold = perf_budgets.get("SLOW_TRANSACTION_THRESHOLD", 2.0)
        very_slow_threshold = perf_budgets.get("VERY_SLOW_THRESHOLD", 5.0)

        # Add transaction header
        response["X-Transaction-Time"] = f"{duration:.3f}s"

        # Log very slow transactions
        if duration > very_slow_threshold:
            logger.error(
                f"VERY SLOW TRANSACTION: {transaction_name} took {duration:.3f}s "
                f"(threshold: {very_slow_threshold}s)",
                extra={
                    "transaction": transaction_name,
                    "duration": duration,
                    "threshold": very_slow_threshold,
                    "level": "critical",
                },
            )
        # Log slow transactions
        elif duration > slow_threshold:
            logger.warning(
                f"Slow transaction: {transaction_name} took {duration:.3f}s "
                f"(threshold: {slow_threshold}s)",
                extra={
                    "transaction": transaction_name,
                    "duration": duration,
                    "threshold": slow_threshold,
                    "level": "warning",
                },
            )

        return response


class DatabaseQueryTrackingMiddleware(MiddlewareMixin):
    """
    Database query tracking middleware.

    Monitors database queries per request and logs slow queries
    based on PERFORMANCE_BUDGETS configuration.
    """

    def process_request(self, request):
        """Reset query tracking"""
        # Store initial query count
        request._db_query_start_count = len(connection.queries)
        return None

    def process_response(self, request, response):
        """Track database queries and log if needed"""
        if not hasattr(request, "_db_query_start_count"):
            return response

        # Calculate queries executed in this request
        queries = connection.queries[request._db_query_start_count :]
        query_count = len(queries)

        # Calculate total query time
        total_query_time = sum(float(q.get("time", 0)) for q in queries)

        # Get performance budgets from settings
        perf_budgets = getattr(settings, "PERFORMANCE_BUDGETS", {})
        db_threshold = perf_budgets.get("DATABASE_QUERY_THRESHOLD", 0.1)

        # Add query metrics to response headers
        response["X-DB-Query-Count"] = str(query_count)
        response["X-DB-Query-Time"] = f"{total_query_time:.3f}s"

        # Log excessive query count
        if query_count > 50:
            logger.warning(
                f"High query count: {request.method} {request.path} "
                f"executed {query_count} queries",
                extra={
                    "path": request.path,
                    "method": request.method,
                    "query_count": query_count,
                    "total_time": total_query_time,
                },
            )

        # Log slow queries
        slow_queries = [q for q in queries if float(q.get("time", 0)) > db_threshold]
        if slow_queries:
            for query in slow_queries:
                query_time = float(query.get("time", 0))
                logger.warning(
                    f'Slow database query ({query_time:.3f}s): {query.get("sql", "")[:100]}...',
                    extra={
                        "query_time": query_time,
                        "threshold": db_threshold,
                        "sql": query.get("sql", "")[:500],
                    },
                )

        return response
