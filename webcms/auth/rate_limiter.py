"""
Rate Limiter

Request rate limiting for authentication endpoints.
"""

import time
from typing import Dict, Optional, Tuple
from collections import defaultdict


class RateLimiter:
    """Simple rate limiter with Redis or memory backend."""
    
    def __init__(self, redis_client=None, 
                 max_requests: int = 100,
                 window: int = 60):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client or None for memory
            max_requests: Max requests per window
            window: Time window in seconds
        """
        self.redis = redis_client
        self.max_requests = max_requests
        self.window = window
        
        # Memory storage: {key: [(timestamp, count), ...]}
        self._memory: Dict[str, list] = defaultdict(list)
    
    def is_allowed(self, key: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed.
        
        Args:
            key: Rate limit key (e.g., IP + endpoint)
        
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()
        
        if self.redis:
            # Redis-based rate limiting
            pipe = self.redis.pipeline()
            
            # Remove old entries
            pipe.zremrangebyscore(f"ratelimit:{key}", 0, now - self.window)
            
            # Count current entries
            pipe.zcard(f"ratelimit:{key}")
            
            # Add current request
            pipe.zadd(f"ratelimit:{key}", {str(now): now})
            
            # Set expiry
            pipe.expire(f"ratelimit:{key}", self.window)
            
            results = pipe.execute()
            current_count = results[1]
        else:
            # Memory-based rate limiting
            # Clean old entries
            self._memory[key] = [
                ts for ts in self._memory[key] 
                if ts > now - self.window
            ]
            
            current_count = len(self._memory[key])
            self._memory[key].append(now)
        
        allowed = current_count <= self.max_requests
        
        info = {
            "limit": self.max_requests,
            "remaining": max(0, self.max_requests - current_count),
            "window": self.window,
            "allowed": allowed
        }
        
        return allowed, info
    
    def check_auth_attempt(self, identifier: str) -> Tuple[bool, int]:
        """
        Check authentication attempt rate.
        
        Args:
            identifier: IP address or username
        
        Returns:
            Tuple of (allowed, attempts_remaining)
        """
        key = f"auth:{identifier}"
        allowed, info = self.is_allowed(key)
        
        # Stricter limits for auth
        auth_limit = 5  # 5 attempts per window
        if info["remaining"] < (self.max_requests - auth_limit):
            return False, 0
        
        return allowed, info["remaining"]
    
    def reset(self, key: str) -> bool:
        """
        Reset rate limit for key.
        
        Args:
            key: Rate limit key
        
        Returns:
            True if reset
        """
        if self.redis:
            return self.redis.delete(f"ratelimit:{key}") > 0
        else:
            if key in self._memory:
                del self._memory[key]
                return True
            return False