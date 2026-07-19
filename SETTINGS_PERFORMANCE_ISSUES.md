# Settings Save Performance Issues

## Overview
Saving settings on `/admin/settings` takes 10-30 seconds. The root cause is a
combination of CMS-side architecture issues and KosDB-side missing features.

---

## Fixes Completed in This Repository

The following optimizations have been implemented in the webcms codebase:

### ✅ Issue 1: N+1 Query Problem — FIXED
**File:** `webcms/admin/admin_api.py:1321-1376`

`update_settings()` now loads all existing keys with a single `SELECT` before
the write loop, then uses INSERT or UPDATE per key based on an in-memory set.
This cuts round-trips from 2N to N+1.

**Implementation:**
```python
# OPTIMIZATION: Load all existing keys in a single query
existing_keys_result = self.db.query("SELECT setting_key FROM settings")
existing_keys = {
    row.get('setting_key')
    for row in existing_keys_result.get('rows', [])
    if row.get('setting_key')
}
# Then decide INSERT vs UPDATE per key without second SELECT
```

### ✅ Issue 2: Pool Acquire/Release Overhead — FIXED
**File:** `webcms/database/kosdb_client.py:485-565`

Added `KosDBClient.transaction()` context manager that acquires a single
connection for multiple operations, avoiding repeated pool acquire/release
and ping overhead.

**Usage:**
```python
with self.db.transaction() as conn:
    # All operations share one connection
    existing = conn.query("SELECT setting_key FROM settings")
    for key, value in settings.items():
        conn.execute(f"UPDATE ...")
```

### ✅ Issue 2b: Ping Skip Optimization — FIXED
**File:** `webcms/database/kosdb_client.py:45, 334-346`

Added `max_ping_interval` config (default 5s) to skip the `ping()` round-trip
if the connection was used within the last few seconds. Logs at debug level
when ping is skipped.

**Configuration:**
```python
@dataclass
class KosDBConfig:
    max_ping_interval: float = 5.0  # Skip ping if used within 5s
```

### ✅ Issue 6: Connection Reuse Within Request — FIXED
**File:** `webcms/admin/admin_api.py:1330-1376`

The KosDB path now uses `self.db.transaction()` context manager when
available, holding a single connection for the entire settings save operation.

**Implementation:**
```python
if hasattr(self.db, 'transaction'):
    with self.db.transaction() as conn:
        # All SELECT/UPDATE/INSERT operations share one connection
        ...
else:
    # Fallback for legacy KosDB interfaces
    ...
```

---

## Fixes Requiring External test.KosDB Project Changes

The following features require changes to the external `test.KosDB` project
(LevelDB socket server). These cannot be implemented in this repository alone.

### 🔧 Issue 3: Add UPSERT Support
**Required Files:** `test.KosDB/commands.py`, `test.KosDB/database.py`

KosDB has no `UPSERT` or `INSERT OR UPDATE` command. The CMS must do two
round-trips (SELECT + INSERT/UPDATE) for every setting.

**Recommended Implementation:**

Add new command parser in `test.KosDB/commands.py`:
```python
# New command: INSERT OR UPDATE
elif cmd_upper.startswith("INSERT OR UPDATE INTO"):
    # Parse: INSERT OR UPDATE INTO table (cols) VALUES (vals)
    return self._handle_upsert(parts)
```

**Recommended SQL Syntax:**
```sql
-- Standard UPSERT syntax
INSERT OR UPDATE INTO settings (setting_key, value, type)
VALUES ('site_name', 'KosCMS', 'str');

-- Alternative: MySQL-style ON DUPLICATE KEY UPDATE
INSERT INTO settings (setting_key, value, type)
VALUES ('site_name', 'KosCMS', 'str')
ON DUPLICATE KEY UPDATE value='KosCMS', type='str';
```

