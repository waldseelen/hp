"""
Backward compatibility module for middleware.
All middleware classes have been moved to the middleware/ package.

This module re-exports them for backward compatibility.
"""

# Import all middleware from the package
from .middleware import (
    APMMiddleware,
    CacheControlMiddleware,
    CompressionMiddleware,
    DatabaseQueryTrackingMiddleware,
    PerformanceMiddleware,
    SecurityHeadersMiddleware,
    StaticOptimizationMiddleware,
)

__all__ = [
    "APMMiddleware",
    "DatabaseQueryTrackingMiddleware",
    "StaticOptimizationMiddleware",
    "CacheControlMiddleware",
    "SecurityHeadersMiddleware",
    "CompressionMiddleware",
    "PerformanceMiddleware",
]
