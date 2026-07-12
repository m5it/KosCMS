"""
Distributed locking with Redis.
"""

import time
import uuid
from typing import Optional


class DistributedLock:
    """Redis-based distributed lock."""

    def __init__(self, redis_client, lock_name, ttl=30, retry_delay=0.1, max_retries=100):
        self.redis = redis_client
        self.lock_name = f"lock:{lock_name}"
        self.ttl = ttl
        self.retry_delay = retry_delay
        self.max_retries = max_retries
        self.token = str(uuid.uuid4())
        self._acquired = False

    async def acquire(self) -> bool:
        """Acquire lock with retries."""
        client = self.redis.get_client()
        for _ in range(self.max_retries):
            acquired = client.set(
                self.lock_name,
                self.token,
                nx=True,
                ex=self.ttl
            )
            if acquired:
                self._acquired = True
                return True
            time.sleep(self.retry_delay)
        return False

    async def release(self):
        """Release lock if owned."""
        if not self._acquired:
            return False
        client = self.redis.get_client()
        current = client.get(self.lock_name)
        token = current.decode() if isinstance(current, bytes) else current
        if token == self.token:
            client.delete(self.lock_name)
            self._acquired = False
            return True
        return False
        return False

    async def __aenter__(self):
        await self.acquire()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        await self.release()
