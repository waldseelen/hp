"""
Search Engine Components

This package contains modular search components following SOLID principles.
Complexity reduced from D:27 to B:≤6 through strategic design patterns.
"""

from .base_search_engine import SearchEngine, search_engine
from .formatters.base_formatter import SearchResultFormatter
from .formatters.metadata_collector import MetadataCollector
from .formatters.url_builder import URLBuilder
from .scorers.relevance_scorer import RelevanceScorer

__all__ = [
    "SearchEngine",
    "search_engine",
    "SearchResultFormatter",
    "URLBuilder",
    "MetadataCollector",
    "RelevanceScorer",
]
