"""
Cache analytics dashboard data.
"""

import asyncio
from datetime import datetime, timedelta


class CacheAnalytics:
    """Track and report cache performance."""

    def __init__(self, redis_client):
        self.redis = redis_client
        self._hits = 0
        self._misses = 0
        self._invalidations = 0

    async def record_hit(self):
        self._hits += 1
        self.redis.get_client().incr("analytics:cache:hits")

    async def record_miss(self):
        self._misses += 1
        self.redis.get_client().incr("analytics:cache:misses")

    async def record_invalidation(self, count=1):
        self._invalidations += count
        self.redis.get_client().incrby("analytics:cache:invalidations", count)

    def get_stats(self) -> dict:
        """Get cache statistics."""
        client = self.redis.get_client()
        hits = int(client.get("analytics:cache:hits") or 0) + self._hits
        misses = int(client.get("analytics:cache:misses") or 0) + self._misses
        invalidations = int(client.get("analytics:cache:invalidations") or 0) + self._invalidations

        total = hits + misses
        hit_rate = hits / total if total > 0 else 0

        return {
            "hits": hits,
            "misses": misses,
            "invalidations": invalidations,
            "hit_rate": round(hit_rate, 4),
            "total_requests": total,
            "timestamp": datetime.utcnow().isoformat()
        }

    def get_dashboard_data(self) -> dict:
        """Get data for analytics dashboard."""
        return {
            "stats": self.get_stats(),
            "memory": self._get_memory_info(),
            "top_keys": self._get_top_keys()
        }

    def _get_memory_info(self) -> dict:
        try:
            info = self.redis.get_client().info("memory")
            return {
                "used_memory": info.get("used_memory", 0),
                "used_memory_human": info.get("used_memory_human", "0B"),
                "maxmemory": info.get("maxmemory", 0)
            }
        except Exception:
            return {}

    def _get_top_keys(self, count=10) -> list:
        try:
            client = self.redis.get_client()
            keys = client.keys("query:*")[:count]
            return [k.decode() for k in keys]
        except Exception:
            return []
