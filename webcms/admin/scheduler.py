"""
Task Scheduler for Admin Panel

Provides cron-like scheduling for automated tasks
(No external dependencies required)
"""

import time
import threading
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Callable, Any
from dataclasses import dataclass
from enum import Enum
import uuid


class TaskStatus(Enum):
    """Task execution status."""
    PENDING = 'pending'
    RUNNING = 'running'
    SUCCESS = 'success'
    FAILED = 'failed'
    CANCELLED = 'cancelled'


@dataclass
class ScheduledTask:
    """Scheduled task configuration."""
    id: str
    name: str
    schedule: str  # Schedule expression
    function: Callable
    args: tuple
    kwargs: Dict
    enabled: bool
    last_run: Optional[datetime]
    last_status: Optional[TaskStatus]
    last_error: Optional[str]
    run_count: int
    fail_count: int
    next_run: Optional[datetime] = None


class SimpleScheduler:
    """Simple task scheduler without external dependencies."""
    
    def __init__(self, db=None):
        self.db = db
        self.tasks: Dict[str, ScheduledTask] = {}
        self._running = False
        self._thread: Optional[threading.Thread] = None
        self._ensure_table()
        self._load_tasks()
    
    def _ensure_table(self):
        """Ensure scheduled_tasks table exists."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'scheduled_tasks' not in tables:
                self.db.execute("""
                    CREATE TABLE scheduled_tasks (
                        id TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        schedule TEXT NOT NULL,
                        enabled INTEGER DEFAULT 1,
                        last_run TEXT,
                        last_status TEXT,
                        last_error TEXT,
                        run_count INTEGER DEFAULT 0,
                        fail_count INTEGER DEFAULT 0,
                        next_run TEXT
                    )
                """)
        except Exception:
            pass
    
    def _load_tasks(self):
        """Load tasks from database."""
        if not self.db:
            return
        
        try:
            result = self.db.query("SELECT * FROM scheduled_tasks")
            for row in result.get('rows', []):
                task_id = row['id']
                self.tasks[task_id] = ScheduledTask(
                    id=task_id,
                    name=row['name'],
                    schedule=row['schedule'],
                    function=None,  # Must be registered
                    args=(),
                    kwargs={},
                    enabled=bool(row['enabled']),
                    last_run=datetime.fromisoformat(row['last_run']) if row.get('last_run') else None,
                    last_status=TaskStatus(row['last_status']) if row.get('last_status') else None,
                    last_error=row.get('last_error'),
                    run_count=row.get('run_count', 0),
                    fail_count=row.get('fail_count', 0),
                    next_run=datetime.fromisoformat(row['next_run']) if row.get('next_run') else None
                )
        except Exception:
            pass
    
    def register_task(self, name: str, schedule_expr: str, function: Callable,
                     args: tuple = (), kwargs: Dict = None) -> str:
        """
        Register a new scheduled task.
        
        Args:
            name: Task name
            schedule_expr: Schedule expression (e.g., 'every 1 hours', 'daily at 10:00')
            function: Function to execute
            args: Positional arguments
            kwargs: Keyword arguments
        
        Returns:
            Task ID
        """
        task_id = str(uuid.uuid4())
        
        # Calculate next run
        next_run = self._parse_schedule(schedule_expr)
        
        task = ScheduledTask(
            id=task_id,
            name=name,
            schedule=schedule_expr,
            function=function,
            args=args,
            kwargs=kwargs or {},
            enabled=True,
            last_run=None,
            last_status=None,
            last_error=None,
            run_count=0,
            fail_count=0,
            next_run=next_run
        )
        
        self.tasks[task_id] = task
        
        # Save to database
        if self.db:
            try:
                next_run_str = next_run.isoformat() if next_run else ''
                self.db.execute(f"""
                    INSERT INTO scheduled_tasks 
                    (id, name, schedule, enabled, next_run, run_count, fail_count)
                    VALUES ('{task_id}', '{name}', '{schedule_expr}', 1, '{next_run_str}', 0, 0)
                """)
            except Exception:
                pass
        
        return task_id
    
    def _parse_schedule(self, schedule_expr: str) -> Optional[datetime]:
        """Parse schedule expression and calculate next run time."""
        now = datetime.utcnow()
        parts = schedule_expr.lower().split()
        
        try:
            if 'every' in parts:
                # Format: every N minutes/hours/days
                idx = parts.index('every')
                if idx + 2 < len(parts):
                    interval = int(parts[idx + 1])
                    unit = parts[idx + 2]
                    
                    if unit in ['minute', 'minutes']:
                        return now + timedelta(minutes=interval)
                    elif unit in ['hour', 'hours']:
                        return now + timedelta(hours=interval)
                    elif unit in ['day', 'days']:
                        return now + timedelta(days=interval)
            
            elif 'daily' in parts and 'at' in parts:
                # Format: daily at HH:MM
                idx = parts.index('at')
                if idx + 1 < len(parts):
                    time_str = parts[idx + 1]
                    hour, minute = map(int, time_str.split(':'))
                    next_run = now.replace(hour=hour, minute=minute, second=0, microsecond=0)
                    if next_run <= now:
                        next_run += timedelta(days=1)
                    return next_run
            
            elif 'hourly' in parts:
                return now.replace(minute=0, second=0, microsecond=0) + timedelta(hours=1)
            
            elif 'weekly' in parts:
                return now + timedelta(weeks=1)
                
        except (ValueError, IndexError):
            pass
        
        # Default: every hour
        return now + timedelta(hours=1)
    
    def _run_task(self, task_id: str):
        """Execute a task."""
        if task_id not in self.tasks:
            return
        
        task = self.tasks[task_id]
        
        if not task.enabled or task.function is None:
            return
        
        # Update status
        task.last_status = TaskStatus.RUNNING
        
        try:
            # Execute function
            task.function(*task.args, **task.kwargs)
            
            # Success
            task.last_run = datetime.utcnow()
            task.last_status = TaskStatus.SUCCESS
            task.last_error = None
            task.run_count += 1
            
        except Exception as e:
            # Failure
            task.last_run = datetime.utcnow()
            task.last_status = TaskStatus.FAILED
            task.last_error = str(e)
            task.fail_count += 1
        
        # Calculate next run
        task.next_run = self._parse_schedule(task.schedule)
        
        # Update database
        if self.db:
            try:
                last_run_str = task.last_run.isoformat() if task.last_run else ''
                next_run_str = task.next_run.isoformat() if task.next_run else ''
                self.db.execute(f"""
                    UPDATE scheduled_tasks 
                    SET last_run = '{last_run_str}',
                        last_status = '{task.last_status.value}',
                        last_error = '{task.last_error or ''}',
                        run_count = {task.run_count},
                        fail_count = {task.fail_count},
                        next_run = '{next_run_str}'
                    WHERE id = '{task_id}'
                """)
            except Exception:
                pass
    
    def start(self):
        """Start the scheduler."""
        if self._running:
            return
        
        self._running = True
        
        def run_scheduler():
            while self._running:
                now = datetime.utcnow()
                
                # Check for tasks to run
                for task in self.tasks.values():
                    if task.enabled and task.function and task.next_run and task.next_run <= now:
                        # Run in separate thread
                        threading.Thread(
                            target=self._run_task,
                            args=(task.id,),
                            daemon=True
                        ).start()
                        
                        # Update next run to prevent duplicate execution
                        task.next_run = self._parse_schedule(task.schedule)
                
                time.sleep(1)  # Check every second
        
        self._thread = threading.Thread(target=run_scheduler, daemon=True)
        self._thread.start()
    
    def stop(self):
        """Stop the scheduler."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=5)
    
    def enable_task(self, task_id: str) -> bool:
        """Enable a task."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = True
        
        if self.db:
            try:
                self.db.execute(f"UPDATE scheduled_tasks SET enabled = 1 WHERE id = '{task_id}'")
            except Exception:
                pass
        
        return True
    
    def disable_task(self, task_id: str) -> bool:
        """Disable a task."""
        if task_id not in self.tasks:
            return False
        
        self.tasks[task_id].enabled = False
        
        if self.db:
            try:
                self.db.execute(f"UPDATE scheduled_tasks SET enabled = 0 WHERE id = '{task_id}'")
            except Exception:
                pass
        
        return True
    
    def delete_task(self, task_id: str) -> bool:
        """Delete a task."""
        if task_id not in self.tasks:
            return False
        
        del self.tasks[task_id]
        
        if self.db:
            try:
                self.db.execute(f"DELETE FROM scheduled_tasks WHERE id = '{task_id}'")
            except Exception:
                pass
        
        return True
    
    def list_tasks(self) -> List[Dict]:
        """List all tasks."""
        return [
            {
                'id': task.id,
                'name': task.name,
                'schedule': task.schedule,
                'enabled': task.enabled,
                'last_run': task.last_run.isoformat() if task.last_run else None,
                'last_status': task.last_status.value if task.last_status else None,
                'last_error': task.last_error,
                'run_count': task.run_count,
                'fail_count': task.fail_count,
                'next_run': task.next_run.isoformat() if task.next_run else None
            }
            for task in self.tasks.values()
        ]
    
    def get_task(self, task_id: str) -> Optional[ScheduledTask]:
        """Get task by ID."""
        return self.tasks.get(task_id)
    
    def run_task_now(self, task_id: str) -> bool:
        """Manually trigger a task."""
        if task_id not in self.tasks:
            return False
        
        threading.Thread(
            target=self._run_task,
            args=(task_id,),
            daemon=True
        ).start()
        
        return True


class CommonTasks:
    """Common scheduled tasks."""
    
    @staticmethod
    def cleanup_old_logs(days: int = 30):
        """Clean up old log files."""
        print(f"[{datetime.now()}] Cleaning up logs older than {days} days")
    
    @staticmethod
    def backup_database():
        """Create database backup."""
        print(f"[{datetime.now()}] Creating database backup")
    
    @staticmethod
    def clear_expired_cache():
        """Clear expired cache entries."""
        print(f"[{datetime.now()}] Clearing expired cache")
    
    @staticmethod
    def send_digest_emails():
        """Send digest emails to users."""
        print(f"[{datetime.now()}] Sending digest emails")
    
    @staticmethod
    def update_search_index():
        """Update search index."""
        print(f"[{datetime.now()}] Updating search index")
    
    @staticmethod
    def check_system_health():
        """Check system health and send alerts."""
        print(f"[{datetime.now()}] Checking system health")


# Alias for compatibility
TaskScheduler = SimpleScheduler

# Global scheduler instance
scheduler = SimpleScheduler()


def setup_common_tasks():
    """Setup common scheduled tasks."""
    # These are registered but need to be started with scheduler.start()
    scheduler.register_task(
        'cleanup_logs',
        'every 7 days',
        CommonTasks.cleanup_old_logs,
        args=(30,)
    )
    
    scheduler.register_task(
        'daily_backup',
        'daily at 02:00',
        CommonTasks.backup_database
    )
    
    scheduler.register_task(
        'clear_cache',
        'every 1 hours',
        CommonTasks.clear_expired_cache
    )
    
    scheduler.register_task(
        'send_digests',
        'daily at 09:00',
        CommonTasks.send_digest_emails
    )
    
    scheduler.register_task(
        'update_search',
        'every 6 hours',
        CommonTasks.update_search_index
    )
    
    scheduler.register_task(
        'health_check',
        'every 15 minutes',
        CommonTasks.check_system_health
    )


# Export
__all__ = [
    'TaskStatus',
    'ScheduledTask',
    'SimpleScheduler',
    'TaskScheduler',
    'scheduler',
    'CommonTasks',
    'setup_common_tasks'
]
