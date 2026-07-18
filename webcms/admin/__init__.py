"""
WebCMS Admin Package

Provides administrative functionality for WebCMS including:
- Admin API with CRUD operations
- User and role management
- Content management
- System administration
- Webhooks and scheduled tasks
- Performance monitoring
- Data import/export
"""

from .admin_api import AdminAPI
from .logging_middleware import AdminLogger, admin_logger
from .performance_monitor import (
    PerformanceMonitor, monitor, timed,
    QueryProfiler, profiler,
    CacheMetrics, cache_metrics,
    get_system_metrics
)
from .rate_limiter import (
    RateLimiter, rate_limiter, rate_limit,
    SlidingWindowRateLimiter
)
from .validators import (
    ValidationError, MultipleValidationError,
    Validator, StringValidator, EmailValidator,
    IntegerValidator, BooleanValidator, ListValidator, DictValidator,
    Validators, validate_request, validate_or_error
)
from .data_import_export import (
    DataFormat, DataExporter, DataImporter,
    BulkOperations, ImportResult, ExportResult,
    exporter, importer,
    export_users, export_content,
    import_users, import_content
)
from .webhooks import (
    WebhookEvent, Webhook, WebhookManager,
    webhook_manager, EventEmitter, event_emitter,
    emit_event
)
from .scheduler import (
    TaskStatus, ScheduledTask, TaskScheduler,
    scheduler, CommonTasks, setup_common_tasks
)

__version__ = '1.0.0'

__all__ = [
    # Core
    'AdminAPI',
    'AdminLogger',
    'admin_logger',
    
    # Performance
    'PerformanceMonitor',
    'monitor',
    'timed',
    'QueryProfiler',
    'profiler',
    'CacheMetrics',
    'cache_metrics',
    'get_system_metrics',
    
    # Security
    'RateLimiter',
    'rate_limiter',
    'rate_limit',
    'SlidingWindowRateLimiter',
    
    # Validation
    'ValidationError',
    'MultipleValidationError',
    'Validator',
    'StringValidator',
    'EmailValidator',
    'IntegerValidator',
    'BooleanValidator',
    'ListValidator',
    'DictValidator',
    'Validators',
    'validate_request',
    'validate_or_error',
    
    # Import/Export
    'DataFormat',
    'DataExporter',
    'DataImporter',
    'BulkOperations',
    'ImportResult',
    'ExportResult',
    'exporter',
    'importer',
    'export_users',
    'export_content',
    'import_users',
    'import_content',
    
    # Webhooks
    'WebhookEvent',
    'Webhook',
    'WebhookManager',
    'webhook_manager',
    'EventEmitter',
    'event_emitter',
    'emit_event',
    
    # Scheduler
    'TaskStatus',
    'ScheduledTask',
    'TaskScheduler',
    'scheduler',
    'CommonTasks',
    'setup_common_tasks',
]
