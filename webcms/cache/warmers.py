"""
Cache warming background tasks.
"""

import asyncio
from typing import Callable, List


class CacheWarmer:
    """Manages background cache warming tasks."""

    def __init__(self, cache_manager):
        self.cache_manager = cache_manager
        self._tasks: List[Callable] = []
        self._running = False

    def register(self, task: Callable):
        """Register warming task."""
        self._tasks.append(task)

    async def warm_once(self):
        """Run all warmers once."""
        for task in self._tasks:
            try:
                await task(self.cache_manager)
            except Exception as e:
                print(f"Cache warmer error: {e}")

    async def warm_periodically(self, interval_seconds=300):
        """Run warmers in background loop."""
        self._running = True
        while self._running:
            await self.warm_once()
            await asyncio.sleep(interval_seconds)

    def stop(self):
        """Stop background warming."""
        self._running = False
