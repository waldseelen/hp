"""Logging utilities for standardized logging across the application

This module provides helper functions for consistent logging configuration
and usage throughout the application.
"""

import logging
from typing import Any, Optional

from django.conf import settings

__all__ = [
    "get_logger",
    "log_exception",
    "log_api_request",
    "log_performance",
]


def get_logger(name: str) -> logging.Logger:
    """Get a configured logger instance

    Args:
        name: Logger name (usually __name__ of the module)

    Returns:
        logging.Logger: Configured logger instance

    Examples:
        >>> logger = get_logger(__name__)
        >>> logger.info("Application started")

    Note:
        Logger configuration is inherited from Django settings.
    """
    return logging.getLogger(name)


def log_exception(
    logger: logging.Logger,
    exception: Exception,
    context: Optional[dict] = None,
    level: int = logging.ERROR,
) -> None:
    """Log an exception with context

    Args:
        logger: Logger instance to use
        exception: Exception to log
        context: Optional additional context (dict)
        level: Logging level (default: ERROR)

    Examples:
        >>> logger = get_logger(__name__)
        >>> try:
        ...     risky_operation()
        ... except Exception as e:
        ...     log_exception(logger, e, context={"user_id": 123})
    """
    exc_type = type(exception).__name__
    exc_message = str(exception)

    log_message = f"{exc_type}: {exc_message}"

    if context:
        log_message += f" | Context: {context}"

    logger.log(level, log_message, exc_info=True)


def log_api_request(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: Optional[int] = None,
    duration_ms: Optional[float] = None,
    user_id: Optional[int] = None,
) -> None:
    """Log an API request with details

    Args:
        logger: Logger instance to use
        method: HTTP method (GET, POST, etc.)
        url: Request URL or path
        status_code: Optional HTTP status code
        duration_ms: Optional request duration in milliseconds
        user_id: Optional user ID who made the request

    Examples:
        >>> logger = get_logger(__name__)
        >>> log_api_request(
        ...     logger, "GET", "/api/posts/",
        ...     status_code=200, duration_ms=45.2, user_id=123
        ... )
    """
    parts = [f"{method} {url}"]

    if status_code is not None:
        parts.append(f"status={status_code}")

    if duration_ms is not None:
        parts.append(f"duration={duration_ms:.2f}ms")

    if user_id is not None:
        parts.append(f"user={user_id}")

    log_message = " | ".join(parts)

    # Use different log levels based on status code
    if status_code and status_code >= 500:
        logger.error(log_message)
    elif status_code and status_code >= 400:
        logger.warning(log_message)
    else:
        logger.info(log_message)


def log_performance(
    logger: logging.Logger,
    operation: str,
    duration_ms: float,
    metadata: Optional[dict] = None,
    threshold_ms: float = 1000.0,
) -> None:
    """Log performance metrics for an operation

    Args:
        logger: Logger instance to use
        operation: Name of the operation
        duration_ms: Operation duration in milliseconds
        metadata: Optional additional metadata
        threshold_ms: Threshold for warning (default: 1000ms)

    Examples:
        >>> logger = get_logger(__name__)
        >>> log_performance(
        ...     logger, "database_query",
        ...     duration_ms=523.5,
        ...     metadata={"query": "SELECT * FROM posts"}
        ... )

    Note:
        Logs at WARNING level if duration exceeds threshold.
    """
    log_message = f"Performance: {operation} took {duration_ms:.2f}ms"

    if metadata:
        log_message += f" | {metadata}"

    # Warn if operation is slow
    if duration_ms > threshold_ms:
        logger.warning(log_message)
    else:
        logger.debug(log_message)
