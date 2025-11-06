"""
Test mocks for external dependencies

This package provides mock implementations of external services
to allow tests to run without real infrastructure dependencies.

Available mocks:
- MockMeilisearchClient: Mock for Meilisearch search engine
- MockRedisClient: Mock for Redis cache/queue
- MockCeleryApp: Mock for Celery task queue
"""

from .celery_mock import MockCeleryApp
from .meilisearch_mock import MockMeilisearchClient
from .redis_mock import MockRedisClient

__all__ = [
    "MockMeilisearchClient",
    "MockRedisClient",
    "MockCeleryApp",
]
