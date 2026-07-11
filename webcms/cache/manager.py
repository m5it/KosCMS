
"""
Cache Manager

Multi-level caching with tagging and warming support.
"""

import json
import time
from typing import Any, Optional, List, Dict, Set, Callable
from dataclasses import dataclass, field

from .backends import CacheBackend, MemoryCache


@dataclass
class CacheEntry:
    """Cache entry with metadata."""
    value: Any
    tags: Set[str] = field(default_factory=set)
    created_at: float = field(default_factory=time.time)
    access_count: int = 0


class CacheTag:
    """Cache tag for grouping entries."""
    
    def __init__(self, name: str):
        self.name = name
        self._keys: Set[str] = set()
    
    def add_key(self, key: str):
        """Add a key to this tag."""
        self._keys.add(key)
    
    def remove_key(self, key: str):
        """Remove a key from this tag."""
        self._keys.discard(key)
    
    def get_keys(self) -> Set[str]:
        """Get all keys with this tag."""
        return self._keys.copy()
    
    def clear(self):
        """Clear all keys."""
        self._keys.clear()


class CacheManager:
    """Multi-level cache manager with tagging support."""
    
    def __init__(self, backends: List[CacheBackend] = None, 
                 namespace: str = "default"):
        self.backends = backends or [MemoryCache()]
        self.namespace = namespace
        self._tags: Dict[str, CacheTag] = {}
        self._metadata: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "tag_invalidations": 0
        }
    
    def _namespaced_key(self, key: str) -> str:
        """Add namespace prefix to key."""
        return f"{self.namespace}:{key}"
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Tries each backend in order, populating
        earlier backends on cache hit.
        """
        namespaced = self._namespaced_key(key)
        value = None
        found_at = -1
        
        for i, backend in enumerate(self.backends):
            value = backend.get(namespaced)
            if value is not None:
                found_at = i
                self._stats["hits"] += 1
                break
        
        if found_at == -1:
            self._stats["misses"] += 1
            return None
        
        # Update metadata
        if key in self._metadata:
            self._metadata[key].access_count += 1
        
        # Populate earlier caches
        if found_at > 0:
            for i in range(found_at):
                self.backends[i].set(namespaced, value)
        
        return value
    
    def set(self, key: str, value: Any, timeout: int = 300,
            tags: List[str] = None) -> bool:
        """
        Set value in all caches with optional tags.
        
        Args:
            key: Cache key
            value: Value to cache
            timeout: TTL in seconds
            tags: Optional list of tags for grouping
        """
        namespaced = self._namespaced_key(key)
        tags = tags or []
        
        # Store metadata
        self._metadata[key] = CacheEntry(
            value=value,
            tags=set(tags)
        )
        
        # Register with tags
        for tag_name in tags:
            if tag_name not in self._tags:
                self._tags[tag_name] = CacheTag(tag_name)
            self._tags[tag_name].add_key(key)
        
        # Set in all backends
        results = []
        for backend in self.backends:
            results.append(backend.set(namespaced, value, timeout))
        
        self._stats["sets"] += 1
        return any(results)
    
    def delete(self, key: str) -> bool:
        """Delete from all caches."""
        namespaced = self._namespaced_key(key)
        
        # Remove from tags
        if key in self._metadata:
            entry = self._metadata[key]
            for tag_name in entry.tags:
                if tag_name in self._tags:
                    self._tags[tag_name].remove_key(key)
            del self._metadata[key]
        
        results = []
        for backend in self.backends:
            results.append(backend.delete(namespaced))
        
        self._stats["deletes"] += 1
        return any(results)
    
    def tag_invalidate(self, tag: str) -> int:
        """
        Invalidate all cache entries with a given tag.
        
        Args:
            tag: Tag name to invalidate
        
        Returns:
            Number of entries invalidated
        """
        if tag not in self._tags:
            return 0
        
        tag_obj = self._tags[tag]
        keys = tag_obj.get_keys()
        count = 0
        
        for key in list(keys):
            if self.delete(key):
                count += 1
        
        tag_obj.clear()
        self._stats["tag_invalidations"] += 1
        
        return count
    
    def tag_warm(self, tag: str, data_loader: Callable[[], Dict[str, Any]],
                 timeout: int = 300) -> int:
        """
        Pre-warm cache for a tag by loading data.
        
        Args:
            tag: Tag name
            data_loader: Function that returns dict of key->value
            timeout: Cache TTL
        
        Returns:
            Number of entries warmed
        """
        try:
            data = data_loader()
            count = 0
            
            for key, value in data.items():
                self.set(key, value, timeout, tags=[tag])
                count += 1
            
            return count
            
        except Exception as e:
            print(f"Cache warming error for tag '{tag}': {e}")
            return 0
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total_requests = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total_requests if total_requests > 0 else 0
        
        return {
            "namespace": self.namespace,
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "hit_rate": round(hit_rate, 4),
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"],
            "tag_invalidations": self._stats["tag_invalidations"],
            "tag_count": len(self._tags),
            "metadata_entries": len(self._metadata),
            "backends": len(self.backends)
        }
    
    def clear(self) -> bool:
        """Clear all caches."""
        self._tags.clear()
        self._metadata.clear()
        
        results = []
        for backend in self.backends:
            results.append(backend.clear())
        
        return all(results)
    
    def memoize(self, timeout: int = 300, tags: List[str] = None):
        """
        Decorator to cache function results with tagging.
        
        Usage:
            @cache.memoize(timeout=60, tags=["posts"])
            def get_posts():
                return db.query(Post).all()
        """
        tags = tags or []
        
        def decorator(func):
            def wrapper(*args, **kwargs):
                key = f"memo:{func.__name__}:{hash(str(args))}:{hash(str(kwargs))}"
                
                result = self.get(key)
                if result is not None:
                    return result
                
                result = func(*args, **kwargs)
                self.set(key, result, timeout, tags=tags)
                return result
            
            wrapper.clear_cache = lambda: self.delete(
                f"memo:{func.__name__}"
            )
            
            wrapper.invalidate_tag = lambda tag: self.tag_invalidate(tag)
            
            return wrapper
        return decorator


class CacheWarmer:
    """Service for pre-warming common cache queries."""
    
    def __init__(self, cache: CacheManager):
        self.cache = cache
        self._warmers: Dict[str, Callable] = {}
    
    def register(self, name: str, data_loader: Callable[[], Dict[str, Any]],
                 timeout: int = 300):
        """
        Register a cache warming function.
        
        Args:
            name: Warmer name
            data_loader: Function returning dict of key->value
            timeout: Cache TTL
        """
        self._warmers[name] = {
            "loader": data_loader,
            "timeout": timeout
        }
    
    def warm(self, name: str = None) -> Dict[str, int]:
        """
        Execute cache warming.
        
        Args:
            name: Specific warmer to run, or None for all
        
        Returns:
            Dict of warmer name -> entries warmed
        """
        results = {}
        
        warmers_to_run = [name] if name else list(self._warmers.keys())
        
        for warmer_name in warmers_to_run:
            if warmer_name not in self._warmers:
                continue
            
            config = self._warmers[warmer_name]
            count = self.cache.tag_warm(
                warmer_name,
                config["loader"],
                config["timeout"]
            )
            results[warmer_name] = count
        
        return results
    
    def warm_all(self) -> Dict[str, int]:
        """Warm all registered caches."""
        return self.warm()


# Tenant-aware cache factory
_tenant_caches: Dict[str, CacheManager] = {}


def get_tenant_cache(tenant_id: str = "default") -> CacheManager:
    """Get or create namespaced cache for tenant."""
    if tenant_id not in _tenant_caches:
        _tenant_caches[tenant_id] = CacheManager(namespace=tenant_id)
    return _tenant_caches[tenant_id]
