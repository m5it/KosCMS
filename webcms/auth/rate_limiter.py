"""
Rate Limiter

Request rate limiting with endpoint-specific rules.
"""

import time
import re
from typing import Dict, Optional, Tuple, List, Callable
from collections import defaultdict
from dataclasses import dataclass, field
from functools import wraps


@dataclass
class RateLimitRule:
    """Rate limit rule for endpoint patterns."""
    
    name: str
    pattern: str  # Regex pattern to match endpoints
    requests_per_minute: int = 60
    burst_size: int = 10  # Allow burst of requests
    window: int = 60  # Time window in seconds
    
    def matches(self, endpoint: str) -> bool:
        """Check if endpoint matches this rule."""
        return bool(re.match(self.pattern, endpoint))
    
    def to_dict(self) -> Dict:
        """Convert to dictionary."""
        return {
            "name": self.name,
            "pattern": self.pattern,
            "requests_per_minute": self.requests_per_minute,
            "burst_size": self.burst_size,
            "window": self.window
        }


class RateLimiter:
    """Advanced rate limiter with endpoint-specific rules."""
    
    def __init__(self, redis_client=None):
        """
        Initialize rate limiter.
        
        Args:
            redis_client: Redis client or None for memory
        """
        self.redis = redis_client
        self.rules: Dict[str, RateLimitRule] = {}
        self._memory: Dict[str, Dict] = defaultdict(lambda: {
            "tokens": 0,
            "last_update": 0,
            "count": 0
        })
        
        # Default rules
        self._register_default_rules()
    
    def _register_default_rules(self):
        """Register default rate limit rules."""
        # General API
        self.add_rule(RateLimitRule(
            name="default",
            pattern=r"^/api/v1/.*",
            requests_per_minute=60,
            burst_size=10
        ))
        
        # Auth endpoints - stricter limits
        self.add_rule(RateLimitRule(
            name="auth",
            pattern=r"^/api/v1/auth/.*",
            requests_per_minute=10,
            burst_size=3
        ))
        
        # Login specifically
        self.add_rule(RateLimitRule(
            name="login",
            pattern=r"^/api/v1/auth/login",
            requests_per_minute=5,
            burst_size=2
        ))
        
        # Admin endpoints
        self.add_rule(RateLimitRule(
            name="admin",
            pattern=r"^/api/v1/admin/.*",
            requests_per_minute=30,
            burst_size=5
        ))
        
        # Search endpoint
        self.add_rule(RateLimitRule(
            name="search",
            pattern=r"^/api/v1/search",
            requests_per_minute=30,
            burst_size=5
        ))
    
    def add_rule(self, rule: RateLimitRule):
        """Add a rate limit rule."""
        self.rules[rule.name] = rule
    
    def get_rule_for_endpoint(self, endpoint: str) -> RateLimitRule:
        """Get applicable rule for endpoint."""
        # Find matching rule (last match wins for specificity)
        matching = None
        for rule in self.rules.values():
            if rule.matches(endpoint):
                matching = rule
        
        return matching or self.rules.get("default")
    
    def is_allowed(self, key: str, endpoint: str) -> Tuple[bool, Dict]:
        """
        Check if request is allowed using token bucket algorithm.
        
        Args:
            key: Rate limit key (e.g., IP + user)
            endpoint: Request endpoint
        
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        now = time.time()
        rule = self.get_rule_for_endpoint(endpoint)
        full_key = f"{key}:{rule.name}"
        
        if self.redis:
            return self._check_redis(full_key, rule, now)
        else:
            return self._check_memory(full_key, rule, now)
    
    def _check_memory(self, key: str, rule: RateLimitRule, 
                     now: float) -> Tuple[bool, Dict]:
        """Check rate limit using memory storage."""
        data = self._memory[key]
        
        # Token bucket algorithm
        time_passed = now - data["last_update"]
        tokens_to_add = time_passed * (rule.requests_per_minute / 60)
        
        data["tokens"] = min(
            rule.burst_size,
            data["tokens"] + tokens_to_add
        )
        data["last_update"] = now
        
        # Check if request allowed
        if data["tokens"] >= 1:
            data["tokens"] -= 1
            data["count"] += 1
            allowed = True
        else:
            allowed = False
        
        # Calculate reset time
        reset_time = now + (1 / (rule.requests_per_minute / 60))
        
        info = {
            "limit": rule.requests_per_minute,
            "remaining": int(data["tokens"]),
            "reset": int(reset_time),
            "window": rule.window,
            "rule": rule.name,
            "allowed": allowed
        }
        
        return allowed, info
    
    def _check_redis(self, key: str, rule: RateLimitRule,
                     now: float) -> Tuple[bool, Dict]:
        """Check rate limit using Redis."""
        pipe = self.redis.pipeline()
        
        # Use Redis cell algorithm for token bucket
        pipe.multi()
        
        # Get current state
        pipe.hgetall(f"ratelimit:{key}")
        
        # Set expiry
        pipe.expire(f"ratelimit:{key}", rule.window)
        
        results = pipe.execute()
        data = results[0] or {}
        
        tokens = float(data.get("tokens", rule.burst_size))
        last_update = float(data.get("last_update", now))
        
        # Calculate new tokens
        time_passed = now - last_update
        tokens = min(rule.burst_size, 
                    tokens + time_passed * (rule.requests_per_minute / 60))
        
        # Check request
        if tokens >= 1:
            tokens -= 1
            allowed = True
        else:
            allowed = False
        
        # Update Redis
        self.redis.hmset(f"ratelimit:{key}", {
            "tokens": tokens,
            "last_update": now,
            "count": int(data.get("count", 0)) + (1 if allowed else 0)
        })
        
        reset_time = now + (1 / (rule.requests_per_minute / 60))
        
        info = {
            "limit": rule.requests_per_minute,
            "remaining": int(tokens),
            "reset": int(reset_time),
            "window": rule.window,
            "rule": rule.name,
            "allowed": allowed
        }
        
        return allowed, info
    
    def check_auth_attempt(self, identifier: str, 
                           endpoint: str = "/api/v1/auth/login") -> Tuple[bool, Dict]:
        """
        Check authentication attempt rate.
        
        Args:
            identifier: IP address or username
            endpoint: Auth endpoint
        
        Returns:
            Tuple of (allowed, rate_limit_info)
        """
        key = f"auth:{identifier}"
        return self.is_allowed(key, endpoint)
    
    def reset(self, key: str) -> bool:
        """
        Reset rate limit for key.
        
        Args:
            key: Rate limit key
        
        Returns:
            True if reset
        """
        if self.redis:
            # Find all keys matching pattern
            pattern = f"ratelimit:{key}:*"
            keys = self.redis.keys(pattern)
            if keys:
                return self.redis.delete(*keys) > 0
            return False
        else:
            # Remove all matching keys from memory
            keys_to_remove = [k for k in self._memory.keys() if k.startswith(key)]
            for k in keys_to_remove:
                del self._memory[k]
            return len(keys_to_remove) > 0
    
    def get_headers(self, info: Dict) -> Dict[str, str]:
        """
        Get rate limit headers for response.
        
        Args:
            info: Rate limit info from is_allowed()
        
        Returns:
            Dict of HTTP headers
        """
        return {
            "X-RateLimit-Limit": str(info["limit"]),
            "X-RateLimit-Remaining": str(info["remaining"]),
            "X-RateLimit-Reset": str(info["reset"]),
            "X-RateLimit-Rule": info.get("rule", "default")
        }


def rate_limit(rule_name: Optional[str] = None):
    """
    Decorator to apply rate limiting to endpoints.
    
    Args:
        rule_name: Specific rule to use, or auto-detect if None
    
    Usage:
        @rate_limit("auth")
        def login(request):
            ...
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Get request from args (first arg is usually request)
            request = args[0] if args else None
            
            if request and hasattr(request, 'client_ip'):
                # Create limiter instance (should be singleton in production)
                limiter = RateLimiter()
                
                # Get endpoint from request
                endpoint = getattr(request, 'path', '/')
                client_ip = request.client_ip
                
                # Check rate limit
                allowed, info = limiter.is_allowed(client_ip, endpoint)
                
                if not allowed:
                    from webcms.core.response import Response
                    response = Response.error("Rate limit exceeded", 429)
                    response.headers.update(limiter.get_headers(info))
                    return response
                
                # Call original function
                response = func(*args, **kwargs)
                
                # Add rate limit headers to response
                if hasattr(response, 'headers'):
                    response.headers.update(limiter.get_headers(info))
                
                return response
            
            # No request object, call without rate limiting
            return func(*args, **kwargs)
        
        # Store rule name for later use
        wrapper._rate_limit_rule = rule_name
        return wrapper
    return decorator


# Global limiter instance
_limiter_instance: Optional[RateLimiter] = None


def get_limiter(redis_client=None) -> RateLimiter:
    """Get or create global rate limiter."""
    global _limiter_instance
    if _limiter_instance is None:
        _limiter_instance = RateLimiter(redis_client)
    return _limiter_instance
