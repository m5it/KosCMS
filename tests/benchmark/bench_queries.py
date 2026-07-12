#!/usr/bin/env python3
"""Performance benchmarking suite for WebCMS queries."""

import time
import asyncio
import statistics
from webcms.cache import RedisClient, CacheManager
from webcms.search.analytics import SearchAnalytics


class MockRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value

    def ping(self):
        return True


async def benchmark_cache_queries(iterations=1000):
    client = RedisClient()
    client._client = MockRedis()
    cache = CacheManager(client)

    times = []
    async def fetch():
        return {"items": []}

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        await cache.cache_query("posts", {"page": i}, fetch)
        times.append(time.perf_counter() - start)

    return {
        "operation": "cache_query",
        "iterations": iterations,
        "avg_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000
    }


async def benchmark_search_analytics(iterations=1000):
    analytics = SearchAnalytics()

    times = []
    for i in range(iterations):
        start = time.perf_counter()
        analytics.record_query(f"query {i}", i)
        times.append(time.perf_counter() - start)

    return {
        "operation": "record_query",
        "iterations": iterations,
        "avg_ms": statistics.mean(times) * 1000,
        "median_ms": statistics.median(times) * 1000,
        "min_ms": min(times) * 1000,
        "max_ms": max(times) * 1000
    }


async def main():
    print("Running performance benchmarks...")
    cache_result = await benchmark_cache_queries()
    analytics_result = await benchmark_search_analytics()

    print(f"Cache benchmark: {cache_result}")
    print(f"Analytics benchmark: {analytics_result}")


if __name__ == "__main__":
    asyncio.run(main())
