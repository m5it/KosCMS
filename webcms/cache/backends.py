"""
Cache Backends

Memory and Redis cache implementations.
"""

import json
import time
from abc import ABC, abstractmethod
from typing import Any, Optional, Dict


class CacheBackend(ABC):
    """Abstract cache backend."""
    
    @abstractmethod
    def get(self, key: str) -> Optional[Any]:
        """Get value from cache."""
        pass
    
    @abstractmethod
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in cache."""
        pass
    
    @abstractmethod
    def delete(self, key: str) -> bool:
        """Delete key from cache."""
        pass
    
    @abstractmethod
    def clear(self) -> bool:
        """Clear all cache."""
        pass


class MemoryCache(CacheBackend):
    """In-memory cache with TTL."""
    
    def __init__(self):
        self._cache: Dict[str, Dict] = {}
    
    def get(self, key: str) -> Optional[Any]:
        """Get value if not expired."""
        item = self._cache.get(key)
        if item is None:
            return None
        
        if item["expires"] < time.time():
            del self._cache[key]
            return None
        
        return item["value"]
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value with expiration."""
        self._cache[key] = {
            "value": value,
            "expires": time.time() + timeout
        }
        return True
    
    def delete(self, key: str) -> bool:
        """Delete key."""
        if key in self._cache:
            del self._cache[key]
            return True
        return False
    
    def clear(self) -> bool:
        """Clear all."""
        self._cache.clear()
        return True


class RedisCache(CacheBackend):
    """Redis cache backend."""
    
    def __init__(self, redis_client):
        self.redis = redis_client
    
    def get(self, key: str) -> Optional[Any]:
        """Get from Redis."""
        try:
            data = self.redis.get(key)
            if data:
                return json.loads(data.decode())
            return None
        except Exception:
            return None
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set in Redis."""
        try:
            self.redis.setex(key, timeout, json.dumps(value))
            return True
        except Exception:
            return False
    
    def delete(self, key: str) -> bool:
        """Delete from Redis."""
        try:
            return self.redis.delete(key) > 0
        except Exception:
            return False
    
    def clear(self) -> bool:
        """Clear Redis cache."""
        try:
            self.redis.flushdb()
            return True
        except Exception:
            return False