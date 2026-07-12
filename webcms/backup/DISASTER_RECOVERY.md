# WebCMS Disaster Recovery Plan

## Overview

This document outlines disaster recovery procedures for WebCMS deployments.

## Backup Strategy

- **Full backups**: Daily at 02:00 UTC
- **Incremental backups**: Every 6 hours
- **Media backups**: Continuous sync to S3/Azure
- **Retention**: 30 days

## Recovery Procedures

### 1. Database Restore

Use the backup API or CLI:

```bash
curl -X POST /api/v1/backups/<backup_id>/restore
```

### 2. Media Restore

Media files are restored from object storage (S3/Azure) using the same restore endpoint.

### 3. Complete Site Recovery

1. Provision new infrastructure
2. Restore database from latest verified backup
3. Sync media from object storage
4. Verify integrity using `/api/v1/backups/<backup_id>/verify`
5. Update DNS and SSL certificates

## Encryption

Backups are encrypted at rest using Fernet (AES-128). Store the encryption key in a secure secrets manager.

## Monitoring

Monitor backup health via:

```bash
curl /api/v1/backups/monitor
```

Alerts are triggered when backups fail or verification fails.

## RTO / RPO

- **RTO**: 4 hours
- **RPO**: 6 hours
