# KosCMS Database Issues — Settings Not Persisting

These bugs were found while debugging why admin/settings changes report success but revert on page refresh.

## Bug 1: `list_tables()` includes "OK:" as a table name

**File:** `webcms/database/kosdb_client.py:461-466`

`SHOW TABLES` on the server returns `"OK:\nsettings"`. The client splits by newline:

```python
def list_tables(self) -> List[str]:
    result = self.execute("SHOW TABLES")
    if result.startswith("ERROR"):
        return []
    return [line.strip() for line in result.split('\n') if line.strip()]
    # Returns: ["OK:", "settings"]  <-- "OK:" is a phantom table
```

This works by accident for `"settings" in tables` in `_ensure_settings_table_kosdb()`, but is fragile.

**Fix:**
```python
def list_tables(self) -> List[str]:
    result = self.execute("SHOW TABLES")
    if result.startswith("ERROR"):
        return []
    return [line.strip() for line in result.split('\n')
            if line.strip() and not line.strip().startswith("OK")]
```

---

## Bug 2: INSERT/UPDATE results never checked for errors

**File:** `webcms/admin/admin_api.py:1263-1295`

In `update_settings()`, the result of each `self.db.execute(cmd)` is printed but never inspected:

```python
result = self.db.execute(cmd)
print(f"[DEBUG] Execute result: {result}")
# If result is "ERROR: No database selected" — still returns {"updated": true}
```

**Fix:** Collect errors and return them:
```python
errors = []
for key, value in normalized.items():
    # ... existing check/insert/update logic ...
    result = self.db.execute(cmd)
    if result and ("ERROR" in result or "No database" in result):
        errors.append({"key": key, "error": result})

if errors:
    return Response.json({"updated": False, "errors": errors, "settings": data}, 400)
```

---

## Bug 3: Pool re-sends `USE` on every acquire (triggers KosDB race condition)

**File:** `webcms/database/kosdb_client.py:331-332`

Every time a connection is taken from the pool, it re-sends `USE webcms`:

```python
@contextmanager
def acquire(self):
    # ...
    if self.config.database:
        conn.execute(f"USE {self.config.database}")  # <-- triggers use_database() on server every time
    yield conn
```

This is the direct trigger of the KosDB thread-safety bug (see KOSDB_ISSUES.md Bug #1). Each `USE` call closes and reopens the shared `_db` handle on the server.

**Fix:** Only send `USE` on new connections, not on every acquire:
```python
class KosDBConnection:
    def __init__(self, config):
        # ...
        self._db_selected = False

    def connect(self) -> bool:
        # ... existing connect logic ...
        self._db_selected = False  # reset on reconnect
        return True

    def _select_database(self, database: str) -> bool:
        result = self.execute(f"USE {database}")
        self._db_selected = result.startswith("OK")
        return self._db_selected

# In pool acquire():
@contextmanager
def acquire(self):
    # ...
    if self.config.database and not conn._db_selected:
        conn.execute(f"USE {self.config.database}")
    yield conn
```

---

## Bug 4: Port mismatch in config

**File:** `config.json:6`

Config says port `5555`, but KosDB server runs on `5556`.

```json
"port": 5555   <-- should be 5556
```

**Fix:** Change to `"port": 5556`.

---

## Bug 5: Stale version across multiple files

`AUTOVERSION.py` is at `1.3.29` but several files have old versions:

| File | Current | Should be |
|------|---------|-----------|
| `README.md:3` | 1.3.6 | 1.3.29 (already fixed) |
| `setup.py:12` | 1.0.0 | 1.3.29 |
| `pyproject.toml:7` | 1.2.0 | 1.3.29 |

**Fix:** Update all to match `AUTOVERSION.py` (currently `1.3.29`).

---

## Bug 6: `setup.py` and `requirements.txt` reference Flask — wrong framework

**Files:** `setup.py:21-29`, `requirements.txt:3-8`

Both list Flask, Flask-SQLAlchemy, Flask-JWT-Extended, Flask-CORS as dependencies. But the project uses its own framework (`webcms.core.application`, `webcms.core.request`, `webcms.core.response`) — **not Flask**. These dependencies are dead weight and may cause confusion.

**Fix:** Update `requirements.txt` to list actual dependencies (plyvel, etc.) and remove Flask references. Update `setup.py` accordingly.

---

## Bug 7: `Dockerfile` and `docker-compose.yml` reference Flask

**Files:** `Dockerfile:9-10,45`, `docker-compose.yml:13`

- `Dockerfile` sets `FLASK_APP=run.py` and runs gunicorn — but the app uses its own server via `run.py` calling `app.run()`
- `docker-compose.yml` sets `DATABASE_URL=sqlite:///` — but the app uses KosDB

**Fix:** Update Dockerfile CMD to `CMD ["python", "run.py", "--host", "0.0.0.0", "--port", "8080"]` and update docker-compose environment to use KosDB config.

---

## Summary

| # | File | Issue | Severity | Also needs |
|---|------|-------|----------|------------|
| 1 | `kosdb_client.py:461` | `list_tables()` returns "OK:" as table | Low | - |
| 2 | `admin_api.py:1294` | INSERT/UPDATE errors silently swallowed | High | - |
| 3 | `kosdb_client.py:331` | Pool re-sends USE on every acquire | **Critical** | KOSDB_ISSUES.md Bug #1 |
| 4 | `config.json:6` | Wrong port (5555 vs 5556) | High | - |
| 5 | `README.md`, `setup.py`, `pyproject.toml` | Stale versions | Low | - |
| 6 | `setup.py`, `requirements.txt` | Flask deps — wrong framework | Medium | - |
| 7 | `Dockerfile`, `docker-compose.yml` | Flask refs — wrong framework | Medium | - |

**Bug #3 + KosDB Bug #1 together are the root cause** of the settings not persisting. Fix both sides.
