"""
Search analytics and suggestions tracking.
"""

from datetime import datetime
from collections import defaultdict


class SearchAnalytics:
    """Track search queries and popular terms."""

    def __init__(self):
        self._queries = []
        self._clicks = defaultdict(int)
        self._popular = defaultdict(int)

    def record_query(self, query_text, result_count, filters=None):
        """Record search query."""
        self._queries.append({
            "query": query_text,
            "result_count": result_count,
            "filters": filters or {},
            "timestamp": datetime.utcnow().isoformat()
        })
        self._popular[query_text.lower()] += 1

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

    def get_stats(self):
        """Get search analytics stats."""
        return {
            "total_queries": len(self._queries),
            "unique_queries": len(self._popular),
            "total_clicks": sum(self._clicks.values()),
            "popular_queries": self.get_popular_queries(),
            "recent_queries": self.get_recent_queries(5)
        }
