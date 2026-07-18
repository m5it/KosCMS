
# WebCMS Admin Panel - Quick Reference Card

**One-page reference for common tasks**

---

## 🚀 Quick Start (5 minutes)

```bash
# 1. Verify
python3 final_verification.py

# 2. Run
python3 run.py -d

# 3. Test
curl http://localhost:5000/health
```

---

## 📋 Common Commands

| Task | Command |
|------|---------|
| Start app | `python3 run.py -d` |
| Run tests | `python3 tests/test_simple.py` |
| Verify | `python3 final_verification.py` |
| CLI info | `python3 -m webcms.cli info` |
| Deploy | `./scripts/deploy.sh` |
| Logs | `docker-compose logs -f` |

---

## 🔗 API Endpoints

### REST
```
GET    /api/v1/admin/dashboard
GET    /api/v1/admin/users
POST   /api/v1/admin/users
GET    /api/v1/admin/pages
POST   /api/v1/admin/pages
GET    /api/v1/admin/settings
PUT    /api/v1/admin/settings
GET    /health
```

### GraphQL
```
POST /graphql
Query: { users { id username } }
```

---

## 🐍 SDK Usage

```python
from webcms.client import WebCMSAdminClient

client = WebCMSAdminClient(
    base_url='http://localhost:5000',
    api_key='your-key'
)

# Users
users = client.list_users()

# Pages
page = client.create_page(
    title='Hello',
    slug='hello',
    content='World'
)
```

---

## 🐳 Docker Commands

| Task | Command |
|------|---------|
| Start | `docker-compose up -d` |
| Stop | `docker-compose down` |
| Logs | `docker-compose logs -f` |
| Rebuild | `docker-compose up -d --build` |
| Status | `docker-compose ps` |

---

## 🔧 Troubleshooting

| Issue | Solution |
|-------|----------|
| 502 error | `docker-compose restart` |
| DB locked | `chmod 644 data/*.db` |
| Port in use | Change port in docker-compose.yml |
| Import error | `pip install -r requirements.txt` |

---

## 📁 Key Files

| File | Purpose |
|------|---------|
| `run.py` | Start application |
| `final_verification.py` | Verify installation |
| `docker-compose.yml` | Deploy stack |
| `scripts/deploy.sh` | Auto-deploy |
| `.env` | Configuration |

---

## 📊 Health Checks

- **Web:** http://localhost:5000/health
- **CLI:** `python3 -m webcms.cli health`
- **Docker:** `docker-compose ps`

---

## 🆘 Emergency

```bash
# Full reset
docker-compose down
docker-compose up -d --build

# Restore backup
cp backups/webcms-*.db data/webcms.db
```

---

**Docs:** See PROJECT_INDEX.md for complete documentation

**Status:** ✅ Production Ready
