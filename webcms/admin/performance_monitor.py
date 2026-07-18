"""
Performance Monitoring for Admin Panel

Tracks API response times, database queries, and system metrics
"""

import time
import functools
import threading
from collections import defaultdict, deque
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable


class PerformanceMonitor:
    """Monitor API and system performance."""
    
    def __init__(self, max_history: int = 1000):
        self.max_history = max_history
        self.metrics = defaultdict(lambda: {
            'count': 0,
            'total_time': 0.0,
            'min_time': float('inf'),
            'max_time': 0.0,
            'history': deque(maxlen=max_history),
            'errors': 0
        })
        self._lock = threading.Lock()
        self.start_time = datetime.now()
    
    def record(self, endpoint: str, duration: float, success: bool = True):
        """Record a metric."""
        with self._lock:
            metric = self.metrics[endpoint]
            metric['count'] += 1
            metric['total_time'] += duration
            
            if success:
                metric['min_time'] = min(metric['min_time'], duration)
                metric['max_time'] = max(metric['max_time'], duration)
            else:
                metric['errors'] += 1
            
            metric['history'].append({
                'timestamp': datetime.now().isoformat(),
                'duration': duration,
                'success': success
            })
    
    def get_stats(self, endpoint: Optional[str] = None) -> Dict:
        """Get performance statistics."""
        with self._lock:
            if endpoint:
                if endpoint not in self.metrics:
                    return {}
                return self._calculate_stats(self.metrics[endpoint])
            
            return {
                name: self._calculate_stats(data)
                for name, data in self.metrics.items()
            }
    
    def _calculate_stats(self, metric: Dict) -> Dict:
        """Calculate statistics from metric data."""
        count = metric['count']
        if count == 0:
            return {}
        
        avg_time = metric['total_time'] / count
        
        # Calculate percentiles from history
        durations = [h['duration'] for h in metric['history']]
        durations.sort()
        
        p50 = self._percentile(durations, 50)
        p95 = self._percentile(durations, 95)
        p99 = self._percentile(durations, 99)
        
        return {
            'count': count,
            'avg_time_ms': round(avg_time * 1000, 2),
            'min_time_ms': round(metric['min_time'] * 1000, 2) if metric['min_time'] != float('inf') else 0,
            'max_time_ms': round(metric['max_time'] * 1000, 2),
            'p50_ms': round(p50 * 1000, 2) if p50 else 0,
            'p95_ms': round(p95 * 1000, 2) if p95 else 0,
            'p99_ms': round(p99 * 1000, 2) if p99 else 0,
            'errors': metric['errors'],
            'error_rate': round(metric['errors'] / count * 100, 2) if count > 0 else 0
        }
    
    def _percentile(self, sorted_data: List[float], percentile: int) -> Optional[float]:
        """Calculate percentile from sorted data."""
        if not sorted_data:
            return None
        
        index = int(len(sorted_data) * percentile / 100)
        return sorted_data[min(index, len(sorted_data) - 1)]
    
    def get_slow_endpoints(self, threshold_ms: float = 1000) -> List[Dict]:
        """Get endpoints slower than threshold."""
        slow = []
        for name, metric in self.metrics.items():
            stats = self._calculate_stats(metric)
            if stats.get('avg_time_ms', 0) > threshold_ms:
                slow.append({
                    'endpoint': name,
                    'avg_time_ms': stats['avg_time_ms'],
                    'p95_ms': stats['p95_ms']
                })
        
        return sorted(slow, key=lambda x: x['avg_time_ms'], reverse=True)
    
    def get_uptime(self) -> Dict:
        """Get system uptime."""
        uptime = datetime.now() - self.start_time
        return {
            'days': uptime.days,
            'hours': uptime.seconds // 3600,
            'minutes': (uptime.seconds % 3600) // 60,
            'total_seconds': int(uptime.total_seconds())
        }
    
    def reset(self):
        """Reset all metrics."""
        with self._lock:
            self.metrics.clear()
            self.start_time = datetime.now()


# Global monitor instance
monitor = PerformanceMonitor()


def timed(endpoint_name: Optional[str] = None):
    """Decorator to time function execution."""
    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            name = endpoint_name or func.__name__
            start = time.time()
            
            try:
                result = func(*args, **kwargs)
                duration = time.time() - start
                monitor.record(name, duration, success=True)
                return result
            
            except Exception as e:
                duration = time.time() - start
                monitor.record(name, duration, success=False)
                raise
        
        return wrapper
    return decorator


class QueryProfiler:
    """Profile database queries."""
    
    def __init__(self):
        self.queries = []
        self.enabled = False
    
    def enable(self):
        """Enable query profiling."""
        self.enabled = True
    
    def disable(self):
        """Disable query profiling."""
        self.enabled = False
    
    def profile(self, query: str, duration: float):
        """Record a query."""
        if self.enabled:
            self.queries.append({
                'query': query[:200],  # Truncate long queries
                'duration_ms': round(duration * 1000, 2),
                'timestamp': datetime.now().isoformat()
            })
    
    def get_slow_queries(self, threshold_ms: float = 100) -> List[Dict]:
        """Get slow queries."""
        return [
            q for q in self.queries
            if q['duration_ms'] > threshold_ms
        ]
    
    def get_stats(self) -> Dict:
        """Get query statistics."""
        if not self.queries:
            return {'count': 0, 'avg_time_ms': 0}
        
        durations = [q['duration_ms'] for q in self.queries]
        return {
            'count': len(self.queries),
            'avg_time_ms': round(sum(durations) / len(durations), 2),
            'max_time_ms': max(durations),
            'slow_queries': len(self.get_slow_queries())
        }
    
    def clear(self):
        """Clear query history."""
        self.queries.clear()


# Global profiler instance
profiler = QueryProfiler()


class CacheMetrics:
    """Track cache performance."""
    
    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.evictions = 0
    
    def record_hit(self):
        """Record cache hit."""
        self.hits += 1
    
    def record_miss(self):
        """Record cache miss."""
        self.misses += 1
    
    def record_eviction(self):
        """Record cache eviction."""
        self.evictions += 1
    
    def get_stats(self) -> Dict:
        """Get cache statistics."""
        total = self.hits + self.misses
        hit_rate = self.hits / total if total > 0 else 0
        
        return {
            'hits': self.hits,
            'misses': self.misses,
            'evictions': self.evictions,
            'hit_rate': round(hit_rate * 100, 2),
            'total_requests': total
        }


# Global cache metrics
cache_metrics = CacheMetrics()


def get_system_metrics() -> Dict:
    """Get overall system metrics."""
    import psutil
    
    try:
        cpu_percent = psutil.cpu_percent(interval=0.1)
        memory = psutil.virtual_memory()
        disk = psutil.disk_usage('/')
        
        return {
            'cpu_percent': cpu_percent,
            'memory': {
                'total_gb': round(memory.total / (1024**3), 2),
                'available_gb': round(memory.available / (1024**3), 2),
                'percent': memory.percent
            },
            'disk': {
                'total_gb': round(disk.total / (1024**3), 2),
                'free_gb': round(disk.free / (1024**3), 2),
                'percent': round((disk.used / disk.total) * 100, 2)
            },
            'uptime': monitor.get_uptime()
        }
    except ImportError:
        return {
            'error': 'psutil not installed',
            'uptime': monitor.get_uptime()
        }


# Export
__all__ = [
    'PerformanceMonitor',
    'monitor',
    'timed',
    'QueryProfiler',
    'profiler',
    'CacheMetrics',
    'cache_metrics',
    'get_system_metrics'
]
