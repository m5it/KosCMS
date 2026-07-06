# WebCMS - Modern Python Content Management System

A production-ready CMS with plugin architecture, template system, HTTPS support, and **KosDB integration**.

## Features

- **Plugin System**: Hook-based architecture with secure sandbox
- **Theme Engine**: Jinja2 templates with asset pipeline
- **HTTPS/Security**: SSL/TLS, security headers, CSRF/XSS protection
- **Content Management**: Pages, posts, categories, tags with revisions
- **Media Library**: Image processing, multiple storage backends
- **Admin Dashboard**: React-based UI with REST API
- **Authentication**: JWT tokens, RBAC, OAuth2, 2FA support
- **Database**: SQLAlchemy ORM with migrations, soft delete, audit logging
- **🆕 KosDB Support**: LevelDB-based database with replication, failover, and SQL-like commands

## Quick Start

### Standard Setup (PostgreSQL/MySQL)

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py --debug

# Or with Docker
docker-compose up -d
```

### KosDB Setup (LevelDB Backend)

```bash
# Start KosDB + WebCMS stack
docker-compose -f docker-compose.kosdb.yml up -d

# Or manually start KosDB
cd kosdb
python server.py --prepare_admin admin --prepare_password admin
python server.py --host 0.0.0.0 --port 9999

# Then start WebCMS with KosDB config
python run.py --config config/config.kosdb.yaml
```

## Project Structure

```
webcms/
├── core/           # Framework: Application, Router, Middleware
├── models/         # Database: User, Post, Page, Media, etc.
├── auth/           # Authentication: JWT, RBAC, OAuth2, KosDB bridge
├── templates/      # Theme system with Jinja2
├── plugins/        # Plugin architecture
├── content/        # Content management
├── media/          # File uploads and storage
├── security/       # HTTPS, CSRF, XSS protection
├── admin/          # Admin dashboard, API, KosDB tools
├── database/       # SQLAlchemy + KosDB client, dialect, replication
└── config/         # Configuration files
```

## Configuration

### Standard Database (PostgreSQL/MySQL)

Edit `config/config.yaml`:

```yaml
database:
  url: "postgresql://user:pass@localhost/webcms"
```

### KosDB Configuration

Edit `config/config.yaml`:

```yaml
database:
  # KosDB connection URL
  url: "kosdb://admin:admin@localhost:9999/webcms"
  
  # KosDB-specific settings
  kosdb:
    host: "localhost"
    port: 9999
    username: "admin"
    password: "admin"
    database: "webcms"
    pool_size: 10
    
    # Replication configuration
    replication:
      enabled: true
      role: "master"  # standalone, master, slave, master_master
      server_id: 1
      master_host: null      # for slave
      master_port: null
      peer_host: null        # for master-master
      auto_failover: true
```

## API Endpoints

### Content API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/dashboard` | - | Dashboard statistics |
| `GET /api/v1/posts` | - | List posts |
| `POST /api/v1/posts` | - | Create post |
| `GET /api/v1/posts/<id>` | - | Get post |
| `PUT /api/v1/posts/<id>` | - | Update post |
| `DELETE /api/v1/posts/<id>` | - | Delete post |
| `GET /api/v1/users` | - | List users |
| `GET /api/v1/media` | - | List media files |

### KosDB Admin API

| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/kosdb/databases` | - | List databases |
| `POST /api/v1/kosdb/databases` | - | Create database |
| `GET /api/v1/kosdb/tables` | - | List tables |
| `POST /api/v1/kosdb/query` | - | Execute SQL query |
| `GET /api/v1/kosdb/replication/status` | - | Replication status |
| `GET /api/v1/kosdb/users` | - | List KosDB users |

## KosDB Features

### Connection Pooling
```python
from webcms.database import KosDBClient, KosDBConfig

config = KosDBConfig(
    host="localhost",
    port=9999,
    username="admin",
    password="admin",
    pool_size=10,
    max_overflow=20
)

client = KosDBClient(config)
result = client.query("SELECT * FROM users")
```

### SQLAlchemy Integration
```python
from sqlalchemy import create_engine

# Use KosDB with SQLAlchemy ORM
engine = create_engine("kosdb://admin:admin@localhost:9999/webcms")
```

### Replication
```python
from webcms.database import KosDBReplicationManager, ReplicationConfig, ReplicationRole

config = ReplicationConfig(
    role=ReplicationRole.SLAVE,
    master_host="master.example.com",
    master_port=9999,
    auto_failover=True
)

repl = KosDBReplicationManager(kosdb_client, config)
repl.start()
```

### Migration from SQL to KosDB
```python
from webcms.database.kosdb_migrate import KosDBMigrator

migrator = KosDBMigrator(
    source_url="postgresql://localhost/old_db",
    kosdb_client=kosdb_client
)

# Migrate all tables
report = migrator.migrate_all("webcms")
print(f"Migrated {report['tables']} tables")
```

### Backup & Restore
```python
from webcms.database.kosdb_migrate import KosDBBackup

backup = KosDBBackup(kosdb_client)

# Backup
backup_file = backup.backup_database("webcms")

# Restore
backup.restore_database(backup_file, "webcms_restored")
```

## Plugin Development

```python
from webcms.plugins import PluginBase, PluginConfig

class MyPlugin(PluginBase):
    def register(self):
        self.register_hook("post_save", self.on_post_save)
    
    def activate(self):
        return True
    
    def on_post_save(self, post, **kwargs):
        print(f"Post saved: {post.title}")
```

## Security Features

- HTTPS redirect with HSTS
- Content Security Policy headers
- CSRF token validation
- XSS input filtering
- Rate limiting
- SQL injection prevention
- KosDB authentication with privilege system

## Deployment

### Standard Docker
```bash
# Production with PostgreSQL
docker-compose -f docker-compose.yml up -d
```

### KosDB Docker Stack
```bash
# Full stack with KosDB master-slave replication
docker-compose -f docker-compose.kosdb.yml up -d

# Scale KosDB slaves
docker-compose -f docker-compose.kosdb.yml up --scale kosdb-slave=3
```

### With systemd
```bash
sudo cp systemd/webcms.service /etc/systemd/system/
sudo systemctl enable webcms
sudo systemctl start webcms
```

## Admin Panel

Access WebCMS admin at `http://localhost:8000/admin`

### KosDB Management
- **Dashboard**: `/admin/kosdb` - Database status and quick actions
- **Query Executor**: `/admin/kosdb/query` - Run SQL queries
- **Database Browser**: `/admin/kosdb/browser` - Browse tables and data
- **Replication**: `/admin/kosdb/replication` - Monitor replication status

## Documentation

- [KosDB Integration Guide](KOSDB_INTEGRATION.md) - Detailed KosDB setup and usage
- [KosDB Summary](KOSDB_INTEGRATION_SUMMARY.md) - Complete integration overview

## License

MIT License