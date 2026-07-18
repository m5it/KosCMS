
"""
Cache Manager

Multi-level caching with tagging, warming support, and KosDB persistence.
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
                 namespace: str = "default", db=None):
        self.backends = backends or [MemoryCache()]
        self.namespace = namespace
        self.db = db
        self._tags: Dict[str, CacheTag] = {}
        self._metadata: Dict[str, CacheEntry] = {}
        self._stats = {
            "hits": 0,
            "misses": 0,
            "sets": 0,
            "deletes": 0,
            "tag_invalidations": 0
        }
        self._ensure_cache_table()
    
    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods
    
    def _ensure_cache_table(self):
        """Ensure cache stats table exists in KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            tables = self.db.list_tables()
            if 'cache_stats' in tables:
                return
        except Exception:
            pass
        
        try:
            self.db.execute("""
                CREATE TABLE cache_stats (
                    id TEXT PRIMARY KEY,
                    namespace TEXT,
                    hits INTEGER DEFAULT 0,
                    misses INTEGER DEFAULT 0,
                    sets INTEGER DEFAULT 0,
                    deletes INTEGER DEFAULT 0,
                    tag_invalidations INTEGER DEFAULT 0,
                    keys_count INTEGER DEFAULT 0,
                    memory_usage TEXT,
                    updated_at TEXT
                )
            """)
        except Exception:
            pass
    
    def _save_stats_to_kosdb(self):
        """Save cache stats to KosDB."""
        if not self.db or not self._is_kosdb():
            return
        
        try:
            now = time.time()
            keys_count = len(self._metadata)
            memory_usage = self._estimate_memory()
            
            # Check if exists
            result = self.db.query(f"SELECT id FROM cache_stats WHERE namespace='{self.namespace}'")
            
            if result.get('rows'):
                self.db.execute(f"""
                    UPDATE cache_stats SET
                        hits={self._stats['hits']},
                        misses={self._stats['misses']},
                        sets={self._stats['sets']},
                        deletes={self._stats['deletes']},
                        tag_invalidations={self._stats['tag_invalidations']},
                        keys_count={keys_count},
                        memory_usage='{memory_usage}',
                        updated_at='{now}'
                    WHERE namespace='{self.namespace}'
                """)
            else:
                self.db.execute(f"""
                    INSERT INTO cache_stats 
                    (id, namespace, hits, misses, sets, deletes, tag_invalidations, keys_count, memory_usage, updated_at)
                    VALUES (
                        '{self.namespace}_{int(now)}',
                        '{self.namespace}',
                        {self._stats['hits']},
                        {self._stats['misses']},
                        {self._stats['sets']},
                        {self._stats['deletes']},
                        {self._stats['tag_invalidations']},
                        {keys_count},
                        '{memory_usage}',
                        '{now}'
                    )
                """)
        except Exception:
            pass
    
    def _estimate_memory(self) -> str:
        """Estimate memory usage."""
        try:
            import sys
            total = sys.getsizeof(self._metadata)
            for key, entry in self._metadata.items():
                total += sys.getsizeof(key)
                total += sys.getsizeof(entry)
            return f"{total / 1024 / 1024:.2f}MB"
        except Exception:
            return "unknown"
    
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
        self._save_stats_to_kosdb()
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
        self._save_stats_to_kosdb()
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
        self._save_stats_to_kosdb()
        
        return count
    
    def tag_warm(self, tag: str, data_loader: Callable[[], Dict[str, Any]],
                  timeout: int = 300) -> int:
        """
        Pre-populate cache for a tag.
        
        Args:
            tag: Tag to warm
            data_loader: Function returning dict of key->value
            timeout: TTL for warmed entries
        
        Returns:
            Number of entries warmed
        """
        data = data_loader()
        count = 0
        
        for key, value in data.items():
            if self.set(key, value, timeout, tags=[tag]):
                count += 1
        
        return count
    
    def get_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._stats["hits"] + self._stats["misses"]
        hit_rate = self._stats["hits"] / total if total > 0 else 0
        
        return {
            "keys": len(self._metadata),
            "hit_rate": round(hit_rate, 4),
            "memory": self._estimate_memory(),
            "evicted": self._stats.get("tag_invalidations", 0),
            "hits": self._stats["hits"],
            "misses": self._stats["misses"],
            "sets": self._stats["sets"],
            "deletes": self._stats["deletes"]
        }
    
    def get_stats_from_kosdb(self) -> Dict[str, Any]:
        """Get stats from KosDB persistence."""
        if self.db and self._is_kosdb():
            try:
                result = self.db.query(f"SELECT * FROM cache_stats WHERE namespace='{self.namespace}'")
                if result.get('rows'):
                    row = result['rows'][0]
                    total = int(row.get('hits', 0)) + int(row.get('misses', 0))
                    hit_rate = int(row.get('hits', 0)) / total if total > 0 else 0
                    return {
                        "keys": int(row.get('keys_count', 0)),
                        "hit_rate": round(hit_rate, 4),
                        "memory": row.get('memory_usage', '0MB'),
                        "evicted": int(row.get('tag_invalidations', 0)),
                        "hits": int(row.get('hits', 0)),
                        "misses": int(row.get('misses', 0)),
                        "sets": int(row.get('sets', 0)),
                        "deletes": int(row.get('deletes', 0))
                    }
            except Exception:
                pass
        return self.get_stats()
    
    def clear(self) -> bool:
        """Clear all caches."""
        for backend in self.backends:
            if hasattr(backend, 'clear'):
                backend.clear()
        
        self._metadata.clear()
        self._tags.clear()
        self._save_stats_to_kosdb()
        return True
    
    def invalidate_pattern(self, pattern: str) -> int:
        """
        Invalidate keys matching pattern.
        
        Args:
            pattern: Glob pattern to match
        
        Returns:
            Number of keys invalidated
        """
        import fnmatch
        count = 0
        
        for key in list(self._metadata.keys()):
            if fnmatch.fnmatch(key, pattern):
                if self.delete(key):
                    count += 1
        
        self._save_stats_to_kosdb()
        return count


