"""
Main middleware package initialization.
Exports all middleware classes for easy import.
"""

# Import from submodules
from .apm_middleware import APMMiddleware, DatabaseQueryTrackingMiddleware
from .cache_security import (
    CacheControlMiddleware,
    CompressionMiddleware,
    PerformanceMiddleware,
    SecurityHeadersMiddleware,
)
from .static_optimization_middleware import StaticOptimizationMiddleware

__all__ = [
    "APMMiddleware",
    "DatabaseQueryTrackingMiddleware",
    "StaticOptimizationMiddleware",
    "CacheControlMiddleware",
    "SecurityHeadersMiddleware",
    "CompressionMiddleware",
    "PerformanceMiddleware",
]
