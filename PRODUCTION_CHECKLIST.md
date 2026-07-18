
# WebCMS Admin Panel - Production Deployment Checklist

## Pre-Deployment ✅

### Environment Setup
- [ ] Create `.env` file with secure values
- [ ] Generate strong JWT_SECRET_KEY (32+ chars)
- [ ] Generate strong ADMIN_API_KEY (32+ chars)
- [ ] Set DATABASE_URL to production database
- [ ] Configure REDIS_URL for caching
- [ ] Set FLASK_ENV=production

### SSL/TLS Certificates
- [ ] Obtain SSL certificates from trusted CA
- [ ] Place certificates in `ssl/` directory
- [ ] Verify certificate permissions (600 for key, 644 for cert)
- [ ] Test certificate validity

### Security Hardening
- [ ] Run security audit: `python3 scripts/security_audit.py`
- [ ] Disable debug mode
- [ ] Enable rate limiting
- [ ] Configure CORS properly
- [ ] Set up firewall rules

## Deployment Steps 🚀

### 1. Server Preparation
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker and Docker Compose
curl -fsSL https://get.docker.com | sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo curl -L "https://github.com/docker/compose/releases/latest/download/docker-compose-$(uname -s)-$(uname -m)" -o /usr/local/bin/docker-compose
sudo chmod +x /usr/local/bin/docker-compose
```

### 2. Application Deployment
```bash
# Clone repository
git clone <repository-url>
cd webcms

# Run deployment script
./scripts/deploy.sh

# Verify deployment
curl http://localhost:5000/health
```

### 3. Post-Deployment Verification
- [ ] Health check passes
- [ ] All services running: `docker-compose ps`
- [ ] Logs show no errors: `docker-compose logs -f`
- [ ] SSL working: `curl -I https://localhost`
- [ ] Admin panel accessible: `https://localhost/admin`

## Monitoring & Maintenance 📊

### Health Monitoring
- [ ] Set up uptime monitoring
- [ ] Configure log aggregation
- [ ] Enable performance metrics
- [ ] Set up alerting

### Backup Strategy
- [ ] Automated database backups
- [ ] File upload backups
- [ ] Configuration backups
- [ ] Test restore procedures

### Security Updates
- [ ] Weekly dependency updates
- [ ] Monthly security audits
- [ ] Quarterly penetration testing
- [ ] Annual security review

## Troubleshooting 🔧

### Common Issues

**Application won't start:**
```bash
docker-compose logs webcms
```

**Database connection failed:**
```bash
# Check database permissions
ls -la data/
# Fix permissions
chmod 755 data
chmod 644 data/webcms.db
```

**SSL certificate errors:**
```bash
# Check certificate validity
openssl x509 -in ssl/cert.pem -text -noout
```

**Rate limiting too strict:**
```bash
# Adjust in nginx.conf
limit_req zone=api burst=50 nodelay;
```

## Rollback Procedure ⏮️

If deployment fails:

```bash
# Stop services
docker-compose down

# Restore from backup
cp backups/webcms.db.backup data/webcms.db

# Restart
docker-compose up -d

# Verify
curl http://localhost:5000/health
```

## Support Contacts 📞

- **Documentation**: README_ADMIN_PANEL.md
- **API Reference**: API_DOCUMENTATION.md
- **Emergency**: Check logs with `docker-compose logs -f`

---

**Deployment Date:** ___________
**Deployed By:** ___________
**Verified By:** ___________
