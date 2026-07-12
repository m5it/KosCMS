# Migration Guide: WebCMS v1.1.0 to v1.2.0

## Overview

WebCMS v1.2.0 introduces major new features including real-time collaboration, content versioning, GraphQL API, and Redis integration. This guide helps you migrate from v1.1.0.

## Prerequisites

- Python 3.9+
- Redis 6.0+ (for caching and sessions)
- Elasticsearch 8.0+ (optional, for advanced search)

## Step 1: Update Dependencies

```bash
pip install -r requirements.txt
```

New dependencies in v1.2.0:
- `websockets>=11.0.0` - Real-time collaboration
- `graphene>=3.3.0` - GraphQL API
- `celery>=5.3.0` - Background tasks
- `elasticsearch>=8.0.0` - Advanced search (optional)
- `sendgrid>=6.10.0` - Email delivery (optional)

## Step 2: Database Migrations

Run Alembic migrations:

```bash
alembic upgrade head
```

New tables in v1.2.0:
- `versions` - Content version history
- `workflows` - Workflow definitions
- `workflow_states` - Workflow state transitions
- `notifications` - User notifications
- `tenants` - Multi-tenant data (if using multi-tenant mode)

## Step 3: Redis Configuration

Add to your `config.yaml`:

```yaml
redis:
  host: localhost
  port: 6379
  db: 0
  password: null  # if required

cache:
  backend: redis  # was: simple
  ttl: 3600

sessions:
  backend: redis  # was: file
```

## Step 4: Enable New Features

### Real-Time Collaboration

```yaml
features:
  collaboration:
    enabled: true
    websocket_port: 8765
```

### Content Versioning

```yaml
features:
  versioning:
    enabled: true
    max_versions: 50  # per content item
    auto_prune: true
```

### GraphQL API

GraphQL endpoint is automatically available at `/graphql`

### Elasticsearch (Optional)

```yaml
search:
  backend: elasticsearch  # was: sqlite
  hosts:
    - localhost:9200
  index_name: webcms
```

## Step 5: Environment Variables

New optional variables:

```bash
# Redis
REDIS_URL=redis://localhost:6379/0

# Celery
CELERY_BROKER_URL=redis://localhost:6379/0
CELERY_RESULT_BACKEND=redis://localhost:6379/0

# Elasticsearch
ELASTICSEARCH_URL=http://localhost:9200

# Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SENDGRID_API_KEY=your_key_here
```

## Step 6: Start Services

### Start Redis
```bash
redis-server
```

### Start Celery Worker (for background tasks)
```bash
celery -A webcms.tasks worker --loglevel=info
```

### Start WebSocket Server (for collaboration)
```bash
python -m webcms.websocket_server
```

### Start Main Application
```bash
python run.py
```

## Breaking Changes

### API Changes

1. **Rate Limiting**: Default limits now stricter
   - Before: 100 requests/minute
   - After: 60 requests/minute

2. **Cache Keys**: Cache key format changed
   - Old keys will be invalidated automatically

3. **Plugin API**: Minor changes to plugin interface
   - `PluginBase` now requires `version` attribute

### Configuration Changes

- `security.csp` structure updated
- Added `features` section
- Database URL format unchanged

## Rollback Plan

If issues occur:

1. Stop all services
2. Restore database from backup
3. Revert to v1.1.0 code
4. Clear Redis cache: `redis-cli FLUSHDB`

## Verification

After migration, verify:

```bash
# Check version
python -c "import webcms; print(webcms.__version__)"
# Should print: 1.2.0

# Test GraphQL endpoint
curl http://localhost:8000/graphql \
  -H "Content-Type: application/json" \
  -d '{"query": "{ __schema { types { name } } }"}'

# Test WebSocket (should connect)
wscat -c ws://localhost:8765
```

## Support

For migration issues:
- Check logs: `logs/migration.log`
- Enable debug mode: `app.debug = True`
- Contact support: support@webcms.io

## See Also

- [CHANGELOG.md](../CHANGELOG.md) - Full change list
- [docs/GRAPHQL.md](GRAPHQL.md) - GraphQL API guide
- [docs/COLLABORATION.md](COLLABORATION.md) - Real-time collaboration setup
