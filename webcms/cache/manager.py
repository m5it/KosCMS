"""
Cache Manager

Multi-level caching with fallback strategies.
"""

from typing import Any, Optional, List
from .backends import CacheBackend, MemoryCache


class CacheManager:
    """Multi-level cache manager."""
    
    def __init__(self, backends: List[CacheBackend] = None):
        self.backends = backends or [MemoryCache()]
    
    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Tries each backend in order, populating
        earlier backends on cache hit.
        """
        value = None
        found_at = -1
        
        for i, backend in enumerate(self.backends):
            value = backend.get(key)
            if value is not None:
                found_at = i
                break
        
        # Populate earlier caches
        if found_at > 0:
            for i in range(found_at):
                self.backends[i].set(key, value)
        
        return value
    
    def set(self, key: str, value: Any, timeout: int = 300) -> bool:
        """Set value in all caches."""
        results = []
        for backend in self.backends:
            results.append(backend.set(key, value, timeout))
        return any(results)
    
    def delete(self, key: str) -> bool:
        """Delete from all caches."""
        results = []
        for backend in self.backends:
            results.append(backend.delete(key))
        return any(results)
    
    def clear(self) -> bool:
        """Clear all caches."""
        results = []
        for backend in self.backends:
            results.append(backend.clear())
        return all(results)
    
    def memoize(self, timeout: int = 300):
        """
        Decorator to cache function results.
        
        Usage:
            @cache.memoize(timeout=60)
            def expensive_function(x):
                return x * 2
        """
        def decorator(func):
            def wrapper(*args, **kwargs):
                # Create cache key from function name and arguments
                key = f"memo:{func.__name__}:{hash(str(args))}:{hash(str(kwargs))}"
                
                # Try cache
                result = self.get(key)
                if result is not None:
                    return result
                
                # Compute and cache
                result = func(*args, **kwargs)
                self.set(key, result, timeout)
                return result
            
            # Add cache clear method
            wrapper.clear_cache = lambda: self.delete(
                f"memo:{func.__name__}"
            )
            
            return wrapper
        return decorator