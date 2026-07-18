"""
Rate Limiter for Admin API

Provides configurable rate limiting per endpoint and user
"""

import time
import functools
from collections import defaultdict
from typing import Dict, Optional, Callable
from datetime import datetime, timedelta


class RateLimiter:
    """Token bucket rate limiter."""
    
    def __init__(self):
        self.buckets = defaultdict(lambda: {
            'tokens': 0,
            'last_update': time.time(),
            'requests': []
        })
        self.limits = {}
    
    def set_limit(self, endpoint: str, requests: int, window: int):
        """
        Set rate limit for an endpoint.
        
        Args:
            endpoint: Endpoint identifier
            requests: Number of requests allowed
            window: Time window in seconds
        """
        self.limits[endpoint] = {
            'requests': requests,
            'window': window
        }
    
    def is_allowed(self, key: str, endpoint: str = 'default') -> bool:
        """
        Check if request is allowed.
        
        Args:
            key: Unique identifier (e.g., IP + user)
            endpoint: Endpoint identifier
        
        Returns:
            True if request is allowed, False otherwise
        """
        if endpoint not in self.limits:
            return True
        
        limit = self.limits[endpoint]
        now = time.time()
        bucket_key = f"{key}:{endpoint}"
        bucket = self.buckets[bucket_key]
        
        # Clean old requests
        cutoff = now - limit['window']
        bucket['requests'] = [r for r in bucket['requests'] if r > cutoff]
        
        # Check limit
        if len(bucket['requests']) >= limit['requests']:
            return False
        
        # Record request
        bucket['requests'].append(now)
        return True
    
    def get_remaining(self, key: str, endpoint: str = 'default') -> Dict:
        """Get remaining rate limit info."""
        if endpoint not in self.limits:
            return {'remaining': -1, 'reset': 0}
        
        limit = self.limits[endpoint]
        bucket_key = f"{key}:{endpoint}"
        bucket = self.buckets[bucket_key]
        
        now = time.time()
        cutoff = now - limit['window']
        valid_requests = [r for r in bucket['requests'] if r > cutoff]
        
        remaining = max(0, limit['requests'] - len(valid_requests))
        reset = int(valid_requests[0] + limit['window']) if valid_requests else int(now)
        
        return {
            'remaining': remaining,
            'limit': limit['requests'],
            'reset': reset,
            'window': limit['window']
        }


# Global rate limiter instance
rate_limiter = RateLimiter()

# Default limits
rate_limiter.set_limit('default', 100, 60)      # 100 requests per minute
rate_limiter.set_limit('login', 5, 300)         # 5 login attempts per 5 minutes
rate_limiter.set_limit('api_write', 20, 60)     # 20 write operations per minute


def rate_limit(requests: int = 100, window: int = 60, key_func: Optional[Callable] = None):
    """
    Decorator to apply rate limiting.
    
    Args:
        requests: Number of requests allowed
        window: Time window in seconds
        key_func: Function to generate rate limit key from request
    """
    def decorator(func: Callable) -> Callable:
        endpoint = func.__name__
        rate_limiter.set_limit(endpoint, requests, window)
        
        @functools.wraps(func)
        def wrapper(self, request, *args, **kwargs):
            # Generate key
            if key_func:
                key = key_func(request)
            else:
                ip = getattr(request, 'remote_addr', 'unknown')
                user = getattr(request, 'user_id', 'anonymous')
                key = f"{ip}:{user}"
            
            # Check rate limit
            if not rate_limiter.is_allowed(key, endpoint):
                from webcms.core.response import Response
                import json
                
                info = rate_limiter.get_remaining(key, endpoint)
                return Response(
                    status_code=429,
                    body=json.dumps({
                        'error': 'Rate limit exceeded',
                        'retry_after': info['reset'] - int(time.time()),
                        'limit': info['limit'],
                        'window': info['window']
                    }),
                    content_type='application/json',
                    headers={
                        'X-RateLimit-Limit': str(info['limit']),
                        'X-RateLimit-Remaining': str(info['remaining']),
                        'X-RateLimit-Reset': str(info['reset']),
                        'Retry-After': str(info['reset'] - int(time.time()))
                    }
                )
            
            # Add rate limit headers to response
            result = func(self, request, *args, **kwargs)
            
            if hasattr(result, 'headers'):
                info = rate_limiter.get_remaining(key, endpoint)
                result.headers['X-RateLimit-Limit'] = str(info['limit'])
                result.headers['X-RateLimit-Remaining'] = str(info['remaining'])
                result.headers['X-RateLimit-Reset'] = str(info['reset'])
            
            return result
        
        return wrapper
    return decorator


class SlidingWindowRateLimiter:
    """Sliding window rate limiter for more accurate limiting."""
    
    def __init__(self):
        self.windows = defaultdict(list)
    
    def is_allowed(self, key: str, limit: int, window_size: int) -> bool:
        """
        Check if request is allowed using sliding window.
        
        Args:
            key: Unique identifier
            limit: Maximum requests allowed
            window_size: Window size in seconds
        
        Returns:
            True if allowed, False otherwise
        """
        now = time.time()
        window = self.windows[key]
        
        # Remove requests outside window
        cutoff = now - window_size
        while window and window[0] < cutoff:
            window.pop(0)
        
        # Check limit
        if len(window) >= limit:
            return False
        
        # Add current request
        window.append(now)
        return True
    
    def get_window_info(self, key: str, limit: int, window_size: int) -> Dict:
        """Get sliding window info."""
        now = time.time()
        window = self.windows[key]
        cutoff = now - window_size
        
        # Clean window
        valid = [t for t in window if t > cutoff]
        
        return {
            'current': len(valid),
            'limit': limit,
            'remaining': max(0, limit - len(valid)),
            'reset': int(valid[0] + window_size) if valid else int(now + window_size)
        }


# Export
__all__ = [
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'SlidingWindowRateLimiter'
]
