# KosDB Installation Guide
# =======================

## Quick Start (No PostgreSQL!)

KosDB uses LevelDB via a TCP socket server - no database installation required.

### 1. Install Dependencies

```bash
# Use the KosDB-optimized requirements (no PostgreSQL)
pip install -r requirements-kosdb.txt

# Or use the install script
chmod +x install-kosdb.sh
./install-kosdb.sh
```

### 2. Start KosDB Server

```bash
# Start the LevelDB socket server (default: port 9999)
python -m webcms.database.kosdb_server

# Or with custom host/port
python -m webcms.database.kosdb_server --host 0.0.0.0 --port 9999
```

### 3. Run KosCMS

```bash
# In another terminal
python -m webcms
```

## What's Different from PostgreSQL?

| Feature | KosDB | PostgreSQL |
|---------|-------|------------|
| Installation | `pip install` only | Install PostgreSQL server + client |
| Dependencies | None (pure Python + LevelDB) | `libpq-dev`, `psycopg2-binary` |
| Setup time | Instant | 10-30 min setup |
| Disk usage | ~10MB | ~100MB+ |
| Performance | Excellent for CMS workloads | Excellent for complex queries |
| Best for | Single-node deployments | Multi-node, complex analytics |

## File Structure

```
requirements-kosdb.txt      # KosDB-only dependencies (NO PostgreSQL)
requirements.txt            # Full dependencies (with PostgreSQL as optional)
install-kosdb.sh            # Automated installation script
README-KosDB.md             # This file
```

## Troubleshooting

### "Connection refused" error
```bash
# Make sure KosDB server is running
python -m webcms.database.kosdb_server
```

### Port already in use
```bash
# Use a different port
python -m webcms.database.kosdb_server --port 9998
```

### Permission denied
```bash
# Make install script executable
chmod +x install-kosdb.sh
```

## Configuration

Create `.env` file:

```bash
# Database type
DATABASE_TYPE=kosdb

# KosDB connection (TCP socket)
KOSDB_HOST=localhost
KOSDB_PORT=9999

# Optional: authentication
KOSDB_USERNAME=admin
KOSDB_PASSWORD=secret
```

## Why No PostgreSQL?

KosDB (LevelDB) is perfect for CMS workloads:
- ✅ Zero external dependencies
- ✅ Instant setup
- ✅ Embedded in application
- ✅ Fast key-value operations
- ✅ No DBA maintenance needed

Use PostgreSQL only if you need:
- Complex SQL queries with JOINs
- Multi-node replication
- External analytics tools
