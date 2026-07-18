"""
Backup engine with KosDB persistence.
"""

import json
import hashlib
import os
import shutil
import tarfile
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path


class BackupEngine:
    """Creates and manages backups with KosDB persistence."""

    def __init__(self, storage=None, db=None, backup_dir: str = "backups"):
        self.storage = storage
        self.db = db
        self.backup_dir = Path(backup_dir)
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        self._ensure_backups_table()

    def _is_kosdb(self) -> bool:
        """Check if database is KosDB."""
        if self.db is None:
            return False
        has_methods = all(
            hasattr(self.db, method) 
            for method in ['execute', 'query', 'list_tables']
        )
        return has_methods

    def _ensure_backups_table(self):
        """Ensure backups table exists in KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = self.db.list_tables()
            if 'backups' in tables:
                return
        except Exception:
            pass

        try:
            self.db.execute("""
                CREATE TABLE backups (
                    backup_id TEXT PRIMARY KEY,
                    name TEXT,
                    type TEXT,
                    status TEXT,
                    size INTEGER,
                    checksum TEXT,
                    tables TEXT,
                    files_count INTEGER,
                    created_at TEXT,
                    completed_at TEXT,
                    metadata TEXT
                )
            """)
        except Exception:
            pass

    def _get_backup_path(self, backup_id: str) -> Path:
        """Get path for backup file."""
        return self.backup_dir / f"{backup_id}.tar.gz"

    def _get_metadata_path(self, backup_id: str) -> Path:
        """Get path for backup metadata."""
        return self.backup_dir / f"{backup_id}.json"

    async def backup_database(self, db_connection, backup_type="full") -> Dict:
        """Backup database."""
        return self.create_backup(backup_type)

    def create_backup(self, backup_type: str = "full", name: str = None) -> Dict:
        """Create a new backup (sync version for admin API)."""
        timestamp = datetime.utcnow()
        backup_id = f"backup_{int(timestamp.timestamp())}"
        
        if name is None:
            name = f"Backup {timestamp.strftime('%Y-%m-%d %H:%M:%S')}"

        # Create backup metadata
        backup_data = {
            "id": backup_id,
            "name": name,
            "type": backup_type,
            "status": "in_progress",
            "timestamp": timestamp.isoformat(),
            "tables": ["posts", "pages", "users", "media", "templates", "themes"],
            "files_count": 0,
            "size": 0,
            "checksum": None,
            "metadata": {}
        }

        try:
            # Create actual backup archive
            backup_path = self._get_backup_path(backup_id)
            
            # Create tar.gz archive of data directory
            data_dir = Path("data")
            if data_dir.exists():
                with tarfile.open(backup_path, "w:gz") as tar:
                    tar.add(data_dir, arcname="data")
                
                # Calculate size and checksum
                backup_data["size"] = backup_path.stat().st_size
                with open(backup_path, 'rb') as f:
                    backup_data["checksum"] = hashlib.sha256(f.read()).hexdigest()
                
                backup_data["files_count"] = len(list(data_dir.rglob("*")))

            backup_data["status"] = "completed"
            backup_data["completed_at"] = datetime.utcnow().isoformat()

            # Save metadata to file
            metadata_path = self._get_metadata_path(backup_id)
            with open(metadata_path, 'w') as f:
                json.dump(backup_data, f, indent=2)

            # Persist to KosDB if available
            if self.db and self._is_kosdb():
                self._save_to_kosdb(backup_data)

        except Exception as e:
            backup_data["status"] = "failed"
            backup_data["error"] = str(e)

        # Ensure id key exists
        if "id" not in backup_data:
            backup_data["id"] = backup_data.get("backup_id")
        
        return backup_data

    def _save_to_kosdb(self, backup_data: Dict):
        """Save backup metadata to KosDB."""
        if not self.db or not self._is_kosdb():
            return

        try:
            tables = json.dumps(backup_data.get("tables", []))
            metadata = json.dumps(backup_data.get("metadata", {}))
            
            self.db.execute(f"""
                INSERT INTO backups 
                (backup_id, name, type, status, size, checksum, tables, files_count, created_at, completed_at, metadata)
                VALUES (
                    '{backup_data['id']}',
                    '{backup_data['name']}',
                    '{backup_data['type']}',
                    '{backup_data['status']}',
                    {backup_data.get('size', 0)},
                    '{backup_data.get('checksum', '')}',
                    '{tables}',
                    {backup_data.get('files_count', 0)},
                    '{backup_data['timestamp']}',
                    '{backup_data.get('completed_at', '')}',
                    '{metadata}'
                )
            """)
        except Exception:
            pass

    def list_backups(self) -> List[Dict]:
        """List all backups."""
        backups = []
        
        # Load from filesystem
        for metadata_file in self.backup_dir.glob("*.json"):
            try:
                with open(metadata_file, 'r') as f:
                    backup_data = json.load(f)
                    backups.append(backup_data)
            except Exception:
                continue
        
        # Load from KosDB if available
        if self.db and self._is_kosdb():
            try:
                result = self.db.query("SELECT * FROM backups ORDER BY created_at DESC")
                for row in result.get('rows', []):
                    backup = {
                        "id": row['backup_id'],
                        "name": row['name'],
                        "type": row['type'],
                        "status": row['status'],
                        "size": row['size'],
                        "checksum": row['checksum'],
                        "tables": json.loads(row['tables']) if row.get('tables') else [],
                        "files_count": row['files_count'],
                        "timestamp": row['created_at'],
                        "completed_at": row.get('completed_at')
                    }
                    if backup['id'] not in [b['id'] for b in backups]:
                        backups.append(backup)
            except Exception:
                pass
        
        return sorted(backups, key=lambda x: x.get('timestamp', ''), reverse=True)

    def get_backup(self, backup_id: str) -> Optional[Dict]:
        """Get backup by ID."""
        # Try filesystem first
        metadata_path = self._get_metadata_path(backup_id)
        if metadata_path.exists():
            try:
                with open(metadata_path, 'r') as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Try KosDB
        if self.db and self._is_kosdb():
            try:
                result = self.db.query(f"SELECT * FROM backups WHERE backup_id='{backup_id}'")
                rows = result.get('rows', [])
                if rows:
                    row = rows[0]
                    return {
                        "id": row['backup_id'],
                        "name": row['name'],
                        "type": row['type'],
                        "status": row['status'],
                        "size": row['size'],
                        "checksum": row['checksum'],
                        "tables": json.loads(row['tables']) if row.get('tables') else [],
                        "files_count": row['files_count'],
                        "timestamp": row['created_at'],
                        "completed_at": row.get('completed_at')
                    }
            except Exception:
                pass
        
        return None

    def delete_backup(self, backup_id: str) -> bool:
        """Delete backup."""
        success = False
        
        # Delete from filesystem
        backup_path = self._get_backup_path(backup_id)
        metadata_path = self._get_metadata_path(backup_id)
        
        try:
            if backup_path.exists():
                backup_path.unlink()
            if metadata_path.exists():
                metadata_path.unlink()
            success = True
        except Exception:
            pass
        
        # Delete from KosDB
        if self.db and self._is_kosdb():
            try:
                self.db.execute(f"DELETE FROM backups WHERE backup_id='{backup_id}'")
                success = True
            except Exception:
                pass
        
        return success

    def restore_backup(self, backup_id: str, target_dir: str = "data") -> Dict:
        """Restore from backup."""
        backup_path = self._get_backup_path(backup_id)
        
        if not backup_path.exists():
            return {"error": "Backup not found", "success": False}
        
        try:
            # Extract archive
            target = Path(target_dir)
            target.mkdir(parents=True, exist_ok=True)
            
            with tarfile.open(backup_path, "r:gz") as tar:
                tar.extractall(path=target.parent)
            
            return {"success": True, "restored_to": str(target)}
        except Exception as e:
            return {"error": str(e), "success": False}

    def verify_backup(self, backup_id: str) -> Dict:
        """Verify backup integrity."""
        backup = self.get_backup(backup_id)
        if not backup:
            return {"valid": False, "error": "Backup not found"}
        
        backup_path = self._get_backup_path(backup_id)
        if not backup_path.exists():
            return {"valid": False, "error": "Backup file not found"}
        
        # Verify checksum
        if backup.get('checksum'):
            with open(backup_path, 'rb') as f:
                actual_checksum = hashlib.sha256(f.read()).hexdigest()
            if actual_checksum != backup['checksum']:
                return {"valid": False, "error": "Checksum mismatch"}
        
        return {"valid": True, "backup": backup}

    def get_stats(self) -> Dict:
        """Get backup statistics."""
        backups = self.list_backups()
        total_size = sum(b.get('size', 0) for b in backups)
        
        return {
            "total_backups": len(backups),
            "total_size": total_size,
            "total_size_mb": round(total_size / (1024 * 1024), 2),
            "last_backup": backups[0]['timestamp'] if backups else None
        }

    def cleanup_old_backups(self, keep_count: int = 10) -> int:
        """Delete old backups keeping only the most recent."""
        backups = self.list_backups()
        if len(backups) <= keep_count:
            return 0
        
        deleted = 0
        for backup in backups[keep_count:]:
            if self.delete_backup(backup['id']):
                deleted += 1
        
        return deleted
