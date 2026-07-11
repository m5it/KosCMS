"""
FTS5 Search Engine

Provides full-text search using SQLite FTS5.
"""

import sqlite3
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class SearchResult:
    """Search result item."""
    content_id: str
    content_type: str
    title: str
    excerpt: str
    rank: float


class SearchEngine:
    """FTS5 search engine."""
    
    def __init__(self, db_path: str = "webcms_search.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """Initialize FTS5 table."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("""
                CREATE VIRTUAL TABLE IF NOT EXISTS search_index USING fts5(
                    content_id,
                    content_type,
                    title,
                    content,
                    excerpt,
                    tokenize='porter'
                )
            """)
            conn.commit()
    
    def index_document(self, content_id: str, content_type: str,
                      title: str, content: str, excerpt: str = "") -> bool:
        """Index a document."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                # Delete existing entry if present
                conn.execute(
                    "DELETE FROM search_index WHERE content_id = ?",
                    (content_id,)
                )
                # Insert new document
                conn.execute("""
                    INSERT INTO search_index (content_id, content_type, title, content, excerpt)
                    VALUES (?, ?, ?, ?, ?)
                """, (content_id, content_type, title, content, excerpt))
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def remove_document(self, content_id: str) -> bool:
        """Remove document from index."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute(
                    "DELETE FROM search_index WHERE content_id = ?",
                    (content_id,)
                )
                conn.commit()
                return True
        except sqlite3.Error:
            return False
    
    def search(self, query: str, limit: int = 20) -> List[SearchResult]:
        """Search documents."""
        with sqlite3.connect(self.db_path) as conn:
            cursor = conn.execute("""
                SELECT content_id, content_type, title, excerpt, rank
                FROM search_index
                WHERE search_index MATCH ?
                ORDER BY rank
                LIMIT ?
            """, (query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(SearchResult(
                    content_id=row[0],
                    content_type=row[1],
                    title=row[2],
                    excerpt=row[3],
                    rank=row[4]
                ))
            return results
    
    def clear_index(self):
        """Clear all indexed documents."""
        with sqlite3.connect(self.db_path) as conn:
            conn.execute("DELETE FROM search_index")
            conn.commit()
