"""
Cache invalidation patterns for WebCMS.
"""

from typing import List


class CacheInvalidator:
    """Helper for cache invalidation patterns."""

    def __init__(self, cache_manager):
        self.cache = cache_manager

    async def invalidate_content(self, content_type: str, content_id: str):
        """Invalidate content-related cache entries."""
        patterns = [
            f"query:{content_type}:*",
            f"query:search:*",
            f"tag:{content_type}:*",
            f"content:{content_type}:{content_id}"
        ]
        total = 0
        for pattern in patterns:
            total += await self.cache.invalidate_pattern(pattern)
        return total

    async def invalidate_taxonomy(self, taxonomy_type: str, slug: str):
        """Invalidate taxonomy cache."""
        return await self.cache.invalidate_pattern(f"tag:{taxonomy_type}:{slug}:*")

    async def invalidate_user(self, user_id: str):
        """Invalidate user cache."""
        return await self.cache.invalidate_pattern(f"query:user:*") + \
               await self.cache.invalidate_pattern(f"user:{user_id}")

    async def invalidate_all(self):
        """Invalidate all cache."""
        return await self.cache.invalidate_pattern("*")

    async def invalidate_list(self, patterns: List[str]):
        """Invalidate multiple patterns."""
        total = 0
        for pattern in patterns:
            total += await self.cache.invalidate_pattern(pattern)
        return total
