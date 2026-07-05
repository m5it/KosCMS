# WebCMS KosDB Integration Guide

## Overview

WebCMS now supports KosDB as a database backend. KosDB is a LevelDB-based socket server with SQL-like commands, authentication, and replication features.

## Features

- **Dual Database Support**: Use KosDB or traditional SQL databases (PostgreSQL/MySQL)
- **Connection Pooling**: Automatic connection management with overflow support
- **SQLAlchemy Integration**: Use familiar SQLAlchemy ORM with KosDB dialect
- **Replication Support**: Master-slave and master-master replication
- **Authentication Bridge**: Sync WebCMS users with KosDB or use KosDB auth directly
- **Admin Tools**: Built-in KosDB management in WebCMS admin panel

## Quick Start

### 1. Start KosDB Server

```bash
# Using Docker Compose
docker-compose -f docker-compose.kosdb.yml up -d

# Or manually
cd kosdb
python server.py --prepare_admin admin --prepare_password admin
python server.py --host 0.0.0.0 --port 9999
```

### 2. Configure WebCMS

Edit `config/config.yaml`:

```yaml
database:
  url: "kosdb://admin:admin@localhost:9999/webcms"
  
  kosdb:
    host: "localhost"
    port: 9999
    username: "admin"
    password: "admin"
    database: "webcms"
    pool_size: 10
```

### 3. Run WebCMS

```bash
python run.py
```

## Configuration Options

### Database URL Format

```
kosdb://username:password@host:port/database
```

### Replication Setup

```yaml
database:
  kosdb:
    replication:
      enabled: true
      role: "slave"  # master, slave, master_master
      server_id: 2
      master_host: "master.example.com"
      master_port: 9999
```

## Migration from SQL to KosDB

```python
from webcms.database.kosdb_migrate import KosDBMigrator
from webcms.database.kosdb_client import KosDBClient, KosDBConfig

# Connect to KosDB
kosdb = KosDBClient(KosDBConfig(
    host="localhost",
    port=9999,
    username="admin",
    password="admin"
))

# Create migrator
migrator = KosDBMigrator(
    source_url="postgresql://user:pass@localhost/old_db",
    kosdb_client=kosdb
)

# Migrate all tables
report = migrator.migrate_all("webcms")
print(f"Migrated {report['tables']} tables")
```

## Backup and Restore

```python
from webcms.database.kosdb_migrate import KosDBBackup
from webcms.database.kosdb_client import KosDBClient

kosdb = KosDBClient(...)
backup = KosDBBackup(kosdb)

# Backup
backup_file = backup.backup_database("webcms")

# Restore
backup.restore_database(backup_file, "webcms_restored")
```

## Admin Panel

Access KosDB management at:
- Dashboard: `/admin/kosdb`
- Query Executor: `/admin/kosdb/query`
- Database Browser: `/admin/kosdb/browser`
- Replication: `/admin/kosdb/replication`

## API Endpoints

| Endpoint | Method | Description |
|----------|--------|-------------|
| `/api/v1/kosdb/databases` | GET | List databases |
| `/api/v1/kosdb/databases` | POST | Create database |
| `/api/v1/kosdb/tables` | GET | List tables |
| `/api/v1/kosdb/query` | POST | Execute query |
| `/api/v1/kosdb/replication/status` | GET | Replication status |
| `/api/v1/kosdb/users` | GET | List users |

## Architecture

```
┌─────────────┐     ┌─────────────┐     ┌─────────────┐
│   WebCMS    │────▶│  KosDB      │────▶│  LevelDB    │
│   Client    │◀────│  Socket     │◀────│  Storage    │
└─────────────┘     └─────────────┘     └─────────────┘
       │
       └─────────────┬─────────────┐
                     │  Replication │
                     │  Manager   │
                     └─────────────┘
```

## CLI Commands

```bash
# Create KosDB user
webcms kosdb-user-create admin

# Migrate from SQL
webcms migrate-to-kosdb postgresql://localhost/db

# Backup KosDB
webcms kosdb-backup webcms

# Restore KosDB
webcms kosdb-restore backup.json
```

## Docker Deployment

```bash
# Start full stack with KosDB
docker-compose -f docker-compose.kosdb.yml up -d

# Scale slaves
docker-compose -f docker-compose.kosdb.yml up --scale kosdb-slave=3
```

## Troubleshooting

### Connection Issues

Check KosDB server is running:
```bash
nc -zv localhost 9999
```

### Authentication Failed

Verify credentials in config:
```yaml
database:
  kosdb:
    username: "correct_user"
    password: "correct_pass"
```

### Replication Lag

Check replication status:
```bash
curl http://localhost:8000/api/v1/kosdb/replication/status
```

## Performance Tips

1. **Connection Pooling**: Adjust `pool_size` based on load
2. **Indexing**: Use PRIMARY KEY and INDEX in table definitions
3. **Batch Inserts**: Use batch_size parameter in migrations
4. **Replication**: Use master-slave for read scaling

## License

MIT License - See LICENSE file