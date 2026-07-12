#!/usr/bin/env python3
"""Test backup system"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

from webcms.backup import BackupEngine, RestoreManager, BackupScheduler, BackupMonitor, LocalStorage
from webcms.backup.encryption import BackupEncryption


async def test_backup():
    print('Testing backup system...')
    storage = LocalStorage(base_path="test_backups")
    engine = BackupEngine(storage=storage)
    restore = RestoreManager(storage=storage)
    monitor = BackupMonitor()

    full = await engine.backup_database(None, "full")
    print(f'Full backup: {full["backup_id"]}')

    incremental = await engine.incremental_backup(None, ["test_backups/media/logo.png"])
    print(f'Incremental backup: {incremental["database"]["backup_id"]}')

    verification = await restore.verify_backup(full["backup_id"], full)
    print(f'Verification: {verification["valid"]}')

    restore_result = await restore.one_click_restore(full["backup_id"], None)
    print(f'Restore: {restore_result.get("restored", False)}')

    monitor.record_backup(full["backup_id"], "success", full)
    status = monitor.get_status()
    print(f'Monitor status: {status}')

    scheduler = BackupScheduler()
    async def dummy_task():
        print('Scheduled backup ran')
    scheduler.schedule("hourly", 1, dummy_task)
    print(f'Schedule: {scheduler.get_schedule()}')

    encryption = BackupEncryption()
    encrypted = encryption.encrypt("sensitive backup data")
    decrypted = encryption.decrypt(encrypted)
    print(f'Encryption works: {decrypted == "sensitive backup data"}')

    print('Backup system verified!')


if __name__ == '__main__':
    asyncio.run(test_backup())
