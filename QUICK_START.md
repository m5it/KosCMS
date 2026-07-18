
# WebCMS Admin Panel - Quick Start Guide

## 🚀 Get Started in 5 Minutes

### Prerequisites
- Python 3.8+
- Docker (optional, for containerized deployment)

---

## Option 1: Quick Local Setup

### 1. Clone and Install
```bash
git clone <repository-url>
cd KosCMS
pip install -r requirements.txt
```

### 2. Run Development Server
```bash
python3 run.py -d
```

### 3. Access Admin Panel
Open http://localhost:5000/admin in your browser

---

## Option 2: Docker Setup (Recommended)

### 1. Start with Docker Compose
```bash
# Development
docker-compose -f docker-compose.dev.yml up -d

# Production
docker-compose up -d
```

### 2. Verify Installation
```bash
curl http://localhost:5000/health
```

---

## Option 3: Using Makefile

```bash
# Install dependencies
make install

# Run development server
make dev

# Run tests
make test

# Build Docker image
make docker-build

# Deploy production
make deploy
```

---

## First Steps

### 1. Create Admin User
```bash
# Via API
curl -X POST http://localhost:5000/api/v1/admin/users \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "email": "admin@example.com",
    "password": "securepassword",
    "role": "admin"
  }'
```

### 2. Login
```bash
curl -X POST http://localhost:5000/api/v1/auth/login \
  -H "Content-Type: application/json" \
  -d '{
    "username": "admin",
    "password": "securepassword"
  }'
```

### 3. Configure Settings
```bash
curl -X PUT http://localhost:5000/api/v1/admin/settings \
  -H "Authorization: Bearer <your-token>" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "My Website",
    "site_url": "https://example.com"
  }'
```

---

## API Quick Reference

### Dashboard
```bash
GET /api/v1/admin/dashboard
```

### Content
```bash
# List pages
GET /api/v1/admin/pages

# Create page
POST /api/v1/admin/pages
{"title": "About", "content": "..."}

# List posts
GET /api/v1/admin/posts
```

### Users & Roles
```bash
# List users
GET /api/v1/admin/users

# Create user
POST /api/v1/admin/users
{"username": "john", "email": "john@example.com"}

# List roles
GET /api/v1/admin/roles
```

### Media
```bash
# List media
GET /api/v1/admin/media

# Upload file
POST /api/v1/admin/media
Content-Type: multipart/form-data
file: <binary data>
```

### Settings
```bash
# Get settings
GET /api/v1/admin/settings

# Update settings
PUT /api/v1/admin/settings
{"site_name": "New Name"}
```

---

## Testing

### Run All Tests
```bash
python3 run_tests.py
```

### Run Specific Tests
```bash
# Unit tests only
python3 tests/test_admin_unittest.py

# End-to-end tests only
python3 test_admin_e2e.py
```

---

## Common Tasks

### Create a Blog Post
```bash
curl -X POST http://localhost:5000/api/v1/admin/posts \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "My First Post",
    "content": "Hello world!",
    "status": "published"
  }'
```

### Upload an Image
```bash
curl -X POST http://localhost:5000/api/v1/admin/media \
  -H "Authorization: Bearer <token>" \
  -F "file=@/path/to/image.jpg"
```

### Create Backup
```bash
curl -X POST http://localhost:5000/api/v1/admin/backups \
  -H "Authorization: Bearer <token>"
```

### Clear Cache
```bash
curl -X POST http://localhost:5000/api/v1/admin/cache/invalidate \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{"pattern": "*"}'
```

---

## Troubleshooting

### Port Already in Use
```bash
# Kill process on port 5000
lsof -ti:5000 | xargs kill -9

# Or use different port
python3 run.py -d -p 8080
```

### Database Locked
```bash
# Remove SQLite lock file
rm -f webcms.db-journal
```

### Import Errors
```bash
# Ensure PYTHONPATH is set
export PYTHONPATH=/path/to/KosCMS:$PYTHONPATH
```

### Permission Denied
```bash
# Fix permissions
chmod -R 755 uploads/
chmod -R 755 backups/
```

---

## Configuration

### Environment Variables
Create `.env` file:
```bash
SECRET_KEY=your-secret-key
JWT_SECRET_KEY=your-jwt-key
DATABASE_URL=sqlite:///webcms.db
```

### Settings via API
```bash
curl -X PUT http://localhost:5000/api/v1/admin/settings \
  -H "Authorization: Bearer <token>" \
  -H "Content-Type: application/json" \
  -d '{
    "site_name": "My Site",
    "posts_per_page": 10,
    "cache_enabled": true
  }'
```

---

## Next Steps

1. **Explore the API** - See [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
2. **Customize Themes** - Edit templates in `templates/`
3. **Add Plugins** - Place in `plugins/` directory
4. **Configure Backup** - Set up automated backups
5. **Monitor Performance** - Check `/api/v1/admin/dashboard`

---

## Support

- 📖 Documentation: [README_ADMIN_PANEL.md](README_ADMIN_PANEL.md)
- 🔧 API Reference: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- 🚀 Deployment: [DEPLOYMENT_GUIDE.md](DEPLOYMENT_GUIDE.md)

---

**Ready to build amazing things! 🎉**
