"""
Cache manager with warming and invalidation patterns.
"""

import json
import hashlib
import asyncio
from typing import Optional, Any, Callable, List
from datetime import timedelta


class CacheManager:
    """Manages Redis-backed caching."""

    def __init__(self, redis_client, default_ttl=300):
        self.redis = redis_client
        self.default_ttl = default_ttl
        self._warmers: List[Callable] = []
        self._analytics = None

    def set_analytics(self, analytics):
        """Attach analytics tracker."""
        self._analytics = analytics

    async def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        try:
            data = self.redis.get_client().get(key)
            if data:
                if self._analytics:
                    await self._analytics.record_hit()
                return json.loads(data)
            if self._analytics:
                await self._analytics.record_miss()
            return None
        except Exception:
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set value in cache."""
        try:
            serialized = json.dumps(value, default=str)
            self.redis.get_client().setex(
                key,
                ttl or self.default_ttl,
                serialized
            )
            return True
        except Exception:
            return False

    async def delete(self, key: str):
        """Delete cache key."""
        try:
            self.redis.get_client().delete(key)
            return True
        except Exception:
            return False

    async def invalidate_pattern(self, pattern: str):
        """Invalidate keys matching pattern."""
        try:
            client = self.redis.get_client()
            keys = client.keys(pattern)
            if keys:
                client.delete(*keys)
            return len(keys)
        except Exception:
            return 0

    async def invalidate_tag(self, tag: str):
        """Invalidate by cache tag."""
        return await self.invalidate_pattern(f"tag:{tag}:*")

    def _make_query_key(self, query_name: str, params: dict) -> str:
        """Create cache key for query result."""
        param_hash = hashlib.sha256(
            json.dumps(params, sort_keys=True, default=str).encode()
        ).hexdigest()[:16]
        return f"query:{query_name}:{param_hash}"

    async def cache_query(self, query_name: str, params: dict,
                          fetch_func: Callable, ttl: Optional[int] = None):
        """Cache query result with optional warming."""
        key = self._make_query_key(query_name, params)
        cached = await self.get(key)
        if cached is not None:
            return cached

        result = await fetch_func()
        await self.set(key, result, ttl)
        return result

    def register_warmer(self, warmer: Callable):
        """Register cache warming function."""
        self._warmers.append(warmer)

    async def warm_cache(self):
        """Run all cache warmers."""
        results = []
        for warmer in self._warmers:
            try:
                result = await warmer(self)
                results.append(result)
            except Exception as e:
                results.append({"error": str(e)})
        return results
