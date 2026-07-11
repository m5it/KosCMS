
# Migration Guide: v1.0.0 to v1.1.0

This guide helps you upgrade WebCMS from v1.0.0 to v1.1.0.

## Prerequisites

- Backup your database before upgrading
- Ensure Python 3.9+ is installed
- Review breaking changes below

## Step 1: Update Dependencies

```bash
pip install --upgrade -r requirements.txt
```

New dependencies in v1.1.0:
- `packaging>=23.0` (for plugin version checking)

## Step 2: Database Migration

No schema changes required for v1.1.0. The search index is stored separately.

### Create Search Index (Optional)

To enable full-text search on existing content:

```python
from webcms.content.search_service import SearchService

service = SearchService(db)
count = service.reindex_all()
print(f"Indexed {count} items")
```

## Step 3: Configuration Updates

Update `config/config.yaml` with new security settings:

```yaml
security:
  # Add CSP configuration
  csp:
    enabled: true
    report_only: false
    report_uri: "/api/v1/security/csp-report"
    default_src: ["'self'"]
    script_src: ["'self'", "'unsafe-inline'"]
    style_src: ["'self'", "'unsafe-inline'"]
  
  # Add rate limiting
  rate_limit:
    enabled: true
    requests_per_minute: 60
    burst_size: 10
```

## Step 4: Restart Services

```bash
# Stop existing services
docker-compose down

# Start with new version
docker-compose up -d
```

## Breaking Changes

### None

v1.1.0 is fully backward compatible with v1.0.0.

## New Features Available

After migration, you can use:

1. **Full-Text Search** - Automatically works on new content
2. **WebP Images** - Enable in media settings
3. **Plugin Marketplace** - Browse and install plugins
4. **Cache Tagging** - Use with Redis for better cache control
5. **Rate Limiting** - Automatically protects endpoints

## Verification

Check migration success:

```bash
# Verify version
python -c "import webcms; print(webcms.__version__)"

# Run tests
pytest tests/ -v

# Check API endpoints
curl http://localhost:8000/api/v1/dashboard
```

## Rollback

If needed, rollback to v1.0.0:

```bash
# Restore from backup
# Revert to previous code version
pip install -r requirements.txt
```

## Support

For migration issues:
- Check [GitHub Issues](https://github.com/webcms/webcms/issues)
- Review [Documentation](../README.md)
