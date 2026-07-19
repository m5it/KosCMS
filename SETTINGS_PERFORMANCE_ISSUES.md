# Settings Save Performance Issues

## Overview
Saving settings on `/admin/settings` takes 10-30 seconds. The root cause is a
combination of CMS-side architecture issues and KosDB-side missing features.

---

## Issue 1: CMS — N+1 Query Problem (Critical)

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
