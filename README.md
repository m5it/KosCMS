
# WebCMS - Modern Python Content Management System

A production-ready CMS with plugin architecture, template system, HTTPS support, KosDB integration, and **v1.1.0 features**.

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

### 🆕 v1.1.0 Features

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
docker-compose up -d
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
├── cache/          # Multi-level caching with tagging
├── search/         # Full-text search with FTS5
└── config/         # Configuration files
```

## New in v1.1.0

### Full-Text Search
```python
from webcms.content.search_service import SearchService

service = SearchService(db)
results = service.search("python tutorial", limit=20)

# Auto-indexing on content changes
manager.create_post(title="New Post", ...)  # Automatically indexed
```

### Content Import/Export
```python
from webcms.content.exchange import ContentExporter, ExportOptions

# Export to JSON
exporter = ContentExporter(db)
options = ExportOptions(format="json", content_types=["post", "page"])
data = exporter.export(options)

# Import from CSV
importer = ContentImporter(db)
result = importer.import_content(csv_data)
```

### WebP Support
```python
from webcms.media.manager import MediaManager

manager = MediaManager(db)
media = manager.upload(...)

# Convert to WebP
webp_version = manager.convert_to_webp(media)

# Auto-serve WebP to supported browsers
url = manager.get_webp_url(media, accept_header)
```

### Plugin Marketplace
```python
from webcms.plugins.marketplace import get_registry

registry = get_registry()
plugins = registry.list_available()

# Install plugin
registry.install("my-plugin", source="/path/to/plugin.zip")
```

### Cache Tagging
```python
from webcms.cache.manager import get_tenant_cache

cache = get_tenant_cache("tenant-1")
cache.set("key", value, tags=["posts", "homepage"])

# Invalidate by tag
cache.tag_invalidate("posts")
```

### Admin Widgets
```python
from webcms.admin.widgets import StatsWidget, get_widget_registry

# Get dashboard widgets
registry = get_widget_registry()
widgets = registry.render_all(db, configs)
```

### Rate Limiting
```python
from webcms.auth.rate_limiter import rate_limit

@rate_limit("auth")
def login(request):
    # Stricter limits applied
    pass
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
| `GET /api/v1/search` | - | Full-text search |
| `POST /api/v1/content/export` | - | Export content |
| `POST /api/v1/content/import` | - | Import content |

### Plugin API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/plugins/marketplace` | - | List available plugins |
| `POST /api/v1/plugins/install` | - | Install/activate plugin |
| `DELETE /api/v1/plugins/install` | - | Uninstall/deactivate |

### Admin API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `GET /api/v1/admin/widgets` | - | Dashboard widgets |
| `GET /api/v1/cache/stats` | - | Cache statistics |
| `POST /api/v1/cache/stats` | - | Warm/clear cache |

### Security API
| Endpoint | Method | Description |
|----------|--------|-------------|
| `POST /api/v1/security/csp-report` | - | CSP violation reporting |

## Documentation

- [Search Documentation](docs/SEARCH.md) - Full-text search setup
- [Import/Export Guide](docs/IMPORT_EXPORT.md) - Content exchange
- [WebP Images](docs/WEBP.md) - Image optimization
- [Query Optimization](docs/QUERY_OPTIMIZATION.md) - Database optimization

## Migration from v1.0.0

See [Migration Guide](docs/MIGRATION_v1.1.0.md) for upgrade instructions.

## License

MIT License
