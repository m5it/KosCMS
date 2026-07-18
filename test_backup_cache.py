#!/usr/bin/env python3
"""Test backup and cache endpoints"""

import sys
import os
import json
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from webcms.backup.engine import BackupEngine
from webcms.cache.manager import CacheManager, get_tenant_cache

print("=" * 60)
print("Testing BackupEngine and CacheManager")
print("=" * 60)

# Create mock KosDB
class MockKosDB:
    def __init__(self):
        self._tables = {}
    
    def list_tables(self):
        return list(self._tables.keys())
    
    def execute(self, sql):
        if "CREATE TABLE" in sql.upper():
            table = sql.split("TABLE")[1].split("(")[0].strip()
            self._tables[table] = []
        elif "INSERT INTO" in sql.upper():
            table = sql.split("TABLE")[1].split("(")[0].strip()
            if table not in self._tables:
                self._tables[table] = []
            # Simple parse
            row = {"sql": sql[:50]}
            self._tables[table].append(row)
        elif "UPDATE" in sql.upper() or "DELETE" in sql.upper():
            pass
        return {"success": True}
    
    def query(self, sql):
        table = None
        if "FROM" in sql.upper():
            parts = sql.split("FROM")[1].strip().split()
            if parts:
                table = parts[0].strip().strip("'\"")
        
        if table and table in self._tables:
            return {"rows": self._tables[table]}
        return {"rows": []}

db = MockKosDB()

print("\n1. Testing BackupEngine")
print("-" * 40)

# Create backup engine
be = BackupEngine(db=db, backup_dir="test_backups")

print(f"   Backup dir: {be.backup_dir}")
print(f"   Is KosDB: {be._is_kosdb()}")

# Create a backup
print("\n   Creating backup...")
try:
    backup = be.create_backup("full", "Test Backup")
    print(f"   Created: {backup['id']}")
    print(f"   Status: {backup['status']}")
    print(f"   Size: {backup['size']} bytes")
    print(f"   Tables: {backup['tables']}")
except Exception as e:
    print(f"   Error: {e}")

# List backups
print("\n   Listing backups...")
backups = be.list_backups()
print(f"   Found {len(backups)} backups")
for b in backups:
    print(f"   - {b['id']}: {b['name']} ({b['status']})")

if backups:
    backup_id = backups[0]['id']
    
    # Get backup
    print(f"\n   Getting backup {backup_id}...")
    got = be.get_backup(backup_id)
    if got:
        print(f"   Found: {got['name']}")
    else:
        print("   Not found")
    
    # Verify backup
    print(f"\n   Verifying backup {backup_id}...")
    try:
        valid = be.verify_backup(backup_id)
        print(f"   Valid: {valid}")
    except Exception as e:
        print(f"   Error: {e}")

print("\n2. Testing CacheManager")
print("-" * 40)

# Create cache manager
cache = CacheManager(namespace="test", db=db)

print(f"   Namespace: {cache.namespace}")
print(f"   Is KosDB: {cache._is_kosdb()}")

# Set some values
print("\n   Setting cache values...")
cache.set("key1", "value1", tags=["tag1"])
cache.set("key2", "value2", tags=["tag1", "tag2"])
cache.set("key3", {"data": "test"}, tags=["tag2"])

# Get stats
print("\n   Getting stats...")
stats = cache.get_stats()
print(f"   Keys: {stats['keys']}")
print(f"   Hit rate: {stats['hit_rate']}")
print(f"   Memory: {stats['memory']}")

# Get values
print("\n   Getting values...")
val1 = cache.get("key1")
print(f"   key1: {val1}")

# Invalidate by tag
print("\n   Invalidating tag1...")
deleted = cache.tag_invalidate("tag1")
print(f"   Deleted: {deleted} entries")

# Check stats again
print("\n   Stats after invalidation...")
stats = cache.get_stats()
print(f"   Keys: {stats['keys']}")

# Invalidate by pattern
print("\n   Invalidating pattern 'key*'...")
deleted = cache.invalidate_pattern("key*")
print(f"   Deleted: {deleted} entries")

print("\n3. Testing get_tenant_cache")
print("-" * 40)

tc = get_tenant_cache("default", db=db)
print(f"   Got tenant cache: {tc.namespace}")

# Warm cache
print("\n   Warming cache...")
def data_loader():
    return {"warm1": "data1", "warm2": "data2"}

warmed = tc.tag_warm("warm_tag", data_loader)
print(f"   Warmed: {warmed} entries")

print("\n" + "=" * 60)
print("Backup and Cache test completed")
print("=" * 60)

# Cleanup
import shutil
if os.path.exists("test_backups"):
    shutil.rmtree("test_backups")
