"""
Backup engine with incremental database and media backups.
"""

import json
import hashlib
from datetime import datetime
from typing import Dict, List, Optional


class BackupEngine:
    """Creates and manages backups."""

    def __init__(self, storage=None):
        self.storage = storage
        self._backups: List[Dict] = []

    async def backup_database(self, db_connection, backup_type="full") -> Dict:
        """Backup database."""
        timestamp = datetime.utcnow().isoformat()
        backup_id = f"db_{backup_type}_{int(datetime.utcnow().timestamp())}"

        # Placeholder: real implementation dumps database
        data = {
            "backup_id": backup_id,
            "type": backup_type,
            "timestamp": timestamp,
            "tables": ["posts", "pages", "users", "media"],
            "checksum": hashlib.sha256(backup_id.encode()).hexdigest()
        }

        if self.storage:
            await self.storage.store(f"{backup_id}.json", json.dumps(data))

        self._backups.append(data)
        return data

    async def backup_media(self, media_files: List[str]) -> Dict:
        """Backup media assets."""
        timestamp = datetime.utcnow().isoformat()
        backup_id = f"media_{int(datetime.utcnow().timestamp())}"

        uploaded = []
        for file_path in media_files:
            if self.storage:
                key = await self.storage.store_file(file_path)
                uploaded.append(key)

        data = {
            "backup_id": backup_id,
            "type": "media",
            "timestamp": timestamp,
            "files": uploaded,
            "count": len(uploaded)
        }
        self._backups.append(data)
        return data

    async def incremental_backup(self, db_connection, changed_files: List[str]) -> Dict:
        """Incremental backup of changed data."""
        db_backup = await self.backup_database(db_connection, backup_type="incremental")
        media_backup = await self.backup_media(changed_files)
        return {
            "type": "incremental",
            "timestamp": datetime.utcnow().isoformat(),
            "database": db_backup,
            "media": media_backup
        }

    def list_backups(self) -> List[Dict]:
        """List all backups."""
        return sorted(self._backups, key=lambda x: x["timestamp"], reverse=True)

    def get_backup(self, backup_id: str) -> Optional[Dict]:
        """Get backup by ID."""
        for backup in self._backups:
            if backup["backup_id"] == backup_id:
                return backup
        return None
