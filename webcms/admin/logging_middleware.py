"""
Admin API Logging Middleware

Provides comprehensive logging for all admin operations
"""

import json
import time
import logging
from datetime import datetime
from functools import wraps

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger('webcms.admin')


class AdminLogger:
    """Logger for admin operations."""
    
    def __init__(self):
        self.operation_count = {
            'create': 0,
            'update': 0,
            'delete': 0,
            'read': 0,
            'error': 0
        }
    
    def log_operation(self, operation: str, entity_type: str, 
                      entity_id: str = None, user_id: str = None,
                      success: bool = True, details: dict = None):
        """Log an admin operation."""
        self.operation_count[operation if success else 'error'] += 1
        
        log_entry = {
            'timestamp': datetime.utcnow().isoformat(),
            'operation': operation,
            'entity_type': entity_type,
            'entity_id': entity_id,
            'user_id': user_id,
            'success': success,
            'details': details or {}
        }
        
        if success:
            logger.info(f"Admin {operation}: {entity_type} {entity_id} by {user_id}")
        else:
            logger.error(f"Admin {operation} FAILED: {entity_type} {entity_id} by {user_id}")
        
        return log_entry
    
    def log_error(self, error: Exception, context: dict = None):
        """Log an error with context."""
        self.operation_count['error'] += 1
        
        logger.error(
            f"Admin error: {str(error)}",
            exc_info=True,
            extra={'context': context or {}}
        )
    
    def get_stats(self) -> dict:
        """Get logging statistics."""
        return {
            'operation_count': self.operation_count.copy(),
            'total_operations': sum(self.operation_count.values())
        }


# Global logger instance
admin_logger = AdminLogger()


def log_admin_operation(operation: str, entity_type: str):
    """Decorator to log admin operations."""
    def decorator(func):
        @wraps(func)
        def wrapper(self, request, *args, **kwargs):
            start_time = time.time()
            entity_id = kwargs.get(f'{entity_type}_id') or kwargs.get('id')
            
            try:
                result = func(self, request, *args, **kwargs)
                duration = time.time() - start_time
                
                admin_logger.log_operation(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    success=True,
                    details={'duration_ms': int(duration * 1000)}
                )
                
                return result
                
            except Exception as e:
                duration = time.time() - start_time
                
                admin_logger.log_operation(
                    operation=operation,
                    entity_type=entity_type,
                    entity_id=entity_id,
                    success=False,
                    details={
                        'error': str(e),
                        'duration_ms': int(duration * 1000)
                    }
                )
                
                raise
        
        return wrapper
    return decorator


class AuditTrail:
    """Audit trail for admin actions."""
    
    def __init__(self, db=None):
        self.db = db
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure audit trail table exists."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'audit_trail' not in tables:
                self.db.execute("""
                    CREATE TABLE audit_trail (
                        id TEXT PRIMARY KEY,
                        timestamp TEXT,
                        user_id TEXT,
                        action TEXT,
                        entity_type TEXT,
                        entity_id TEXT,
                        old_values TEXT,
                        new_values TEXT,
                        ip_address TEXT
                    )
                """)
        except Exception:
            pass
    
    def log(self, user_id: str, action: str, entity_type: str,
            entity_id: str, old_values: dict = None, 
            new_values: dict = None, ip_address: str = None):
        """Log an audit trail entry."""
        if not self.db:
            return
        
        import uuid
        entry_id = str(uuid.uuid4())
        timestamp = datetime.utcnow().isoformat()
        
        try:
            self.db.execute(f"""
                INSERT INTO audit_trail 
                (id, timestamp, user_id, action, entity_type, entity_id, 
                 old_values, new_values, ip_address)
                VALUES (
                    '{entry_id}',
                    '{timestamp}',
                    '{user_id}',
                    '{action}',
                    '{entity_type}',
                    '{entity_id}',
                    '{json.dumps(old_values or {})}',
                    '{json.dumps(new_values or {})}',
                    '{ip_address or ''}'
                )
            """)
        except Exception as e:
            logger.error(f"Failed to write audit trail: {e}")
    
    def get_trail(self, entity_type: str = None, 
                  entity_id: str = None, limit: int = 50) -> list:
        """Get audit trail entries."""
        if not self.db:
            return []
        
        try:
            sql = "SELECT * FROM audit_trail"
            conditions = []
            
            if entity_type:
                conditions.append(f"entity_type='{entity_type}'")
            if entity_id:
                conditions.append(f"entity_id='{entity_id}'")
            
            if conditions:
                sql += " WHERE " + " AND ".join(conditions)
            
            sql += f" ORDER BY timestamp DESC LIMIT {limit}"
            
            result = self.db.query(sql)
            return result.get('rows', [])
        except Exception:
            return []


# Export
__all__ = ['AdminLogger', 'admin_logger', 'log_admin_operation', 'AuditTrail']
