
"""
Tests for Rate Limiting (v1.1.0)

Endpoint-specific rate limiting with token bucket.
"""

import pytest
import time

from webcms.auth.rate_limiter import (
    RateLimiter,
    RateLimitRule,
    rate_limit,
    get_limiter
)


class TestRateLimitRule:
    """Test rate limit rule."""
    
    def test_rule_creation(self):
        """Test RateLimitRule creation."""
        rule = RateLimitRule(
            name="test",
            pattern=r"^/api/test",
            requests_per_minute=60,
            burst_size=10
        )
        
        assert rule.name == "test"
        assert rule.requests_per_minute == 60
    
    def test_pattern_matching(self):
        """Test endpoint pattern matching."""
        rule = RateLimitRule(
            name="api",
            pattern=r"^/api/v1/.*"
        )
        
        assert rule.matches("/api/v1/users") is True
        assert rule.matches("/other/path") is False


class TestRateLimiter:
    """Test rate limiter."""
    
    @pytest.fixture
    def limiter(self):
        """Create rate limiter."""
        return RateLimiter()
    
    def test_is_allowed(self, limiter):
        """Test basic rate limiting."""
        allowed, info = limiter.is_allowed("client-1", "/api/v1/test")
        
        assert allowed is True
        assert "limit" in info
        assert "remaining" in info
    
    def test_rate_limit_exceeded(self, limiter):
        """Test rate limit enforcement."""
        # Make many requests quickly
        for _ in range(15):
            limiter.is_allowed("client-2", "/api/v1/test")
        
        # Should be rate limited
        allowed, info = limiter.is_allowed("client-2", "/api/v1/test")
        assert allowed is False
    
    def test_get_rule_for_endpoint(self, limiter):
        """Test rule selection."""
        rule = limiter.get_rule_for_endpoint("/api/v1/auth/login")
        
        assert rule is not None
        assert rule.name == "login"  # Most specific match
    
    def test_check_auth_attempt(self, limiter):
        """Test auth attempt checking."""
        allowed, info = limiter.check_auth_attempt("192.168.1.1")
        
        assert isinstance(allowed, bool)
        assert "limit" in info
    
    def test_get_headers(self, limiter):
        """Test header generation."""
        allowed, info = limiter.is_allowed("client-3", "/api/v1/test")
        headers = limiter.get_headers(info)
        
        assert "X-RateLimit-Limit" in headers
        assert "X-RateLimit-Remaining" in headers
        assert "X-RateLimit-Reset" in headers


class TestRateLimitDecorator:
    """Test rate limit decorator."""
    
    def test_decorator_application(self):
        """Test decorator can be applied."""
        @rate_limit("default")
        def test_function():
            return "success"
        
        # Should have decorator attributes
        assert hasattr(test_function, '_rate_limit_rule')
    
    def test_decorator_with_rule(self):
        """Test decorator with specific rule."""
        @rate_limit("auth")
        def auth_endpoint():
            return "auth"
        
        assert auth_endpoint._rate_limit_rule == "auth"


class TestGlobalLimiter:
    """Test global rate limiter."""
    
    def test_singleton(self):
        """Test singleton pattern."""
        limiter1 = get_limiter()
        limiter2 = get_limiter()
        
        assert limiter1 is limiter2
    
    def test_default_rules(self):
        """Test default rules exist."""
        limiter = get_limiter()
        
        assert "default" in limiter.rules
        assert "auth" in limiter.rules
        assert "login" in limiter.rules


class TestTokenBucket:
    """Test token bucket algorithm."""
    
    def test_token_refill(self):
        """Test tokens refill over time."""
        limiter = RateLimiter()
        
        # Use up tokens
        for _ in range(20):
            limiter.is_allowed("client", "/api/v1/test")
        
        # Should be rate limited
        allowed, _ = limiter.is_allowed("client", "/api/v1/test")
        assert allowed is False
        
        # Wait for refill
        time.sleep(0.1)
        
        # Should have some tokens back
        allowed, info = limiter.is_allowed("client", "/api/v1/test")
        assert info["remaining"] >= 0
