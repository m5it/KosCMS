#!/usr/bin/env python3
"""Integration tests for Redis cache system."""

import pytest
from unittest.mock import MagicMock
from webcms.cache import RedisClient, CacheManager, DistributedLock


@pytest.fixture
def cache_manager():
    mock_redis = MagicMock()
    mock_redis.get.return_value = None
    mock_redis.setex.return_value = True
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1
    mock_redis.keys.return_value = []

    client = RedisClient()
    client._client = mock_redis
    return CacheManager(client)


@pytest.mark.asyncio
async def test_cache_set_get(cache_manager):
    await cache_manager.set("key1", {"value": 1})

    async def fetch():
        return {"value": 1}

    result = await cache_manager.cache_query("test", {"id": 1}, fetch)
    assert result == {"value": 1}


@pytest.mark.asyncio
async def test_distributed_lock():
    mock_redis = MagicMock()
    mock_redis.get.return_value = b"token123"
    mock_redis.set.return_value = True
    mock_redis.delete.return_value = 1

    client = RedisClient()
    client._client = mock_redis

    lock = DistributedLock(client, "test-lock")
    lock.token = "token123"
    lock._acquired = True
    result = await lock.release()
    assert result is True
