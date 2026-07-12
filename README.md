# WebCMS - Modern Python Content Management System

A production-ready CMS with plugin architecture, template system, HTTPS support, KosDB integration, and **v1.2.0 features**.

## Features

### Core Features
- **Plugin System**: Hook-based architecture with secure sandbox
- **Theme Engine**: Jinja2 templates with asset pipeline
- **HTTPS/Security**: SSL/TLS, security headers, CSRF/XSS protection
- **Content Management**: Pages, posts, categories, tags with revisions
- **Media Library**: Image processing, multiple storage backends
- **Admin Dashboard**: React-based UI with REST API
- **Authentication**: JWT tokens, RBAC, OAuth2, 2FA support
- **Database**: SQLAlchemy ORM with migrations, soft delete, audit logging

### 🆕 v1.2.0 Features

| Feature | Description |
|---------|-------------|
| **Workflow Engine** | Multi-state content approval with reviewer chains |
| **GraphQL API** | Graphene schema with queries, mutations, subscriptions |
| **Redis Caching** | Connection pooling, distributed locks, query caching |
| **Multi-Tenancy** | Schema-based tenant isolation with themes and quotas |
| **Modern Admin UI** | Vite + React with drag-drop builder and dark mode |
| **Elasticsearch** | Faceted search with highlighting and fuzzy matching |
| **Notifications** | Email, in-app, push with templates and digest queues |
| **Backup & DR** | Scheduled backups, S3/Azure storage, encryption, restore |
| **Testing & Docs** | Integration tests, OpenAPI, ADRs, deployment guides |

### v1.1.0 Features

| Feature | Description |
|---------|-------------|
| **Full-Text Search** | SQLite FTS5 integration with auto-indexing |
| **Content Import/Export** | JSON and CSV format support |
| **WebP Images** | Automatic WebP conversion with browser detection |
| **Plugin Marketplace** | Plugin registry with version compatibility |
| **Cache Tagging** | Redis cache with tag-based invalidation |
| **Admin Widgets** | Dashboard widget system |
| **Rate Limiting** | Endpoint-specific rate limits with token bucket |
| **Query Optimization** | Eager loading with 75-90% query reduction |
| **Enhanced Security** | Configurable CSP with violation reporting |

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Run development server
python run.py --debug

# Or with Docker
docker-compose -f docs/deployment/docker-compose.yml up -d
```

## Project Structure

```
webcms/
├── core/           # Framework: Application, Router, Middleware
├── models/         # Database: User, Post, Page, Media, etc.
├── auth/           # Authentication: JWT, RBAC, OAuth2, rate limiting
├── templates/      # Theme system with Jinja2
├── plugins/        # Plugin architecture + marketplace
├── content/        # Content management + search + exchange
├── media/          # File uploads, WebP conversion, storage
├── security/       # HTTPS, CSP, CSRF, XSS protection
├── admin/          # Admin dashboard, API, widgets
├── cache/          # Redis caching, locks, sessions, analytics
├── search/         # Elasticsearch search with facets
├── workflow/       # Content approval workflows
├── tenants/        # Multi-tenant isolation
├── notifications/  # Email, in-app, push notifications
├── backup/         # Backup, encryption, restore, DR
├── graphql/        # GraphQL API and GraphiQL
├── admin-ui/       # Vite + React admin frontend
└── tests/          # Integration, unit, load, benchmark tests
```

## New in v1.2.0

### Workflow Engine

```python
import asyncio
from webcms.workflow import WorkflowManager

async def main():
    manager = WorkflowManager()
    workflow = await manager.get_default_workflow()

    instance = await manager.start_workflow(
        content_id="post-1",
        content_type="post",
        workflow_id=workflow.workflow_id
    )
    await manager.assign_reviewers(instance.instance_id, ["reviewer1"])
    await manager.transition(
        instance.instance_id, "review",
        user_id="author1", username="Author"
    )

asyncio.run(main())
```

### GraphQL API

```python
from webcms.graphql import schema

result = schema.execute('{ posts { id title slug status } }')
print(result.data)
```

Visit `/graphiql` for the interactive explorer.

### Redis Caching

```python
from webcms.cache import get_redis_client, CacheManager