**LevelDB Implementation** in `test.KosDB/database.py`:
```python
def upsert(self, table: str, key_col: str, data: dict) -> bool:
    """
    Insert or update a row atomically using LevelDB batch.
    """
    from leveldb import WriteBatch
    
    batch = WriteBatch()
    row_key = f"{table}:{key_col}:{data[key_col]}"
    
    # Check if exists (LevelDB Get)
    existing = self.db.Get(row_key.encode())
    
    # Write the row data
    batch.Put(row_key.encode(), json.dumps(data).encode())
    
    # Update index if needed
    if existing:
        batch.Delete(row_key.encode())  # Remove old index entry
    
    self.db.Write(batch)
    return True
```

**Impact:** Cuts per-setting queries from 2 to 1 (30 → 15 round-trips for 15 settings).

---

### 🔧 Issue 4: Add BEGIN/COMMIT Transaction Support
**Required Files:** `test.KosDB/commands.py`, `test.KosDB/server.py`, `test.KosDB/database.py`

KosDB has no `BEGIN`/`COMMIT` transaction support. Each query is an isolated
LevelDB operation. Even with CMS batching, there's no way to atomicize multiple
writes.

**Recommended Implementation:**

**In `test.KosDB/server.py` - ClientHandler:**
```python
class ClientHandler(threading.Thread):
    def __init__(self, ...):
        ...
        self.transaction_active = False
        self.transaction_batch = None  # WriteBatch instance
        
    def handle_command(self, cmd: str):
        cmd_upper = cmd.upper().strip()
        
        if cmd_upper == "BEGIN":
            self.transaction_active = True
            self.transaction_batch = WriteBatch()
            return "OK Transaction started"
            
        elif cmd_upper == "COMMIT":
            if not self.transaction_active:
                return "ERROR No active transaction"
            self.db.Write(self.transaction_batch)
            self.transaction_active = False
            self.transaction_batch = None
            return "OK Transaction committed"
            
        elif cmd_upper == "ROLLBACK":
            self.transaction_active = False
            self.transaction_batch = None
            return "OK Transaction rolled back"
        
        # Normal query execution
        if self.transaction_active:
            # Defer writes to batch, return tentative OK
            return self._defer_to_transaction(cmd)
        else:
            return self._execute_immediate(cmd)
```

**Recommended SQL Syntax:**
```sql
BEGIN;
UPDATE settings SET value='KosCMS' WHERE setting_key='site_name';
UPDATE settings SET value='en' WHERE setting_key='default_language';
INSERT INTO settings (setting_key, value, type) 
VALUES ('new_setting', 'value', 'str');
COMMIT;
```

**Impact:** Allows the CMS to send all 15 updates in one network round-trip
as a single atomic batch. Cuts round-trips from N+1 (16) to 2 (BEGIN + COMMIT).

---

### 🔧 Issue 5: Add WriteBatch Bulk Write Support
**Required Files:** `test.KosDB/commands.py`, `test.KosDB/database.py`

Even without full transactions, KosDB could support bulk write operations
using LevelDB's native WriteBatch.

**Recommended Implementation:**

**In `test.KosDB/commands.py`:**
```python
# New command: BATCH INSERT
elif cmd_upper.startswith("BATCH INSERT INTO"):
    return self._handle_batch_insert(parts)
```

**Recommended SQL Syntax:**
```sql
-- Batch insert multiple rows in one operation
BATCH INSERT INTO settings (setting_key, value, type) VALUES
    ('site_name', 'KosCMS', 'str'),
    ('default_language', 'en', 'str'),
    ('posts_per_page', '10', 'int');

-- Batch update
BATCH UPDATE settings SET value='updated' WHERE setting_key IN 
    ('key1', 'key2', 'key3');
```

**LevelDB Implementation** in `test.KosDB/database.py`:
```python
def batch_insert(self, table: str, columns: list, rows: list) -> bool:
    """
    Insert multiple rows atomically using WriteBatch.
    """
    from leveldb import WriteBatch
    
    batch = WriteBatch()
    for row in rows:
        key = f"{table}:{columns[0]}:{row[0]}"  # Primary key lookup
        data = dict(zip(columns, row))
        batch.Put(key.encode(), json.dumps(data).encode())
    
    self.db.Write(batch)
    return True
```

