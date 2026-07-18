# WebCMS - Modern Python Content Management System

A production-ready CMS with plugin architecture, template system, HTTPS support, KosDB integration, and a full React-based admin control panel. **Version 1.3.29**

## Features

### Core Features
- **Plugin System**: Hook-based architecture with secure sandbox and marketplace registry
- **Theme Engine**: Jinja2 templates with asset pipeline and theme activation
- **HTTPS/Security**: SSL/TLS, security headers, CSRF/XSS protection, configurable CSP
- **Content Management**: Pages, posts, categories, tags with revisions and import/export
- **Media Library**: Image processing, WebP conversion, multiple storage backends
- **Authentication**: JWT tokens, RBAC, OAuth2, 2FA support, rate limiting
- **Database**: SQLAlchemy ORM with KosDB dialect, migrations, soft delete, audit logging
- **KosDB Integration**: Native KosDB client, custom SQLAlchemy dialect, replication, and migrations

### 🆕 v1.3.0 — React Admin Control Panel

The `/admin` route serves a full React/Vite admin control panel with sidebar navigation and management screens for every major subsystem. The backend exposes `/api/v1/admin/*` REST endpoints consumed by the UI.

| Screen | Capabilities |
|--------|--------------|
| **Dashboard** | Live widgets from `/api/v1/admin/dashboard` |
| **Pages & Posts** | List, create, edit, delete content |
| **Media** | Gallery, upload, bulk select, delete |
| **Templates** | Create, edit, delete template files |
| **Themes** | Activate, preview installed themes |
| **Plugins** | Activate, deactivate, install, uninstall |
| **Users** | List, create, edit, delete, activate/deactivate |
| **Roles** | Permission grid editor |
| **Settings** | Site, cache, search, notifications, security |
| **Cache** | Analytics, warm, invalidate by pattern, flush |
| **Backups** | Create, restore, verify, delete backups |
| **Workflows** | Instances, state transitions, reviewer assignment, definitions |
| **Tenants** | CRUD and per-tenant analytics |
| **Search** | Analytics and query suggestions |
| **Notifications** | Preferences, manual send, digest trigger, queue stats |

### v1.2.0 Features

| Feature | Description |
|---------|-------------|
| **Workflow Engine** | Multi-state content approval with reviewer chains |
| **GraphQL API** | Graphene schema with queries, mutations, subscriptions |
| **Redis Caching** | Connection pooling, distributed locks, query caching |
| **Multi-Tenancy** | Schema-based tenant isolation with themes and quotas |
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

# Build the admin UI
cd webcms/admin-ui
npm install
npm run build
cd ../..

# Run development server
python run.py --debug

# Open the admin panel
open http://localhost:8000/admin

# Or with Docker
docker-compose -f docs/deployment/docker-compose.yml up -d
```

## Admin User Setup

The React admin panel at `/admin` needs at least one active user to manage content, users, and settings. There are three ways to create the first admin user.

### Option 1: Use the built-in CLI command (recommended)

```bash
source .venv/bin/activate  # if using a virtual environment
python -m webcms.cli.commands create-admin \
  --username admin \
  --email admin@example.com \
  --password "ChangeMeNow!"
```

This creates the user, assigns the `admin` role, and activates the account.

### Option 2: Create a user from a Python shell

```bash
python - <<'PY'
from webcms.database import init_db
from webcms.models.user import User, Role
from webcms.auth.password import PasswordHasher

db = init_db("sqlite:///webcms.db")
hasher = PasswordHasher()

# Create the admin role if it does not exist
admin_role = db.query(Role).filter_by(name="admin").first()
if not admin_role:
    admin_role = Role(name="admin", description="Full system access")
    admin_role.permissions = ",".join([
        "content:read", "content:write", "content:delete",
        "media:read", "media:write", "media:delete",
        "plugins:manage", "users:manage", "roles:manage",
        "settings:manage", "cache:manage", "backups:manage"
    ])
    db.add(admin_role)

# Create the admin user
user = User(
    username="admin",
    email="admin@example.com",
    password_hash=hasher.hash("ChangeMeNow!"),
    display_name="Administrator",
    is_active=True,
    is_superuser=True
)
user.roles.append(admin_role)
db.add(user)
db.commit()
print("Admin user created:", user.id)
PY
```

### Option 3: Seed the database automatically

Create a file named `seed_admin.py` in the project root and run it once:

```python
from webcms.database import init_db
from webcms.models.user import User, Role
from webcms.auth.password import PasswordHasher

def seed():
    db = init_db("sqlite:///webcms.db")
    hasher = PasswordHasher()

    if not db.query(Role).filter_by(name="admin").first():
        role = Role(
            name="admin",
            description="Full system access",
            permissions="content:read,content:write,content:delete,media:read,media:write,media:delete,plugins:manage,users:manage,roles:manage,settings:manage,cache:manage,backups:manage"
        )
        db.add(role)

    if not db.query(User).filter_by(username="admin").first():
        user = User(
            username="admin",
            email="admin@example.com",
            password_hash=hasher.hash("ChangeMeNow!"),
            display_name="Administrator",
            is_active=True,
            is_superuser=True
        )
        db.add(user)
        db.commit()
        print("Seeded admin user")

if __name__ == "__main__":
    seed()
```

Run it with:

```bash
python seed_admin.py
```

> **Security note:** Change the default password immediately after first login via **Settings** or the **Users** screen. Never commit a file containing a real password to version control.

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
├── admin/          # Admin dashboard, API, widgets, /admin route
├── cache/          # Redis caching, locks, sessions, analytics
├── search/         # Elasticsearch search with facets
├── database/       # SQLAlchemy + KosDB client, dialect, migrations
├── workflow/       # Content approval workflows
├── tenants/        # Multi-tenant isolation
├── notifications/  # Email, in-app, push notifications
├── backup/         # Backup, encryption, restore, DR
├── graphql/        # GraphQL API and GraphiQL
├── admin-ui/       # Vite + React admin frontend
└── tests/          # Integration, unit, load, benchmark tests
```

## Admin UI Routing

- `App.jsx` mounts `AdminShell` under `/admin/*`
- `AdminShell.jsx` renders the sidebar and top bar, then switches relative child routes (`dashboard`, `content`, `media`, etc.)
- The backend serves `webcms/admin-ui/dist/index.html` for `/admin` and all `/admin/*` paths, enabling browser refresh and deep linking

## Admin API Endpoints

All management screens connect to `/api/v1/admin`:

- `/dashboard`
- `/content`
- `/media`
- `/templates`
- `/themes`
- `/plugins`
- `/users`
- `/roles`
- `/settings`
- `/cache/*`
- `/backups/*`
- `/workflows/*`
- `/tenants/*`
- `/search/*`
- `/notifications/*`

## License

MIT License - see LICENSE file for details.

## Support

For issues and documentation, visit the project repository or open an issue.
