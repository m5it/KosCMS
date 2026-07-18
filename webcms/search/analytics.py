"""
Search analytics and suggestions tracking with KosDB persistence.
"""

import json
from datetime import datetime, timedelta
from collections import defaultdict
from typing import Dict, List, Optional, Any


class SearchAnalytics:
    """Track search queries and popular terms with KosDB persistence."""

    def __init__(self, db=None):
        self.db = db
        self._queries = []
        self._clicks = defaultdict(int)
        self._popular = defaultdict(int)
        self._suggestions = []
        self._ensure_tables()
        self._load_from_kosdb()

    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods

    def _ensure_tables(self):
        """Ensure search tables exist."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
        except Exception:
            tables = []

        # Search queries table
        if 'search_queries' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE search_queries (
                        id TEXT PRIMARY KEY,
                        query TEXT,
                        result_count INTEGER,
                        filters TEXT,
                        timestamp TEXT,
                        user_id TEXT
                    )
                """)
            except Exception:
                pass

        # Search suggestions table
        if 'search_suggestions' not in tables:
            try:
                self.db.execute("""
                    CREATE TABLE search_suggestions (
                        id TEXT PRIMARY KEY,
                        query TEXT,
                        count INTEGER DEFAULT 0,
                        is_active TEXT DEFAULT '1',
                        created_at TEXT,
                        updated_at TEXT
                    )
                """)
            except Exception:
                pass

    def _load_from_kosdb(self):
        """Load data from KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            # Load queries from last 24 hours
            yesterday = (datetime.utcnow() - timedelta(days=1)).isoformat()
            result = self.db.query(f"SELECT * FROM search_queries WHERE timestamp > '{yesterday}'")
            for row in result.get('rows', []):
                self._queries.append({
                    "query": row['query'],
                    "result_count": int(row.get('result_count', 0)),
                    "filters": json.loads(row['filters']) if row.get('filters') else {},
                    "timestamp": row['timestamp']
                })
                self._popular[row['query'].lower()] += 1

            # Load active suggestions
            result = self.db.query("SELECT * FROM search_suggestions WHERE is_active='1'")
            for row in result.get('rows', []):
                self._suggestions.append({
                    "id": row['id'],
                    "query": row['query'],
                    "count": int(row.get('count', 0))
                })
        except Exception:
            pass

    def _save_query_to_kosdb(self, query_data: Dict):
        """Save query to KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            import uuid
            query_id = str(uuid.uuid4())
            filters = json.dumps(query_data.get('filters', {}))
            self.db.execute(f"""
                INSERT INTO search_queries 
                (id, query, result_count, filters, timestamp, user_id)
                VALUES (
                    '{query_id}',
                    '{query_data['query']}',
                    {query_data.get('result_count', 0)},
                    '{filters}',
                    '{query_data['timestamp']}',
                    '{query_data.get('user_id', '')}'
                )
            """)
        except Exception:
            pass

    def record_query(self, query_text, result_count, filters=None, user_id=None):
        """Record search query."""
        query_data = {
            "query": query_text,
            "result_count": result_count,
            "filters": filters or {},
            "timestamp": datetime.utcnow().isoformat(),
            "user_id": user_id
        }
        self._queries.append(query_data)
        self._popular[query_text.lower()] += 1
        self._save_query_to_kosdb(query_data)

    def record_click(self, query_text, doc_id):
        """Record search result click."""
        self._clicks[doc_id] += 1

    def get_popular_queries(self, limit=10):
        """Get most popular queries."""
        return sorted(
            [{"query": k, "count": v} for k, v in self._popular.items()],
            key=lambda x: x["count"],
            reverse=True
        )[:limit]

    def get_recent_queries(self, limit=20):
        """Get recent queries."""
        return self._queries[-limit:]

    def get_suggestions(self, prefix, limit=5):
        """Get query suggestions based on prefix."""
        prefix = prefix.lower()
        matches = [
            {"query": query, "count": count}
            for query, count in self._popular.items()
            if query.startswith(prefix)
        ]
        return sorted(matches, key=lambda x: x["count"], reverse=True)[:limit]

    def list_suggestions(self) -> List[Dict[str, Any]]:
        """List all search suggestions."""
        # Try KosDB first
        if self.db and self._is_kosdb():
            try:
                result = self.db.query("SELECT * FROM search_suggestions WHERE is_active='1' ORDER BY count DESC")
                return [
                    {
                        "id": row['id'],
                        "query": row['query'],
                        "count": int(row.get('count', 0)),
                        "created_at": row.get('created_at')
                    }
                    for row in result.get('rows', [])
                ]
            except Exception:
                pass
        
        # Return in-memory suggestions
        return self._suggestions

    def add_suggestion(self, query: str) -> Dict[str, Any]:
        """Add search suggestion."""
        import uuid
        suggestion_id = str(uuid.uuid4())
        suggestion = {
            "id": suggestion_id,
            "query": query,
            "count": 1,
            "created_at": datetime.utcnow().isoformat()
        }
        self._suggestions.append(suggestion)
        
        # Save to KosDB
        if self.db and self._is_kosdb():
            try:
                now = datetime.utcnow().isoformat()
                self.db.execute(f"""
                    INSERT INTO search_suggestions 
                    (id, query, count, is_active, created_at, updated_at)
                    VALUES (
                        '{suggestion_id}',
                        '{query}',
                        1,
                        '1',
                        '{now}',
                        '{now}'
                    )
                """)
            except Exception:
                pass
        
        return suggestion

    def delete_suggestion(self, suggestion_id: str) -> bool:
        """Delete search suggestion."""
        # Remove from memory
        self._suggestions = [s for s in self._suggestions if s.get('id') != suggestion_id]
        
        # Remove from KosDB
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"DELETE FROM search_suggestions WHERE id='{suggestion_id}'")
                return True
            except Exception:
                pass
        
        return True

    def get_stats(self):
        """Get search analytics stats."""
        return {
            "total_queries": len(self._queries),
            "unique_queries": len(self._popular),
            "total_clicks": sum(self._clicks.values()),
            "popular_queries": self.get_popular_queries(),
            "recent_queries": self.get_recent_queries(5)
        }

    def queries_24h(self) -> int:
        """Get queries in last 24 hours."""
        yesterday = datetime.utcnow() - timedelta(days=1)
        count = 0
        for q in self._queries:
            try:
                query_time = datetime.fromisoformat(q['timestamp'])
                if query_time > yesterday:
                    count += 1
            except Exception:
                continue
        return count

    def top_query(self) -> Optional[str]:
        """Get top query."""
        if not self._popular:
            return None
        return max(self._popular.items(), key=lambda x: x[1])[0]

    def no_results_rate(self) -> float:
        """Calculate no results rate."""
        if not self._queries:
            return 0.0
        no_results = sum(1 for q in self._queries if q.get('result_count', 0) == 0)
        return round(no_results / len(self._queries), 4)

    def avg_time_ms(self) -> int:
        """Get average query time (placeholder)."""
        return 45  # Placeholder value