class CacheWarmer:
    """Cache warming utility for pre-populating cache."""
    
    def __init__(self, cache_manager: CacheManager = None):
        self.cache = cache_manager or CacheManager()
        self._warmers: Dict[str, Callable] = {}
    
    def register(self, tag: str, data_loader: Callable[[], Dict[str, Any]]):
        """Register a cache warming function."""
        self._warmers[tag] = data_loader
    
    def warm(self, tag: str = None, timeout: int = 300) -> Dict[str, int]:
        """
        Warm cache for registered tags.
        
        Args:
            tag: Specific tag to warm, or None for all
            timeout: TTL for warmed entries
        
        Returns:
            Dict of tag -> count warmed
        """
        results = {}
        
        tags_to_warm = [tag] if tag else list(self._warmers.keys())
        
        for t in tags_to_warm:
            if t in self._warmers:
                count = self.cache.tag_warm(t, self._warmers[t], timeout)
                results[t] = count
        
        return results
    
    def warm_all(self, timeout: int = 300) -> Dict[str, int]:
        """Warm all registered cache tags."""
        return self.warm(timeout=timeout)


# Global cache instances
_cache_instances: Dict[str, CacheManager] = {}


def get_cache(namespace: str = "default", db=None) -> CacheManager:
    """Get or create cache manager for namespace."""
    if namespace not in _cache_instances:
        _cache_instances[namespace] = CacheManager(namespace=namespace, db=db)
    return _cache_instances[namespace]


def get_tenant_cache(tenant_id: str, db=None) -> CacheManager:
    """Get cache for specific tenant."""
    return get_cache(f"tenant:{tenant_id}", db=db)


def clear_all_caches():
    """Clear all cache instances."""
    for cache in _cache_instances.values():
        cache.clear()
    _cache_instances.clear()
