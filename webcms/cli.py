#!/usr/bin/env python3
"""
WebCMS Admin CLI

Command-line interface for managing WebCMS admin panel
"""

import argparse
import sys
import json
import getpass
from datetime import datetime
from typing import Optional


class AdminCLI:
    """Command-line interface for WebCMS admin."""
    
    def __init__(self):
        self.parser = self._create_parser()
    
    def _create_parser(self) -> argparse.ArgumentParser:
        """Create argument parser."""
        parser = argparse.ArgumentParser(
            prog='webcms-admin',
            description='WebCMS Admin Panel CLI',
            formatter_class=argparse.RawDescriptionHelpFormatter,
            epilog="""
Examples:
  %(prog)s user create --username admin --email admin@example.com
  %(prog)s backup create --name "Daily Backup"
  %(prog)s cache clear
  %(prog)s settings get
  %(prog)s settings set site_name "My Website"
            """
        )
        
        subparsers = parser.add_subparsers(dest='command', help='Available commands')
        
        # User commands
        user_parser = subparsers.add_parser('user', help='User management')
        user_subparsers = user_parser.add_subparsers(dest='user_command')
        
        user_create = user_subparsers.add_parser('create', help='Create user')
        user_create.add_argument('--username', required=True)
        user_create.add_argument('--email', required=True)
        user_create.add_argument('--role', default='user')
        user_create.add_argument('--active', action='store_true', default=True)
        
        user_list = user_subparsers.add_parser('list', help='List users')
        user_list.add_argument('--limit', type=int, default=50)
        
        user_delete = user_subparsers.add_parser('delete', help='Delete user')
        user_delete.add_argument('user_id', help='User ID to delete')
        
        # Backup commands
        backup_parser = subparsers.add_parser('backup', help='Backup management')
        backup_subparsers = backup_parser.add_subparsers(dest='backup_command')
        
        backup_create = backup_subparsers.add_parser('create', help='Create backup')
        backup_create.add_argument('--name', help='Backup name')
        
        backup_list = backup_subparsers.add_parser('list', help='List backups')
        
        backup_restore = backup_subparsers.add_parser('restore', help='Restore backup')
        backup_restore.add_argument('backup_id', help='Backup ID to restore')
        
        # Cache commands
        cache_parser = subparsers.add_parser('cache', help='Cache management')
        cache_subparsers = cache_parser.add_subparsers(dest='cache_command')
        
        cache_clear = cache_subparsers.add_parser('clear', help='Clear cache')
        cache_clear.add_argument('--pattern', default='*', help='Cache key pattern')
        
        cache_stats = cache_subparsers.add_parser('stats', help='Cache statistics')
        
        cache_warm = cache_subparsers.add_parser('warm', help='Warm cache')
        
        # Settings commands
        settings_parser = subparsers.add_parser('settings', help='Settings management')
        settings_subparsers = settings_parser.add_subparsers(dest='settings_command')
        
        settings_get = settings_subparsers.add_parser('get', help='Get settings')
        settings_get.add_argument('--key', help='Specific setting key')
        
        settings_set = settings_subparsers.add_parser('set', help='Set setting')
        settings_set.add_argument('key', help='Setting key')
        settings_set.add_argument('value', help='Setting value')
        
        # Content commands
        content_parser = subparsers.add_parser('content', help='Content management')
        content_subparsers = content_parser.add_subparsers(dest='content_command')
        
        content_list = content_subparsers.add_parser('list', help='List content')
        content_list.add_argument('--type', choices=['pages', 'posts'], required=True)
        content_list.add_argument('--limit', type=int, default=50)
        
        content_create = content_subparsers.add_parser('create', help='Create content')
        content_create.add_argument('--type', choices=['page', 'post'], required=True)
        content_create.add_argument('--title', required=True)
        content_create.add_argument('--slug', required=True)
        content_create.add_argument('--content', required=True)
        content_create.add_argument('--status', default='draft')
        
        content_delete = content_subparsers.add_parser('delete', help='Delete content')
        content_delete.add_argument('content_id', help='Content ID to delete')
        
        # System commands
        system_parser = subparsers.add_parser('system', help='System management')
        system_subparsers = system_parser.add_subparsers(dest='system_command')
        
        system_health = system_subparsers.add_parser('health', help='System health')
        system_stats = system_subparsers.add_parser('stats', help='System statistics')
        
        # Task commands
        task_parser = subparsers.add_parser('task', help='Scheduled tasks')
        task_subparsers = task_parser.add_subparsers(dest='task_command')
        
        task_list = task_subparsers.add_parser('list', help='List tasks')
        task_run = task_subparsers.add_parser('run', help='Run task')
        task_run.add_argument('task_id', help='Task ID to run')
        
        # Webhook commands
        webhook_parser = subparsers.add_parser('webhook', help='Webhook management')
        webhook_subparsers = webhook_parser.add_subparsers(dest='webhook_command')
        
        webhook_list = webhook_subparsers.add_parser('list', help='List webhooks')
        webhook_create = webhook_subparsers.add_parser('create', help='Create webhook')
        webhook_create.add_argument('--url', required=True)
        webhook_create.add_argument('--events', nargs='+', required=True)
        webhook_create.add_argument('--secret')
        
        webhook_delete = webhook_subparsers.add_parser('delete', help='Delete webhook')
        webhook_delete.add_argument('webhook_id', help='Webhook ID to delete')
        
        # Info command
        info_parser = subparsers.add_parser('info', help='System information')
        
        return parser
    
    def run(self, args: Optional[list] = None):
        """Run CLI with arguments."""
        parsed = self.parser.parse_args(args)
        
        if not parsed.command:
            self.parser.print_help()
            return 1
        
        try:
            return self._execute(parsed)
        except Exception as e:
            print(f"Error: {e}", file=sys.stderr)
            return 1
    
    def _execute(self, args) -> int:
        """Execute command."""
        command = args.command
        
        if command == 'user':
            return self._handle_user(args)
        elif command == 'backup':
            return self._handle_backup(args)
        elif command == 'cache':
            return self._handle_cache(args)
        elif command == 'settings':
            return self._handle_settings(args)
        elif command == 'content':
            return self._handle_content(args)
        elif command == 'system':
            return self._handle_system(args)
        elif command == 'task':
            return self._handle_task(args)
        elif command == 'webhook':
            return self._handle_webhook(args)
        elif command == 'info':
            return self._handle_info()
        
        return 0
    
    def _handle_user(self, args) -> int:
        """Handle user commands."""
        from webcms.admin.admin_api import AdminAPI
        
        api = AdminAPI(db=None, auth=None)
        
        if args.user_command == 'create':
            # Get password interactively
            password = getpass.getpass("Password: ")
            confirm = getpass.getpass("Confirm: ")
            
            if password != confirm:
                print("Error: Passwords don't match")
                return 1
            
            # Create user
            from webcms.core.request import Request
            
            class MockRequest:
                method = 'POST'
                json = {
                    'username': args.username,
                    'email': args.email,
                    'password': password,
                    'role': args.role,
                    'is_active': args.active
                }
                files = {}
            
            req = MockRequest()
            response = api.create_user(req)
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            if 'id' in body:
                print(f"User created: {body['id']}")
                return 0
            else:
                print(f"Error: {body}")
                return 1
        
        elif args.user_command == 'list':
            from webcms.core.request import Request
            
            class MockRequest:
                method = 'GET'
                json = {}
                files = {}
            
            req = MockRequest()
            response = api.list_users(req)
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            users = body.get('users', [])
            print(f"Total users: {len(users)}")
            print("-" * 50)
            
            for user in users:
                print(f"{user.get('id', 'N/A')[:8]}... | {user.get('username', 'N/A')} | {user.get('email', 'N/A')}")
            
            return 0
        
        elif args.user_command == 'delete':
            print(f"Deleting user: {args.user_id}")
            # Implementation would delete user
            return 0
        
        return 0
    
    def _handle_backup(self, args) -> int:
        """Handle backup commands."""
        if args.backup_command == 'create':
            name = args.name or f"Backup_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            print(f"Creating backup: {name}")
            # Implementation would create backup
            return 0
        
        elif args.backup_command == 'list':
            from webcms.admin.admin_api import AdminAPI
            from webcms.core.request import Request
            
            class MockRequest:
                method = 'GET'
                json = {}
                files = {}
            
            api = AdminAPI(db=None, auth=None)
            response = api.list_backups(MockRequest())
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            backups = body.get('backups', [])
            print(f"Total backups: {len(backups)}")
            
            for backup in backups:
                print(f"{backup.get('id', 'N/A')[:8]}... | {backup.get('name', 'N/A')} | {backup.get('status', 'N/A')}")
            
            return 0
        
        elif args.backup_command == 'restore':
            print(f"Restoring backup: {args.backup_id}")
            # Implementation would restore backup
            return 0
        
        return 0
    
    def _handle_cache(self, args) -> int:
        """Handle cache commands."""
        if args.cache_command == 'clear':
            print(f"Clearing cache with pattern: {args.pattern}")
            # Implementation would clear cache
            return 0
        
        elif args.cache_command == 'stats':
            from webcms.admin.admin_api import AdminAPI
            from webcms.core.request import Request
            
            class MockRequest:
                method = 'GET'
                json = {}
                files = {}
            
            api = AdminAPI(db=None, auth=None)
            response = api.cache_stats(MockRequest())
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            print(f"Cache keys: {body.get('keys', 0)}")
            print(f"Hit rate: {body.get('hit_rate', 0):.2%}")
            print(f"Memory: {body.get('memory', 'N/A')}")
            
            return 0
        
        elif args.cache_command == 'warm':
            print("Warming cache...")
            # Implementation would warm cache
            return 0
        
        return 0
    
    def _handle_settings(self, args) -> int:
        """Handle settings commands."""
        from webcms.admin.admin_api import AdminAPI
        from webcms.core.request import Request
        
        api = AdminAPI(db=None, auth=None)
        
        if args.settings_command == 'get':
            class MockRequest:
                method = 'GET'
                json = {}
                files = {}
            
            response = api.get_settings(MockRequest())
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            settings = body.get('settings', {})
            
            if args.key:
                print(f"{args.key}: {settings.get(args.key, 'Not set')}")
            else:
                print(json.dumps(settings, indent=2))
            
            return 0
        
        elif args.settings_command == 'set':
            class MockRequest:
                method = 'PUT'
                json = {args.key: args.value}
                files = {}
            
            response = api.update_settings(MockRequest())
            
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            if body.get('updated'):
                print(f"Setting updated: {args.key} = {args.value}")
                return 0
            else:
                print(f"Error: {body}")
                return 1
        
        return 0
    
    def _handle_content(self, args) -> int:
        """Handle content commands."""
        if args.content_command == 'list':
            print(f"Listing {args.type}...")
            # Implementation would list content
            return 0
        
        elif args.content_command == 'create':
            print(f"Creating {args.type}: {args.title}")
            # Implementation would create content
            return 0
        
        elif args.content_command == 'delete':
            print(f"Deleting content: {args.content_id}")
            # Implementation would delete content
            return 0
        
        return 0
    
    def _handle_system(self, args) -> int:
        """Handle system commands."""
        if args.system_command == 'health':
            from webcms.health import health
            
            response = health.get_status()
            import json
            body = json.loads(response.body) if isinstance(response.body, bytes) else response.body
            
            print(f"Status: {body.get('status', 'unknown')}")
            print(f"Uptime: {body.get('uptime_seconds', 0)} seconds")
            
            for check in body.get('checks', []):
                status = '✅' if check['status'] == 'healthy' else '❌'
                print(f"{status} {check['name']} ({'critical' if check['critical'] else 'optional'})")
            
            return 0 if body.get('status') == 'healthy' else 1
        
        elif args.system_command == 'stats':
            from webcms.admin.performance_monitor import get_system_metrics
            
            metrics = get_system_metrics()
            
            if 'error' in metrics:
                print(f"Error: {metrics['error']}")
                return 1
            
            print(f"CPU: {metrics.get('cpu_percent', 0):.1f}%")
            print(f"Memory: {metrics['memory']['percent']}% ({metrics['memory']['available_gb']:.1f}GB available)")
            print(f"Disk: {metrics['disk']['percent']}% ({metrics['disk']['free_gb']:.1f}GB free)")
            print(f"Uptime: {metrics['uptime']['days']}d {metrics['uptime']['hours']}h {metrics['uptime']['minutes']}m")
            
            return 0
        
        return 0
    
    def _handle_task(self, args) -> int:
        """Handle task commands."""
        from webcms.admin.scheduler import scheduler
        
        if args.task_command == 'list':
            tasks = scheduler.list_tasks()
            print(f"Scheduled tasks: {len(tasks)}")
            print("-" * 70)
            print(f"{'ID':<12} {'Name':<20} {'Schedule':<20} {'Status':<10}")
            print("-" * 70)
            
            for task in tasks:
                status = task.get('last_status', 'never')
                print(f"{task['id'][:8]}...  {task['name'][:18]:<20} {task['schedule'][:18]:<20} {status:<10}")
            
            return 0
        
        elif args.task_command == 'run':
            success = scheduler.run_task_now(args.task_id)
            if success:
                print(f"Task {args.task_id} triggered")
                return 0
            else:
                print(f"Task not found: {args.task_id}")
                return 1
        
        return 0
    
    def _handle_webhook(self, args) -> int:
        """Handle webhook commands."""
        from webcms.admin.webhooks import webhook_manager
        
        if args.webhook_command == 'list':
            webhooks = webhook_manager.list_webhooks()
            print(f"Webhooks: {len(webhooks)}")
            
            for wh in webhooks:
                print(f"{wh.id[:8]}... | {wh.url[:40]} | {len(wh.events)} events")
            
            return 0
        
        elif args.webhook_command == 'create':
            wh = webhook_manager.create_webhook(
                url=args.url,
                events=args.events,
                secret=args.secret
            )
            print(f"Webhook created: {wh.id}")
            return 0
        
        elif args.webhook_command == 'delete':
            success = webhook_manager.delete_webhook(args.webhook_id)
            if success:
                print(f"Webhook deleted: {args.webhook_id}")
                return 0
            else:
                print(f"Webhook not found: {args.webhook_id}")
                return 1
        
        return 0
    
    def _handle_info(self) -> int:
        """Show system information."""
        print("WebCMS Admin Panel")
        print("=" * 50)
        print(f"Version: 1.0.0")
        print(f"Python: {sys.version.split()[0]}")
        print(f"Platform: {sys.platform}")
        print()
        print("Available commands:")
        print("  user      - User management")
        print("  backup    - Backup management")
        print("  cache     - Cache management")
        print("  settings  - Settings management")
        print("  content   - Content management")
        print("  system    - System management")
        print("  task      - Scheduled tasks")
        print("  webhook   - Webhook management")
        print("  info      - System information")
        
        return 0


def main():
    """Main entry point."""
    cli = AdminCLI()
    sys.exit(cli.run())


if __name__ == '__main__':
    main()
