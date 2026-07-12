#!/usr/bin/env python3
"""Integration tests for backup system."""

import pytest
from webcms.backup import BackupEngine, RestoreManager, LocalStorage


@pytest.mark.asyncio
async def test_full_backup_and_restore():
    storage = LocalStorage(base_path="test_backups_integration")
    engine = BackupEngine(storage=storage)
    restore = RestoreManager(storage=storage)

    backup = await engine.backup_database(None, "full")
    assert backup["type"] == "full"

    verification = await restore.verify_backup(backup["backup_id"], backup)
    assert verification["valid"] is True

    result = await restore.one_click_restore(backup["backup_id"], None)
    assert result["restored"] is True


@pytest.mark.asyncio
async def test_media_backup():
    storage = LocalStorage(base_path="test_backups_integration")
    engine = BackupEngine(storage=storage)
    result = await engine.backup_media(["test_backups/media/logo.png"])
    assert result["count"] == 1
