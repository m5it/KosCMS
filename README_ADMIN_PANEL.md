# WebCMS Admin Panel

A comprehensive, production-ready admin panel for WebCMS with full CRUD operations, user management, content management, and system administration.

## Features

### ✅ Core Administration
- **Dashboard** - Real-time statistics and system health monitoring
- **User Management** - Create, edit, delete users with role assignment
- **Role Management** - Define permissions and access levels
- **Settings** - Site configuration with persistent storage

### ✅ Content Management
- **Pages** - Static page creation and management
- **Posts** - Blog/article management with publishing workflow
- **Media** - File upload and asset management
- **Templates** - Theme template editing
- **Themes** - Theme activation and switching

### ✅ System Administration
- **Plugins** - Plugin activation/deactivation
- **Cache** - Statistics and invalidation
- **Backups** - Create, restore, and verify backups
- **Workflows** - Content approval workflows
- **Tenants** - Multi-tenancy management
- **Search** - Analytics and suggestions
- **Notifications** - Email and in-app notifications

## Quick Start

### Prerequisites
- Python 3.8+
- KosDB (or SQLAlchemy as fallback)

### Installation

```bash
# Clone the repository
git clone <repository-url>
cd KosCMS

# Install dependencies (if using requirements.txt)
pip install -r requirements.txt

# Or install manually
pip install flask flask-sqlalchemy flask-jwt-extended
```

### Running the Application

```bash
# Development mode with debug
python3 run.py -d

# Production mode
python3 run.py

# Access the admin panel
open http://localhost:5000/admin
```

### Running Tests

```bash
# Run all tests
python3 run_tests.py

# Run unit tests only
python3 tests/test_admin_unittest.py

# Run end-to-end tests only
python3 test_admin_e2e.py
```

## API Documentation

All admin functionality is exposed via RESTful JSON API.

### Base URL
```
/api/v1/admin
```

### Authentication
Include JWT token in Authorization header:
```
Authorization: Bearer <your-token>
```

### Example Endpoints

#### Get Dashboard Stats
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/v1/admin/dashboard
```

#### List Users
```bash
curl -H "Authorization: Bearer <token>" \
  http://localhost:5000/api/v1/admin/users
```

#### Create User
```bash
curl -X POST \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"username":"john","email":"john@example.com","password":"secret"}' \
  http://localhost:5000/api/v1/admin/users
```

See [API_DOCUMENTATION.md](API_DOCUMENTATION.md) for complete API reference.

## Architecture

### Components

```
webcms/
├── admin/
│   ├── admin_api.py          # Main API class (62 endpoints)
│   ├── logging_middleware.py # Audit logging
│   └── __init__.py
├── cache/
│   └── manager.py            # Cache management
├── core/
│   ├── request.py            # Request handling
│   └── response.py           # Response handling
└── app_factory.py          # App initialization
```

### Key Classes

#### AdminAPI
Main API class providing all administrative operations:
- Dashboard widgets
- CRUD operations for all entities
- System management functions

#### AdminLogger
Comprehensive logging system:
- Operation tracking
- Error logging
- Audit trail

#### AuditTrail
Database-backed audit logging:
- Tracks all admin actions
- Stores before/after values
- Queryable by entity type

## Configuration

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `DATABASE_URL` | Database connection string | `sqlite:///webcms.db` |
| `SECRET_KEY` | Flask secret key | `dev-secret-key` |
| `JWT_SECRET_KEY` | JWT signing key | `jwt-secret-key` |
| `ADMIN_EMAIL` | Default admin email | `admin@example.com` |
| `CACHE_ENABLED` | Enable caching | `True` |

### Settings API

Settings are persisted to database and cached:

```python
# Get settings
GET /api/v1/admin/settings

# Update settings
PUT /api/v1/admin/settings
{
  "site_name": "My Site",
  "posts_per_page": 10
}
```

## Testing

### Test Coverage

| Component | Tests | Status |
|-----------|-------|--------|
| Dashboard | 2 | ✅ Pass |
| Settings | 3 | ✅ Pass |
| Users | 2 | ✅ Pass |
| Roles | 2 | ✅ Pass |
| Content | 3 | ✅ Pass |
| Media | 1 | ✅ Pass |
| Plugins | 1 | ✅ Pass |
| Templates | 1 | ✅ Pass |
| Themes | 1 | ✅ Pass |
| Cache | 1 | ✅ Pass |
| Backups | 1 | ✅ Pass |
| Tenants | 1 | ✅ Pass |
| Search | 1 | ✅ Pass |
| Notifications | 1 | ✅ Pass |

**Total: 21 unit tests + 16 e2e tests = 37 tests**

### Test Structure

```
tests/
├── __init__.py
├── test_admin_unittest.py    # Unit tests
└── test_admin_api.py         # Pytest version (optional)

test_admin_e2e.py            # End-to-end tests
run_tests.py                 # Test runner
```

## Deployment

### Docker

```dockerfile
FROM python:3.9-slim

WORKDIR /app
COPY . /app

RUN pip install -r requirements.txt

EXPOSE 5000

CMD ["python3", "run.py"]
```

### Production Checklist

- [ ] Set strong `SECRET_KEY` and `JWT_SECRET_KEY`
- [ ] Configure production database (PostgreSQL/MySQL)
- [ ] Enable HTTPS
- [ ] Set up log rotation
- [ ] Configure backup schedule
- [ ] Set up monitoring
- [ ] Run tests before deployment

### Security Considerations

1. **Authentication** - JWT tokens with expiration
2. **Authorization** - Role-based access control
3. **Input Validation** - All inputs sanitized
4. **SQL Injection** - Parameterized queries
5. **XSS Protection** - Output encoding
6. **Audit Logging** - All actions logged

## Troubleshooting

### Common Issues

#### Import Errors
```bash
# Ensure PYTHONPATH includes project root
export PYTHONPATH=/path/to/KosCMS:$PYTHONPATH
```

#### Database Connection
```bash
# Check database URL
export DATABASE_URL=sqlite:///webcms.db
# or
export DATABASE_URL=postgresql://user:pass@localhost/webcms
```

#### Permission Denied
Ensure the application has write permissions for:
- Database file (if using SQLite)
- Upload directory
- Log directory

### Debug Mode

Enable debug logging:
```python
# In admin_api.py
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

### Code Style

- Follow PEP 8
- Use type hints where possible
- Document all public methods
- Include docstrings

## License

MIT License - See LICENSE file for details

## Support

- Documentation: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- Issues: GitHub Issues
- Email: support@webcms.example.com

---

**Version**: 1.0.0  
**Status**: Production Ready  
**Last Updated**: 2024
