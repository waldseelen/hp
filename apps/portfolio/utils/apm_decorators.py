"""
APM Decorators for Custom Transaction and Span Tracking
=======================================================

Decorators and utilities for distributed tracing and performance monitoring.
"""

import functools
import logging
import time
from typing import Any, Callable, Dict

from django.conf import settings

try:
    from sentry_sdk import set_context, set_tag, start_span

    SENTRY_AVAILABLE = True
except ImportError:
    SENTRY_AVAILABLE = False

logger = logging.getLogger("main.performance")


def trace_function(
    operation_name: str = None, description: str = None, tags: Dict[str, Any] = None
):
    """
    Decorator to trace function execution with Sentry APM

    Args:
        operation_name: Custom operation name for the span
        description: Description of the operation
        tags: Additional tags to add to the span
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE:
                return func(*args, **kwargs)

            # Generate operation name if not provided
            op_name = operation_name or f"{func.__module__}.{func.__name__}"
            desc = description or f"Function: {func.__name__}"

            # Start span
            with start_span(op=op_name, description=desc) as _span:  # noqa: F841
                # Add function context
                set_context(
                    "function",
                    {
                        "name": func.__name__,
                        "module": func.__module__,
                        "args_count": len(args),
                        "kwargs_keys": list(kwargs.keys()),
                    },
                )

                # Add custom tags
                if tags:
                    for key, value in tags.items():
                        set_tag(key, value)

                # Add function-specific tags
                set_tag("function.name", func.__name__)
                set_tag("function.module", func.__module__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Add performance metrics
                    set_tag(
                        "performance.execution_time_ms", round(execution_time * 1000, 2)
                    )

                    # Log performance
                    logger.debug(
                        f"Function {func.__name__} executed in {execution_time:.3f}s",
                        extra={
                            "function_name": func.__name__,
                            "function_module": func.__module__,
                            "execution_time": execution_time,
                        },
                    )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    # Add error context
                    set_tag("error", True)
                    set_tag("exception.type", type(e).__name__)
                    set_context(
                        "exception",
                        {
                            "type": type(e).__name__,
                            "message": str(e),
                            "execution_time": execution_time,
                        },
                    )

                    logger.error(
                        f"Function {func.__name__} failed after {execution_time:.3f}s: {e}",
                        extra={
                            "function_name": func.__name__,
                            "function_module": func.__module__,
                            "execution_time": execution_time,
                            "error_message": str(e),
                        },
                    )

                    raise

        return wrapper

    return decorator


def trace_database_operation(operation_type: str = "database"):
    """
    Decorator specifically for database operations
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE:
                return func(*args, **kwargs)

            with start_span(
                op=f"db.{operation_type}",
                description=f"Database {operation_type}: {func.__name__}",
            ) as _span:  # noqa: F841
                # Track database queries
                from django.db import connection

                initial_queries = len(connection.queries)

                set_tag("db.operation", operation_type)
                set_tag("function.name", func.__name__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Calculate database metrics
                    query_count = len(connection.queries) - initial_queries
                    query_time = sum(
                        float(q["time"]) for q in connection.queries[initial_queries:]
                    )

                    # Add database performance context
                    set_context(
                        "database_operation",
                        {
                            "query_count": query_count,
                            "query_time_ms": round(query_time * 1000, 2),
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "operation_type": operation_type,
                        },
                    )

                    set_tag("db.query_count", query_count)
                    set_tag("db.query_time_ms", round(query_time * 1000, 2))

                    # Check performance budgets
                    if hasattr(settings, "PERFORMANCE_BUDGETS"):
                        db_threshold = settings.PERFORMANCE_BUDGETS.get(
                            "DATABASE_QUERY_THRESHOLD", 0.1
                        )
                        if query_time > db_threshold:
                            set_tag("budget_exceeded", "db_slow")
                            logger.warning(
                                f"Database operation {func.__name__} exceeded budget: {query_time:.3f}s > {db_threshold}s",
                                extra={
                                    "function_name": func.__name__,
                                    "operation_type": operation_type,
                                    "query_time": query_time,
                                    "query_count": query_count,
                                    "threshold": db_threshold,
                                },
                            )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time
                    query_count = len(connection.queries) - initial_queries

                    set_tag("error", True)
                    set_tag("db.query_count", query_count)
                    set_context(
                        "database_error",
                        {
                            "operation_type": operation_type,
                            "query_count": query_count,
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "error": str(e),
                        },
                    )

                    raise

        return wrapper

    return decorator


def trace_cache_operation(operation_type: str = "cache"):
    """
    Decorator for cache operations
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE:
                return func(*args, **kwargs)

            with start_span(
                op=f"cache.{operation_type}",
                description=f"Cache {operation_type}: {func.__name__}",
            ) as _span:  # noqa: F841
                set_tag("cache.operation", operation_type)
                set_tag("function.name", func.__name__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Add cache performance context
                    set_context(
                        "cache_operation",
                        {
                            "operation_type": operation_type,
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "cache_hit": (
                                getattr(result, "cache_hit", None)
                                if hasattr(result, "cache_hit")
                                else None
                            ),
                        },
                    )

                    set_tag("cache.execution_time_ms", round(execution_time * 1000, 2))

                    # Check cache performance budgets
                    if hasattr(settings, "PERFORMANCE_BUDGETS"):
                        cache_threshold = settings.PERFORMANCE_BUDGETS.get(
                            "CACHE_OPERATION_THRESHOLD", 0.05
                        )
                        if execution_time > cache_threshold:
                            set_tag("budget_exceeded", "cache_slow")
                            logger.warning(
                                f"Cache operation {func.__name__} exceeded budget: {execution_time:.3f}s > {cache_threshold}s",
                                extra={
                                    "function_name": func.__name__,
                                    "operation_type": operation_type,
                                    "execution_time": execution_time,
                                    "threshold": cache_threshold,
                                },
                            )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    set_tag("error", True)
                    set_context(
                        "cache_error",
                        {
                            "operation_type": operation_type,
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "error": str(e),
                        },
                    )

                    raise

        return wrapper

    return decorator


def trace_api_call(service_name: str, endpoint: str = None):
    """
    Decorator for external API calls
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            if not SENTRY_AVAILABLE:
                return func(*args, **kwargs)

            endpoint_name = endpoint or func.__name__

            with start_span(
                op="http.client",
                description=f"API call to {service_name}: {endpoint_name}",
            ) as _span:  # noqa: F841
                set_tag("http.service", service_name)
                set_tag("http.endpoint", endpoint_name)
                set_tag("function.name", func.__name__)

                start_time = time.time()
                try:
                    result = func(*args, **kwargs)
                    execution_time = time.time() - start_time

                    # Try to extract response information if available
                    status_code = None
                    response_size = None

                    if hasattr(result, "status_code"):
                        status_code = result.status_code
                        set_tag("http.status_code", status_code)

                    if hasattr(result, "content"):
                        response_size = len(result.content)
                        set_tag("http.response_size", response_size)

                    # Add API call context
                    set_context(
                        "api_call",
                        {
                            "service": service_name,
                            "endpoint": endpoint_name,
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "status_code": status_code,
                            "response_size": response_size,
                        },
                    )

                    set_tag("api.execution_time_ms", round(execution_time * 1000, 2))

                    # Check API performance budgets
                    if hasattr(settings, "PERFORMANCE_BUDGETS"):
                        api_threshold = settings.PERFORMANCE_BUDGETS.get(
                            "API_RESPONSE_THRESHOLD", 1.0
                        )
                        if execution_time > api_threshold:
                            set_tag("budget_exceeded", "api_slow")
                            logger.warning(
                                f"API call to {service_name} exceeded budget: {execution_time:.3f}s > {api_threshold}s",
                                extra={
                                    "service": service_name,
                                    "endpoint": endpoint_name,
                                    "execution_time": execution_time,
                                    "threshold": api_threshold,
                                    "status_code": status_code,
                                },
                            )

                    return result

                except Exception as e:
                    execution_time = time.time() - start_time

                    set_tag("error", True)
                    set_tag("exception.type", type(e).__name__)
                    set_context(
                        "api_error",
                        {
                            "service": service_name,
                            "endpoint": endpoint_name,
                            "execution_time_ms": round(execution_time * 1000, 2),
                            "error": str(e),
                        },
                    )

                    logger.error(
                        f"API call to {service_name} failed after {execution_time:.3f}s: {e}",
                        extra={
                            "service": service_name,
                            "endpoint": endpoint_name,
                            "execution_time": execution_time,
                            "error": str(e),
                        },
                    )

                    raise

        return wrapper

    return decorator


class APMContext:
    """
    Context manager for custom transaction tracking
    """

    def __init__(
        self, operation_name: str, description: str = None, tags: Dict[str, Any] = None
    ):
        self.operation_name = operation_name
        self.description = description
        self.tags = tags or {}
        self.span = None
        self.start_time = None

    def __enter__(self):
        if SENTRY_AVAILABLE:
            self.span = start_span(op=self.operation_name, description=self.description)
            self.span.__enter__()

            # Add custom tags
            for key, value in self.tags.items():
                set_tag(key, value)

        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        execution_time = time.time() - self.start_time

        if SENTRY_AVAILABLE and self.span:
            # Add execution time
            set_tag("execution_time_ms", round(execution_time * 1000, 2))

            if exc_type:
                set_tag("error", True)
                set_tag("exception.type", exc_type.__name__)
                set_context(
                    "exception",
                    {
                        "type": exc_type.__name__,
                        "message": str(exc_val),
                        "execution_time_ms": round(execution_time * 1000, 2),
                    },
                )

            self.span.__exit__(exc_type, exc_val, exc_tb)

        # Log performance
        if exc_type:
            logger.error(
                f"Operation {self.operation_name} failed after {execution_time:.3f}s: {exc_val}",
                extra={
                    "operation": self.operation_name,
                    "execution_time": execution_time,
                    "error": str(exc_val),
                },
            )
        else:
            logger.debug(
                f"Operation {self.operation_name} completed in {execution_time:.3f}s",
                extra={
                    "operation": self.operation_name,
                    "execution_time": execution_time,
                },
            )


# Convenience function for creating APM contexts
def trace_operation(operation_name: str, description: str = None, **tags):
    """
    Create an APM context for tracing operations

    Usage:
        with trace_operation("custom_operation", description="My operation", user_id=123):
            # Your code here
            pass
    """
    return APMContext(operation_name, description, tags)