**Impact:** Cuts 15 individual INSERT/UPDATE round-trips to 1 batch operation.

---

### 🔧 Issue 5b: Single-Threaded Write Queue Optimization
**Required Files:** `test.KosDB/server.py`, `test.KosDB/database.py`

KosDB uses a single `Database` instance shared across all `ClientHandler`
threads. LevelDB's writes are serialized through the database instance.

**Recommended Implementation:**

**In `test.KosDB/database.py` - WriteQueue:**
```python
import queue
import threading

class Database:
    def __init__(self, path: str):
        self.db = leveldb.LevelDB(path)
        self.write_queue = queue.Queue()
        self.write_thread = threading.Thread(target=self._write_worker, daemon=True)
        self.write_thread.start()
        
    def _write_worker(self):
        """Background thread for serialized writes."""
        while True:
            batch, result_callback = self.write_queue.get()
            try:
                self.db.Write(batch)
                result_callback(True, None)
            except Exception as e:
                result_callback(False, str(e))
            finally:
                self.write_queue.task_done()
    
    def async_write(self, batch) -> Future:
        """Queue a write operation."""
        future = Future()
        self.write_queue.put((batch, lambda ok, err: future.set_result(ok, err)))
        return future
```

**Impact:** Prevents write starvation when multiple clients write simultaneously.

---

## Summary

### Completed in This Repository (webcms)

| Issue | File | Description | Impact |
|-------|------|-------------|--------|
| N+1 Query | `admin/admin_api.py` | Single SELECT for all keys | 30 → 16 queries |
| Transaction Context | `database/kosdb_client.py` | Reuse connection across ops | -30 ping round-trips |
| Ping Skip | `database/kosdb_client.py` | Skip ping if recently used | -N ping round-trips |
| Connection Reuse | `admin/admin_api.py` | Use transaction() in update_settings | Pool efficiency |

### Requires External test.KosDB Changes

| Issue | Files | Description | Impact |
|-------|-------|-------------|--------|
| UPSERT | `commands.py`, `database.py` | INSERT OR UPDATE command | 16 → 8 queries |
| Transactions | `server.py`, `commands.py` | BEGIN/COMMIT support | 16 → 2 round-trips |
| WriteBatch | `commands.py`, `database.py` | Bulk INSERT/UPDATE | 16 → 1 round-trip |
| Write Queue | `server.py`, `database.py` | Async write serialization | Prevents starvation |

**Quick win (completed):** CMS-side fixes cut queries from 30 to ~16.

**Best fix (external):** Add UPSERT + transactions to KosDB → enables single
round-trip saves with atomic guarantees.
**File:** `webcms/admin/admin_api.py:1325-1361`
**Impact:** 30+ round-trips for 15 settings

`update_settings()` processes each setting **one at a time** with a
check-then-write pattern:

```python
for key, value in normalized.items():
    # 1. SELECT to check if exists  → pool acquire → ping → query → pool release
    check = self.db.query(f"SELECT setting_key FROM settings WHERE setting_key='{key}'")
    # 2. INSERT or UPDATE           → pool acquire → ping → query → pool release
    result = self.db.execute(cmd)
```

For 15 settings = **30 pool acquire/release cycles**, each involving a
`ping()` round-trip + the actual query = **60 network round-trips**.

### Fix
Load all existing keys once with a single `SELECT setting_key FROM settings`,
then batch the updates/inserts:

```python
# One query to get all existing keys
existing = self.db.query("SELECT setting_key FROM settings")
existing_keys = {row['setting_key'] for row in existing.get('rows', [])}

# Then write each setting (still individual queries, but no SELECT per key)
for key, value in normalized.items():
    if key in existing_keys:
        self.db.execute(f"UPDATE ...")
    else:
        self.db.execute(f"INSERT ...")
```

