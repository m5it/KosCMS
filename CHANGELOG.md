
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
