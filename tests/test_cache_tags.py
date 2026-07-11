
"""
Tests for Cache Tagging (v1.1.0)

Cache tagging and warming functionality.
"""

import pytest
import time

from webcms.cache.manager import (
    CacheManager,
    CacheTag,
    CacheWarmer,
    get_tenant_cache
)


class TestCacheTag:
    """Test cache tag functionality."""
    
    def test_tag_creation(self):
        """Test CacheTag creation."""
        tag = CacheTag("test-tag")
        assert tag.name == "test-tag"
    
    def test_add_remove_key(self):
        """Test adding and removing keys."""
        tag = CacheTag("test-tag")
        
        tag.add_key("key1")
        tag.add_key("key2")
        
        assert "key1" in tag.get_keys()
        assert "key2" in tag.get_keys()
        
        tag.remove_key("key1")
        assert "key1" not in tag.get_keys()
    
    def test_clear(self):
        """Test clearing tag."""
        tag = CacheTag("test-tag")
        tag.add_key("key1")
        tag.add_key("key2")
        
        tag.clear()
        assert len(tag.get_keys()) == 0


class TestCacheManager:
    """Test cache manager with tagging."""
    
    @pytest.fixture
    def cache(self):
        """Create test cache."""
        return CacheManager(namespace="test")
    
    def test_set_with_tags(self, cache):
        """Test setting value with tags."""
        result = cache.set("key1", "value1", tags=["tag1", "tag2"])
        assert result is True
    
    def test_tag_invalidate(self, cache):
        """Test invalidating by tag."""
        cache.set("key1", "value1", tags=["tag1"])
        cache.set("key2", "value2", tags=["tag1"])
        cache.set("key3", "value3", tags=["tag2"])
        
        count = cache.tag_invalidate("tag1")
        
        assert count == 2
        assert cache.get("key1") is None
        assert cache.get("key2") is None
        assert cache.get("key3") == "value3"
    
    def test_tag_warm(self, cache):
        """Test cache warming."""
        def data_loader():
            return {
                "warm1": "warmed_value1",
                "warm2": "warmed_value2"
            }
        
        count = cache.tag_warm("warm-tag", data_loader)
        
        assert count == 2
        assert cache.get("warm1") == "warmed_value1"
    
    def test_get_stats(self, cache):
        """Test statistics."""
        cache.set("key", "value")
        cache.get("key")
        cache.get("missing")
        
        stats = cache.get_stats()
        
        assert stats["hits"] == 1
        assert stats["misses"] == 1
        assert stats["sets"] == 1


class TestCacheWarmer:
    """Test cache warmer."""
    
    @pytest.fixture
    def cache(self):
        """Create test cache."""
        return CacheManager(namespace="warmer-test")
    
    @pytest.fixture
    def warmer(self, cache):
        """Create cache warmer."""
        return CacheWarmer(cache)
    
    def test_register_warmer(self, warmer):
        """Test registering warming function."""
        def loader():
            return {"key": "value"}
        
        warmer.register("test-warm", loader, timeout=300)
        
        assert "test-warm" in warmer._warmers
    
    def test_warm(self, warmer, cache):
        """Test warming cache."""
        def loader():
            return {"warm-key": "warm-value"}
        
        warmer.register("warm-test", loader)
        results = warmer.warm("warm-test")
        
        assert results["warm-test"] == 1
        assert cache.get("warm-key") == "warm-value"


class TestTenantCache:
    """Test tenant-aware caching."""
    
    def test_get_tenant_cache(self):
        """Test tenant cache isolation."""
        cache1 = get_tenant_cache("tenant-1")
        cache2 = get_tenant_cache("tenant-2")
        
        cache1.set("key", "value1")
        cache2.set("key", "value2")
        
        assert cache1.get("key") == "value1"
        assert cache2.get("key") == "value2"
    
    def test_tenant_isolation(self):
        """Test tenant namespace isolation."""
        cache1 = get_tenant_cache("tenant-a")
        cache2 = get_tenant_cache("tenant-b")
        
        # Different namespaces
        assert cache1.namespace == "tenant-a"
        assert cache2.namespace == "tenant-b"
