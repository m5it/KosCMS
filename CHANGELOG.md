## 2026-07-12 — v1.3.5

### Auto: Version v1.3.5

- Version auto-incremented from v1.3.4
- Files changed: AUTOVERSION.py, HISTORY.md, PLAN.md, PROJECT.md, README.md, background.log, current_task.txt, hooks/pre-commit, plans/1783844596.1984804.json, plans/1783888560.8738713.json, state.aiia, terminal_audit.log, webcms/__init__.py, webcms/admin-ui/package.json, webcms/admin/admin_api.py, webcms/admin/api.py

---

## 2026-07-12 — v0.0.2

### Auto: Version v0.0.2

- Version auto-incremented from v0.0.1
- Files changed: AUTOVERSION.py

---

# WebCMS Changelog

## [1.2.0] - 2024-02-01

### Added

#### Real-Time Collaboration
- WebSocket support for concurrent editing
- Operational transformation for conflict resolution
- Presence indicators and cursor position sharing
- Collaborative lock mechanism

#### Content Versioning
- Automatic version history tracking
- Version diff viewer and comparison
- Restore/rollback functionality
- Version pruning policies

#### Workflow System
- Custom workflow states (draft, review, approved, published)
- Approval chains with multiple reviewers
- Scheduled publishing
- Content calendar view

#### GraphQL API
- GraphQL schema with Graphene
- Queries and mutations for all models
- GraphiQL explorer endpoint
- Subscriptions for real-time updates

#### Redis Integration
- Redis cache backend
- Distributed locking
- Session storage
- Cache analytics dashboard

#### Multi-Tenant Improvements
- Tenant isolation and routing
- Tenant-specific themes and plugins
- Cross-tenant content sharing
- Resource quotas and limits

#### Enhanced Admin UI
- Modern React-based admin interface
- Drag-and-drop page builder
- Rich text editor with markdown
- Dark mode support

#### Elasticsearch Search
- Full-text search with Elasticsearch
- Faceted search UI
- Search analytics and suggestions
- Fuzzy matching and typo tolerance

#### Email & Notifications
- Email template system
- SMTP and SendGrid adapters
- Notification preferences
- Push notification support

#### Backup & Recovery
- Automated backup scheduler
- Incremental backups
- Cloud storage integration (S3/Azure)
- One-click restore

### Changed

- Updated version to 1.2.0
- Added websockets, graphene, celery, elasticsearch dependencies
- Enhanced multi-tenant architecture
- Improved caching with Redis

### Documentation

- Added GraphQL API documentation
- Updated admin user guides
- Added deployment guides
- Created architecture decision records

---
# WebCMS Changelog

## [1.1.0] - 2024-01-15

### Added

#### Full-Text Search
- SQLite FTS5 integration for content search
- Auto-indexing on content create/update/delete
- Search API endpoint: `GET /api/v1/search?q=query`
- Support for filtering by content type
- Search suggestions and ranking

#### Content Import/Export
- JSON and CSV format support
- Export filtering by status, author, date range
- Automatic format detection
- Schema validation for imports
- Duplicate slug handling

#### WebP Image Support
- Automatic WebP conversion
- Browser capability detection via Accept header
- Multiple size variations with WebP
- Configurable quality settings (0-100)
- ImageTransform class for direct manipulation

#### Plugin Marketplace
- Plugin registry with JSON storage
- Version compatibility checking
- Install/uninstall API endpoints
- Activation/deactivation support
- Dependency checking

#### Cache Enhancements
- Cache tagging for grouped invalidation
- CacheWarmer for pre-warming queries
- Per-tenant cache namespacing
- Statistics endpoint: `GET /api/v1/cache/stats`
- Token bucket algorithm

#### Admin Widgets
- WidgetBase class for custom widgets
- StatsWidget (content counts)
- RecentActivityWidget
- SystemHealthWidget
- Widget registry and JavaScript loader
- Auto-refresh support

#### Security Improvements
- Configurable Content Security Policy (CSP)
- CSP violation reporting endpoint
- Nonce generation for inline scripts
- Enhanced security headers middleware
- HSTS configuration options

#### Rate Limiting
- Endpoint-specific rate limit rules
- Token bucket algorithm
- `@rate_limit` decorator
- Rate limit headers (X-RateLimit-*)
- Stricter limits for auth endpoints

#### Query Optimization
- Eager loading with `joinedload()` and `selectinload()`
- 75-90% reduction in query counts
- Query profiler with logging
- CategoryRepository added

### Changed

- Updated `setup.py` version to 1.1.0
- Enhanced `requirements.txt` with new dependencies
- Improved API response times through query optimization
- Security headers now configurable via YAML

### Documentation

- Added `docs/SEARCH.md`
- Added `docs/IMPORT_EXPORT.md`
- Added `docs/WEBP.md`
- Added `docs/QUERY_OPTIMIZATION.md`
- Added `docs/MIGRATION_v1.1.0.md`
- Updated `README.md` with v1.1.0 features

### Tests

- `tests/test_search.py` - FTS search tests
- `tests/test_exchange.py` - Import/export tests
- `tests/test_webp.py` - WebP conversion tests
- `tests/test_marketplace.py` - Plugin registry tests
- `tests/test_cache_tags.py` - Cache tagging tests
- `tests/test_widgets.py` - Admin widget tests
- `tests/test_rate_limit.py` - Rate limiting tests

---

## [1.0.0] - 2023-12-01

### Added

- Initial release
- Plugin system with hooks
- Theme engine with Jinja2
- Content management (posts, pages)
- Media library with image processing
- Admin dashboard with REST API
- Authentication (JWT, RBAC)
- KosDB integration
- Docker support
- HTTPS/security middleware