This cuts it from 30 queries to ~16 (1 SELECT + 15 writes).

---

## Issue 2: CMS — Pool Acquire/Release Overhead Per Query (Medium)

**File:** `webcms/database/kosdb_client.py:369-393`

`KosDBClient.execute()` and `KosDBClient.query()` each acquire and release a
pool connection independently. Every acquire calls `conn.ping()` (a round-trip)
even for a hot connection.

For 30 queries in `update_settings`, that's **30 ping checks** = 30 extra
round-trips on localhost.

### Fix A
Add a `batch()` or `transaction()` method to `KosDBClient` that holds a single
connection for multiple operations:

```python
@contextmanager
def transaction(self):
    conn = self.pool.acquire()
    try:
        yield conn  # conn holds a single connection, no repeated ping
    finally:
        self.pool.release(conn)
```

### Fix B
Skip `ping()` if the connection was used recently (e.g., within last 5 seconds).

---

## Issue 3: KosDB — No Batch/Upsert Support (High)

**File:** `test.KosDB/database.py`, `test.KosDB/commands.py`

KosDB has no `UPSERT` or `INSERT OR UPDATE` command. The CMS must do two
round-trips (SELECT + INSERT/UPDATE) for every setting.

### Fix
Add `INSERT OR UPDATE` / `UPSERT` command to KosDB:

```sql
INSERT OR UPDATE INTO settings (setting_key, value, type)
VALUES ('site_name', 'KosCMS', 'str')
```

This would cut the per-setting queries from 2 to 1, making the whole save
operation ~16 queries instead of ~30.

---

## Issue 4: KosDB — No Transaction Support (High)

**File:** `test.KosDB/commands.py`, `test.KosDB/database.py`

KosDB has no `BEGIN`/`COMMIT` transaction support. Each query is an isolated
operation. Even if the CMS batches operations, there's no way to atomicize them.

### Fix
Add transaction support using LevelDB's WriteBatch:

```sql
BEGIN;
UPDATE settings SET value='KosCMS' WHERE setting_key='site_name';
UPDATE settings SET value='en' WHERE setting_key='default_language';
COMMIT;
```

This allows the CMS to send all 15 updates in one network round-trip as a
single batch.

---

## Issue 5: KosDB — Single-Threaded Write Serialization (Medium)

**File:** `test.KosDB/server.py`

KosDB uses a single `Database` instance shared across all `ClientHandler`
threads. LevelDB's writes are serialized through the database instance. When
multiple clients write simultaneously, they queue up behind each other.

### Impact
Settings save holds 30 sequential writes. If any other client is writing at
the same time (e.g., auto-save, logging), the writes interleave and compound
the latency.

### Fix
Use LevelDB's native WriteBatch for bulk operations, or add a write queue
with priority to prevent starvation.

---

## Issue 6: CMS — No Connection Reuse Within Request (Low)

**File:** `webcms/admin/admin_api.py:1305-1365`

The `update_settings()` method calls `self.db.query()` and `self.db.execute()`
30 times, each going through the full pool lifecycle. A single connection
should be held for the duration of the settings save.

### Fix
Expose a way to get a raw connection from the pool for the duration of a
multi-query operation (see Issue 2 Fix A).

---

## Summary

| Issue | Side | Queries Saved | Effort |
|-------|------|---------------|--------|
| N+1 SELECT per key | CMS | -15 | Low |
| Pool ping overhead | CMS | -30 | Low |
| No UPSERT | KosDB | -15 | Medium |
| No transactions | KosDB | Enables batching | High |
| Single-threaded writes | KosDB | — | High |
| No connection reuse | CMS | — | Low |

**Quick win:** Fix Issue 1 + Issue 2 on the CMS side → cuts queries from 30 to
~16 with minimal code changes.

**Best fix:** Add UPSERT to KosDB + batch support → cuts queries to ~2 and
enables single round-trip saves.
