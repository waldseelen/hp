"""
Search Engine Components

This package contains modular search components following SOLID principles.
Complexity reduced from D:27 to B:≤6 through strategic design patterns.
"""

from .base_search_engine import SearchEngine
from .formatters.base_formatter import SearchResultFormatter
from .formatters.metadata_collector import MetadataCollector
from .formatters.url_builder import URLBuilder
from .scorers.relevance_scorer import RelevanceScorer

__all__ = [
    "SearchEngine",
    "SearchResultFormatter",
    "URLBuilder",
    "MetadataCollector",
    "RelevanceScorer",
]
