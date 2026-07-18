"""
Health Check Module

Provides comprehensive health monitoring for the application
"""

import json
import time
from datetime import datetime
from typing import Dict, List, Optional

from webcms.core.response import Response


class HealthCheck:
    """Health check system."""
    
    def __init__(self):
        self.checks = {}
        self.start_time = time.time()
    
    def register(self, name: str, check_func, critical: bool = True):
        """Register a health check."""
        self.checks[name] = {
            'func': check_func,
            'critical': critical,
            'last_result': None,
            'last_run': None
        }
    
    def check_all(self) -> Dict:
        """Run all health checks."""
        results = []
        healthy = True
        
        for name, config in self.checks.items():
            try:
                result = config['func']()
                status = 'healthy' if result else 'unhealthy'
            except Exception as e:
                result = False
                status = 'error'
            
            config['last_result'] = result
            config['last_run'] = datetime.now().isoformat()
            
            if not result and config['critical']:
                healthy = False
            
            results.append({
                'name': name,
                'status': status,
                'critical': config['critical']
            })
        
        return {
            'status': 'healthy' if healthy else 'unhealthy',
            'timestamp': datetime.now().isoformat(),
            'uptime_seconds': int(time.time() - self.start_time),
            'checks': results
        }
    
    def get_status(self) -> Response:
        """Get health status as HTTP response."""
        result = self.check_all()
        status = 200 if result['status'] == 'healthy' else 503
        
        return Response(
            status=status,
            body=json.dumps(result),
            content_type='application/json'
        )


# Global health check instance
health = HealthCheck()


def init_health_checks(db=None, cache=None):
    """Initialize health checks."""
    
    def check_database():
        """Check database connectivity."""
        if db is None:
            return True  # No DB configured
        
        try:
            # Try a simple query
            if hasattr(db, 'execute'):
                db.execute("SELECT 1")
            return True
        except Exception:
            return False
    
    def check_cache():
        """Check cache connectivity."""
        if cache is None:
            return True  # No cache configured
        
        try:
            # Try set/get
            test_key = 'health_check'
            cache.set(test_key, 'ok', 1)
            result = cache.get(test_key)
            return result == 'ok'
        except Exception:
            return False
    
    def check_disk_space():
        """Check disk space."""
        try:
            import shutil
            usage = shutil.disk_usage('/')
            # Fail if less than 10% free
            return (usage.free / usage.total) > 0.1
        except Exception:
            return True
    
    def check_memory():
        """Check memory usage."""
        try:
            import psutil
            memory = psutil.virtual_memory()
            # Fail if more than 95% used
            return memory.percent < 95
        except ImportError:
            return True
    
    # Register checks
    health.register('database', check_database, critical=True)
    health.register('cache', check_cache, critical=False)
    health.register('disk_space', check_disk_space, critical=True)
    health.register('memory', check_memory, critical=False)


# Export
__all__ = ['HealthCheck', 'health', 'init_health_checks']
