"""
Search Module

SQLite FTS5 integration for full-text search.
"""

from .engine import SearchEngine
from .indexer import ContentIndexer

__all__ = ["SearchEngine", "ContentIndexer"]
