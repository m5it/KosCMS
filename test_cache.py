#!/usr/bin/env python3
"""Test Redis cache system (mock)"""

import sys
import asyncio
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from unittest.mock import MagicMock
from webcms.cache import RedisClient, CacheManager, DistributedLock, RedisSessionStore, CacheAnalytics


class MockRedis:
    def __init__(self):
        self.data = {}

    def get(self, key):
        return self.data.get(key)

    def setex(self, key, ttl, value):
        self.data[key] = value

    def set(self, key, value, nx=False, ex=None):
        if nx and key in self.data:
            return None
        self.data[key] = value
        return True

    def delete(self, *keys):
        count = 0
        for key in keys:
            if key in self.data:
                del self.data[key]
                count += 1
        return count

    def keys(self, pattern):
        import fnmatch
        return [k.encode() for k in self.data if fnmatch.fnmatch(k, pattern)]

    def incr(self, key):
        self.data[key] = str(int(self.data.get(key, 0)) + 1)

    def incrby(self, key, amount):
        self.data[key] = str(int(self.data.get(key, 0)) + amount)

    def ping(self):
        return True


def test_cache():
    print('Testing cache system with mock Redis...')

    mock_redis = MockRedis()
    client = RedisClient()
    client._client = mock_redis

    cache = CacheManager(client)
    analytics = CacheAnalytics(client)
    cache.set_analytics(analytics)

    asyncio.run(cache.set("key1", {"value": 123}, ttl=60))
    result = asyncio.run(cache.get("key1"))
    print(f'Cache set/get: {result}')

    lock = DistributedLock(client, "test-lock")
    acquired = asyncio.run(lock.acquire())
    print(f'Distributed lock acquired: {acquired}')
    asyncio.run(lock.release())

    session_store = RedisSessionStore(client)
    sid = session_store.create_session({"user_id": "1"})
    session = session_store.get_session(sid)
    print(f'Session storage: {session}')

    stats = analytics.get_stats()
    print(f'Analytics stats: {stats}')

    print('Cache system verified!')


if __name__ == '__main__':
    test_cache()