client = get_redis_client()
cache = CacheManager(client)

async def get_popular_posts():
    return await cache.cache_query(
        "popular_posts",
        {"limit": 10},
        fetch_func=lambda: {"posts": []}
    )
```

### Multi-Tenancy

```python
from webcms.tenants import TenantManager

async def main():
    manager = TenantManager()
    tenant = await manager.create_tenant(
        name="Acme Blog",
        slug="acme",
        domain="acme.example.com"
    )
    print(tenant.to_dict())

asyncio.run(main())
```

### Elasticsearch Search

```bash
curl "/api/v1/search?q=webcms&status=published&tags=python"
```

Responses include highlighted results, facets, and pagination.

### Notifications

```python
from webcms.notifications import NotificationManager, SMTPAdapter

manager = NotificationManager(email_adapter=SMTPAdapter())
asyncio.run(manager.notify(
    user_id="user1",
    event_type="welcome",
    subject="Welcome to WebCMS",
    context={"username": "Alice", "email": "alice@example.com"}
))
```

### Backup & Disaster Recovery

```bash
# Create backup
curl -X POST /api/v1/backups

# Restore from backup
curl -X POST /api/v1/backups/<backup_id>/restore

# Monitor backup health
curl /api/v1/backups/monitor
```

### Modern Admin UI

```bash
cd webcms/admin-ui
npm install
npm run dev
```

Features drag-and-drop page builder, markdown editor, media gallery, dark mode, and keyboard shortcuts.

## API Endpoints

### Content API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/posts` | GET | List posts |
| `POST /api/v1/posts` | POST | Create post |
| `GET /api/v1/posts/<id>` | GET | Get post |
| `PUT /api/v1/posts/<id>` | PUT | Update post |
| `DELETE /api/v1/posts/<id>` | DELETE | Delete post |

### Workflow API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/workflows` | GET | List workflow definitions |
| `POST /api/v1/<type>/<id>/workflow` | POST | Start workflow |
| `POST /api/v1/workflow-instances/<id>/transition` | POST | Transition state |
| `POST /api/v1/workflow-instances/<id>/schedule` | POST | Schedule publish |

### Search API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/search` | GET | Full-text search |
| `GET /api/v1/search/suggest` | GET | Search suggestions |
| `GET /api/v1/search/analytics` | GET | Search analytics |

### Tenant API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/tenants` | GET | List tenants |
| `POST /api/v1/tenants` | POST | Create tenant |
| `GET /api/v1/tenants/<id>/analytics` | GET | Tenant analytics |
| `POST /api/v1/tenants/share` | POST | Share content |

### Notification API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/notifications/<user_id>` | GET | User notifications |
| `PUT /api/v1/notifications/<user_id>/preferences` | PUT | Update preferences |
| `POST /api/v1/notifications/digest` | POST | Send digest emails |

### Backup API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/backups` | GET | List backups |
| `POST /api/v1/backups` | POST | Create backup |
| `POST /api/v1/backups/<id>/restore` | POST | Restore backup |
| `GET /api/v1/backups/monitor` | GET | Backup health |

### GraphQL
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /graphql` | POST | GraphQL endpoint |
| `GET /graphiql` | GET | GraphiQL explorer |

## Documentation

- [OpenAPI Spec](docs/api/openapi.yaml) - API documentation
- [Workflow Guide](docs/guides/workflow-guide.md) - Content approval workflows
- [Search Guide](docs/guides/search-guide.md) - Elasticsearch search
- [Deployment Guide](docs/deployment/DEPLOYMENT.md) - Docker and production setup
- [Disaster Recovery](webcms/backup/DISASTER_RECOVERY.md) - Backup and restore
- [Architecture Decisions](docs/adr/) - ADRs

## Testing

```bash
# Run integration and unit tests
pytest tests/integration tests/unit -v

# With coverage
pytest tests/integration tests/unit --cov=webcms --cov-report=term

# Load testing
locust -f tests/load/locustfile.py
k6 run tests/load/k6-script.js

# Benchmarks
python tests/benchmark/bench_queries.py
```

## Migration

See [Migration Guide](docs/MIGRATION_v1.1.0.md) for upgrade instructions from v1.0.0.

## License

MIT License
