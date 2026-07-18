# WebCMS Admin Panel - Deployment Guide

## Quick Start

### Prerequisites
- Docker 20.10+
- Docker Compose 2.0+
- 2GB RAM minimum
- 10GB disk space

### Production Deployment

```bash
# 1. Clone repository
git clone <repository-url>
cd KosCMS

# 2. Set environment variables
export SECRET_KEY="your-secure-secret-key"
export JWT_SECRET_KEY="your-secure-jwt-key"

# 3. Build and start
make deploy
# or
docker-compose up -d --build

# 4. Verify deployment
curl http://localhost/health
```

## Configuration

### Environment Variables

Create `.env` file:

```bash
# Required
SECRET_KEY=your-secure-random-string
JWT_SECRET_KEY=your-secure-jwt-key

# Database (optional, defaults to SQLite)
DATABASE_URL=postgresql://user:pass@db:5432/webcms

# Email (optional)
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USER=your-email@gmail.com
SMTP_PASS=your-app-password

# Storage (optional)
UPLOAD_DIR=/app/uploads
BACKUP_DIR=/app/backups
```

### SSL Certificates

Place certificates in `ssl/` directory:
```bash
mkdir ssl
cp your-cert.pem ssl/cert.pem
cp your-key.pem ssl/key.pem
```

## Deployment Options

### Option 1: Docker Compose (Recommended)

```bash
# Production
docker-compose up -d

# Development
docker-compose -f docker-compose.dev.yml up -d
```

### Option 2: Manual Installation

```bash
# Install dependencies
pip install -r requirements.txt

# Set environment
export FLASK_ENV=production
export SECRET_KEY="your-secret"
export DATABASE_URL="postgresql://..."

# Initialize database
python3 -c "from webcms.app_factory import create_app; create_app()"

# Run with gunicorn
gunicorn -w 4 -b 0.0.0.0:5000 run:app
```

### Option 3: Systemd Service

Create `/etc/systemd/system/webcms.service`:

```ini
[Unit]
Description=WebCMS Admin Panel
After=network.target

[Service]
User=webcms
Group=webcms
WorkingDirectory=/opt/webcms
Environment="PATH=/opt/webcms/venv/bin"
Environment="FLASK_ENV=production"
Environment="SECRET_KEY=your-secret"
ExecStart=/opt/webcms/venv/bin/gunicorn -w 4 -b 127.0.0.1:5000 run:app
Restart=always

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable webcms
sudo systemctl start webcms
```

## Monitoring

### Health Check
```bash
curl http://localhost/health
```

Expected response:
```json
{"status": "healthy", "timestamp": "2024-01-15T10:30:00"}
```

### Logs
```bash
# Docker logs
docker-compose logs -f web

# System logs
sudo journalctl -u webcms -f
```

### Metrics
- Memory usage: `docker stats`
- Disk usage: `df -h`
- Database size: `docker-compose exec db psql -U webcms -c "SELECT pg_size_pretty(pg_database_size('webcms'));"`

## Backup & Recovery

### Automated Backups

Backups run automatically daily. Access via:
- API: `POST /api/v1/admin/backups`
- Admin UI: Settings > Backups

### Manual Backup
```bash
# Create backup
curl -X POST \
  -H "Authorization: Bearer <token>" \
  http://localhost/api/v1/admin/backups

# List backups
curl -H "Authorization: Bearer <token>" \
  http://localhost/api/v1/admin/backups
```

### Restore
```bash
# Restore from backup
curl -X POST \
  -H "Authorization: Bearer <token>" \
  http://localhost/api/v1/admin/backups/<backup-id>/restore
```

## Security Checklist

- [ ] Change default SECRET_KEY
- [ ] Change default JWT_SECRET_KEY
- [ ] Enable HTTPS with valid SSL certificate
- [ ] Configure firewall (allow only 80, 443)
- [ ] Disable debug mode in production
- [ ] Set up log rotation
- [ ] Enable database backups
- [ ] Configure monitoring alerts
- [ ] Set up fail2ban for brute force protection
- [ ] Regular security updates

## Troubleshooting

### Container won't start
```bash
# Check logs
docker-compose logs web

# Check environment
docker-compose exec web env | grep SECRET
```

### Database connection failed
```bash
# Check database container
docker-compose ps db
docker-compose logs db

# Test connection
docker-compose exec db psql -U webcms -c "\l"
```

### High memory usage
```bash
# Restart containers
docker-compose restart

# Check for memory leaks
docker stats --no-stream
```

### SSL certificate errors
```bash
# Check certificate
openssl x509 -in ssl/cert.pem -text -noout

# Test SSL
curl -v https://localhost
```

## Scaling

### Horizontal Scaling

Use Docker Swarm or Kubernetes:

```yaml
# docker-compose.scale.yml
version: '3.8'
services:
  web:
    deploy:
      replicas: 3
      resources:
        limits:
          memory: 512M
```

### Database Scaling

- Use PostgreSQL read replicas
- Enable connection pooling (PgBouncer)
- Consider Redis Cluster for caching

## Updates

### Update Application
```bash
# Pull latest code
git pull origin main

# Rebuild and restart
docker-compose up -d --build

# Run migrations if needed
docker-compose exec web python3 -c "from webcms.app_factory import create_app; create_app()"
```

### Update Dependencies
```bash
# Update requirements.txt
pip install -U -r requirements.txt
pip freeze > requirements.txt

# Rebuild
docker-compose up -d --build
```

## Support

- Documentation: [README_ADMIN_PANEL.md](README_ADMIN_PANEL.md)
- API Docs: [API_DOCUMENTATION.md](API_DOCUMENTATION.md)
- Issues: GitHub Issues

---

**Version**: 1.0.0  
**Last Updated**: 2024
