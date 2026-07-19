# KosCMS Performance Optimizations

Client-side bottlenecks and optimization opportunities, ranked by impact.

---

## C1: Still 15 Individual Writes Per Settings Save (HIGH)

**File:** `webcms/admin/admin_api.py:1347-1371`

Even with the batch SELECT optimization, the code still does 15 individual
`conn.execute()` calls -- one per setting. Each is a separate send/recv on
the socket.

**Fix (requires KosDB support):** Use BEGIN/COMMIT transactions:

```python
with self.db.transaction() as conn:
    conn.execute("BEGIN")
    for key, value in normalized.items():
        if key in existing_keys:
            conn.execute(f"UPDATE settings SET ...")
        else:
            conn.execute(f"INSERT INTO settings ...")
    conn.execute("COMMIT")
```

Or even better, implement bulk insert/update commands (see KosDB PERFORMANCE.md P10/P11).

**Impact:** 15 socket round-trips -> 1 (if KosDB supports pipelining) or
3 (BEGIN + batch + COMMIT).

---

## C2: No SQL Pipelining (MEDIUM)

**File:** `webcms/database/kosdb_client.py:157-185`

`KosDBConnection.execute()` and `query()` send one command and wait for
the full response before returning. There's no way to send multiple commands
before reading responses (pipelining).

```python
def execute(self, command: str) -> str:
    self._send(command)
    return self._receive()  # Blocks until full response
```

**Fix:** Add a `pipeline()` method that sends multiple commands and collects
all responses:

```python
def pipeline(self, commands: List[str]) -> List[str]:
    """Send multiple commands without waiting for individual responses."""
    for cmd in commands:
        self._send(cmd)
    
    results = []
    for _ in commands:
        results.append(self._receive())
    return results
```

Requires KosDB server to support this (it should, since it's line-based).

**Impact:** 15 sends + 15 recvs -> 15 sends + 15 recvs but pipelined (no
wait between send and recv). Eliminates network round-trip idle time.

---

## C3: Connection Pool Ping Check Adds Latency (MEDIUM)

**File:** `webcms/database/kosdb_client.py:331-337`

Even with `max_ping_interval`, every pool acquire checks if ping should run.
The `_ensure_alive()` in the transaction wrapper also pings on entry.

**Fix:** Trust the TCP keepalive instead of application-level ping:

```python
class KosDBConnection:
    def ping(self) -> bool:
        """Check if connection is alive via TCP keepalive."""
        try:
            self.socket.settimeout(2.0)
            import select
            readable, _, _ = select.select([self.socket], [], [], 0)
            if readable:
                data = self.socket.recv(1, socket.MSG_PEEK)
                if not data:
                    return False  # Connection closed
            return True
        except:
            return False
```

**Impact:** Eliminates 1 round-trip per connection acquire.

---

## C4: Response Parsing Fragile (LOW)

**File:** `webcms/database/kosdb_client.py:160-185`

The `query()` method parses ASCII table format back into structured data.
This is fragile (edge cases with column values containing `|` or `+`) and
wasteful (server builds table, client parses it).

**Fix:** Have the server return JSON (see KosDB PERFORMANCE.md P8), then
client just does:

```python
def query(self, command: str) -> Dict[str, Any]:
    raw = self._send_and_receive(command)
    try:
        return json.loads(raw)
    except json.JSONDecodeError:
        return {"error": raw}
```

**Impact:** Eliminates fragile parsing, smaller payloads, faster processing.

---

## C5: SQL Injection via String Interpolation (SECURITY)

**File:** `webcms/admin/admin_api.py:1356-1363`

Settings values are escaped with `_sql_escape()` but this is a custom
function -- no parameterized query support exists in KosDB.

**Fix (requires KosDB support):** Add parameterized queries:

```sql
PREPARE update_setting AS
UPDATE settings SET value=$1, type=$2 WHERE setting_key=$3;
EXECUTE update_setting('KosCMS', 'str', 'site_name');
```

Or at minimum, validate that `_sql_escape()` handles all edge cases
(single quotes, backslashes, null bytes, etc.).

---

## Summary

### Medium Effort (1-4 hours each)

| # | Issue | Impact | Effort | Depends On |
|---|-------|--------|--------|------------|
| C1 | Use BEGIN/COMMIT in settings save | 15 writes -> 3 round-trips | 1 hr | KosDB transaction support |
| C2 | SQL pipelining | Eliminates idle round-trip time | 3 hrs | KosDB pipeline support |
| C3 | Replace ping with TCP check | -1 round-trip/acquire | 15 min | -- |

### Low Effort

| # | Issue | Impact | Effort | Depends On |
|---|-------|--------|--------|------------|
| C4 | JSON response format | Faster parse, smaller payload | -- | KosDB P8 |
| C5 | Parameterized queries | Security + performance | 6 hrs | KosDB prepared stmts |

### What To Focus On First

1. **C1** (BEGIN/COMMIT in settings save) -- requires KosDB to support
   transactions, then the CMS change is trivial.
2. **C3** (TCP-based ping) -- quick standalone fix, no DB changes needed.
3. **C2** (pipelining) -- bigger impact but needs KosDB to handle it.

All C1-C2 require KosDB server changes first. See `KOSDB_PERFORMANCE.md`
for the server-side work.
