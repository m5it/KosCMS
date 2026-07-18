"""
Database Migration System

Provides schema versioning and migration management for WebCMS
"""

import os
import re
import hashlib
from datetime import datetime
from typing import Dict, List, Optional, Callable, Tuple
from dataclasses import dataclass


@dataclass
class Migration:
    """Represents a single migration."""
    version: str
    name: str
    applied_at: Optional[datetime]
    checksum: str
    up_sql: str
    down_sql: str


class MigrationManager:
    """Manages database migrations."""
    
    def __init__(self, db, migrations_dir: str = 'migrations'):
        self.db = db
        self.migrations_dir = migrations_dir
        self._ensure_table()
    
    def _ensure_table(self):
        """Ensure migrations table exists."""
        if not self.db:
            return
        
        try:
            tables = self.db.list_tables()
            if 'schema_migrations' not in tables:
                self.db.execute("""
                    CREATE TABLE schema_migrations (
                        version TEXT PRIMARY KEY,
                        name TEXT NOT NULL,
                        applied_at TEXT NOT NULL,
                        checksum TEXT NOT NULL
                    )
                """)
        except Exception as e:
            print(f"Warning: Could not create migrations table: {e}")
    
    def create_migration(self, name: str, up_sql: str, down_sql: str = '') -> str:
        """
        Create a new migration file.
        
        Args:
            name: Migration name (e.g., 'add_users_table')
            up_sql: SQL to apply migration
            down_sql: SQL to rollback migration
        
        Returns:
            Migration version string
        """
        # Generate version timestamp
        version = datetime.now().strftime('%Y%m%d%H%M%S')
        
        # Sanitize name
        safe_name = re.sub(r'[^a-zA-Z0-9_]', '_', name).lower()
        
        # Create migrations directory
        os.makedirs(self.migrations_dir, exist_ok=True)
        
        # Migration filename
        filename = f"{version}_{safe_name}.sql"
        filepath = os.path.join(self.migrations_dir, filename)
        
        # Write migration file
        with open(filepath, 'w') as f:
            f.write(f"-- Migration: {name}\n")
            f.write(f"-- Version: {version}\n")
            f.write(f"-- Created: {datetime.now().isoformat()}\n")
            f.write("\n-- +migrate Up\n")
            f.write(up_sql)
            f.write("\n\n-- +migrate Down\n")
            f.write(down_sql if down_sql else '-- No rollback')
            f.write("\n")
        
        print(f"Created migration: {filepath}")
        return version
    
    def _parse_migration_file(self, filepath: str) -> Tuple[str, str]:
        """Parse migration file into up and down SQL."""
        with open(filepath, 'r') as f:
            content = f.read()
        
        # Split into up and down sections
        up_match = re.search(r'-- \+migrate Up\s+(.*?)(?=\n-- \+migrate Down|$)', content, re.DOTALL)
        down_match = re.search(r'-- \+migrate Down\s+(.*)$', content, re.DOTALL)
        
        up_sql = up_match.group(1).strip() if up_match else ''
        down_sql = down_match.group(1).strip() if down_match else ''
        
        return up_sql, down_sql
    
    def _calculate_checksum(self, content: str) -> str:
        """Calculate checksum of migration content."""
        return hashlib.sha256(content.encode()).hexdigest()[:16]
    
    def get_pending_migrations(self) -> List[Migration]:
        """Get list of pending migrations."""
        if not os.path.exists(self.migrations_dir):
            return []
        
        # Get all migration files
        files = sorted([
            f for f in os.listdir(self.migrations_dir)
            if f.endswith('.sql') and re.match(r'^\d+_', f)
        ])
        
        # Get applied migrations from database
        applied = set()
        if self.db:
            try:
                result = self.db.query("SELECT version FROM schema_migrations")
                applied = {row['version'] for row in result.get('rows', [])}
            except Exception:
                pass
        
        pending = []
        for filename in files:
            # Extract version from filename
            match = re.match(r'^(\d+)_(.+)\.sql$', filename)
            if not match:
                continue
            
            version = match.group(1)
            name = match.group(2).replace('_', ' ')
            
            if version not in applied:
                filepath = os.path.join(self.migrations_dir, filename)
                with open(filepath, 'r') as f:
                    content = f.read()
                
                up_sql, down_sql = self._parse_migration_file(filepath)
                
                pending.append(Migration(
                    version=version,
                    name=name,
                    applied_at=None,
                    checksum=self._calculate_checksum(content),
                    up_sql=up_sql,
                    down_sql=down_sql
                ))
        
        return pending
    
    def migrate(self, target: Optional[str] = None, dry_run: bool = False) -> Dict:
        """
        Run pending migrations.
        
        Args:
            target: Target version (None = latest)
            dry_run: Show what would be done without executing
        
        Returns:
            Migration results
        """
        if not self.db:
            return {'success': False, 'error': 'No database connection'}
        
        pending = self.get_pending_migrations()
        
        if target:
            pending = [m for m in pending if m.version <= target]
        
        if not pending:
            print("No pending migrations")
            return {'success': True, 'migrations': []}
        
        results = []
        
        for migration in pending:
            print(f"Migrating: {migration.version} - {migration.name}")
            
            if dry_run:
                print(f"  [DRY RUN] Would execute:\n{migration.up_sql[:200]}...")
                results.append({
                    'version': migration.version,
                    'status': 'dry_run',
                    'name': migration.name
                })
                continue
            
            try:
                # Execute migration
                self.db.execute(migration.up_sql)
                
                # Record migration
                self.db.execute(f"""
                    INSERT INTO schema_migrations (version, name, applied_at, checksum)
                    VALUES (
                        '{migration.version}',
                        '{migration.name}',
                        '{datetime.now().isoformat()}',
                        '{migration.checksum}'
                    )
                """)
                
                results.append({
                    'version': migration.version,
                    'status': 'applied',
                    'name': migration.name
                })
                print(f"  ✓ Applied")
                
            except Exception as e:
                results.append({
                    'version': migration.version,
                    'status': 'failed',
                    'name': migration.name,
                    'error': str(e)
                })
                print(f"  ✗ Failed: {e}")
                break
        
        successful = sum(1 for r in results if r['status'] in ('applied', 'dry_run'))
        
        return {
            'success': successful == len(results),
            'migrations': results,
            'applied': successful,
            'failed': len(results) - successful
        }
    
    def rollback(self, steps: int = 1, dry_run: bool = False) -> Dict:
        """
        Rollback migrations.
        
        Args:
            steps: Number of migrations to rollback
            dry_run: Show what would be done without executing
        
        Returns:
            Rollback results
        """
        if not self.db:
            return {'success': False, 'error': 'No database connection'}
        
        # Get applied migrations
        try:
            result = self.db.query(
                "SELECT version, name FROM schema_migrations "
                "ORDER BY version DESC"
            )
            applied = result.get('rows', [])
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        if not applied:
            print("No migrations to rollback")
            return {'success': True, 'migrations': []}
        
        to_rollback = applied[:steps]
        results = []
        
        for record in to_rollback:
            version = record['version']
            name = record['name']
            
            # Find migration file
            filename = f"{version}_{name.replace(' ', '_')}.sql"
            filepath = os.path.join(self.migrations_dir, filename)
            
            if not os.path.exists(filepath):
                results.append({
                    'version': version,
                    'status': 'skipped',
                    'name': name,
                    'error': 'Migration file not found'
                })
                continue
            
            # Parse down SQL
            _, down_sql = self._parse_migration_file(filepath)
            
            if not down_sql or down_sql == '-- No rollback':
                results.append({
                    'version': version,
                    'status': 'skipped',
                    'name': name,
                    'error': 'No rollback available'
                })
                continue
            
            print(f"Rolling back: {version} - {name}")
            
            if dry_run:
                print(f"  [DRY RUN] Would execute:\n{down_sql[:200]}...")
                results.append({
                    'version': version,
                    'status': 'dry_run',
                    'name': name
                })
                continue
            
            try:
                # Execute rollback
                self.db.execute(down_sql)
                
                # Remove migration record
                self.db.execute(f"DELETE FROM schema_migrations WHERE version = '{version}'")
                
                results.append({
                    'version': version,
                    'status': 'rolled_back',
                    'name': name
                })
                print(f"  ✓ Rolled back")
                
            except Exception as e:
                results.append({
                    'version': version,
                    'status': 'failed',
                    'name': name,
                    'error': str(e)
                })
                print(f"  ✗ Failed: {e}")
                break
        
        successful = sum(1 for r in results if r['status'] in ('rolled_back', 'dry_run'))
        
        return {
            'success': successful == len(results),
            'migrations': results,
            'rolled_back': successful,
            'failed': len(results) - successful
        }
    
    def status(self) -> Dict:
        """Get migration status."""
        pending = self.get_pending_migrations()
        
        applied_count = 0
        if self.db:
            try:
                result = self.db.query("SELECT COUNT(*) as count FROM schema_migrations")
                applied_count = result.get('rows', [{}])[0].get('count', 0)
            except Exception:
                pass
        
        return {
            'pending': len(pending),
            'applied': applied_count,
            'latest': pending[-1].version if pending else None,
            'migrations_dir': self.migrations_dir
        }
    
    def verify(self) -> Dict:
        """Verify migration checksums."""
        if not self.db:
            return {'success': False, 'error': 'No database connection'}
        
        try:
            result = self.db.query("SELECT version, name, checksum FROM schema_migrations")
            records = result.get('rows', [])
        except Exception as e:
            return {'success': False, 'error': str(e)}
        
        verified = 0
        mismatched = []
        missing = []
        
        for record in records:
            version = record['version']
            name = record['name']
            expected_checksum = record['checksum']
            
            filename = f"{version}_{name.replace(' ', '_')}.sql"
            filepath = os.path.join(self.migrations_dir, filename)
            
            if not os.path.exists(filepath):
                missing.append({'version': version, 'name': name})
                continue
            
            with open(filepath, 'r') as f:
                content = f.read()
            
            actual_checksum = self._calculate_checksum(content)
            
            if actual_checksum != expected_checksum:
                mismatched.append({
                    'version': version,
                    'name': name,
                    'expected': expected_checksum,
                    'actual': actual_checksum
                })
            else:
                verified += 1
        
        return {
            'success': len(mismatched) == 0 and len(missing) == 0,
            'verified': verified,
            'mismatched': mismatched,
            'missing': missing
        }


# Common migrations
class CommonMigrations:
    """Common migration templates."""
    
    @staticmethod
    def create_table(name: str, columns: Dict[str, str]) -> str:
        """Generate CREATE TABLE migration."""
        cols = ',\n    '.join([f"{col} {dtype}" for col, dtype in columns.items()])
        return f"CREATE TABLE {name} (\n    {cols}\n);"
    
    @staticmethod
    def add_column(table: str, column: str, dtype: str) -> str:
        """Generate ADD COLUMN migration."""
        return f"ALTER TABLE {table} ADD COLUMN {column} {dtype};"
    
    @staticmethod
    def create_index(table: str, columns: List[str], unique: bool = False) -> str:
        """Generate CREATE INDEX migration."""
        index_name = f"idx_{table}_{'_'.join(columns)}"
        unique_str = "UNIQUE " if unique else ""
        cols = ', '.join(columns)
        return f"CREATE {unique_str}INDEX {index_name} ON {table} ({cols});"


# Export
__all__ = [
    'Migration',
    'MigrationManager',
    'CommonMigrations'
]
