# WebCMS Deployment Guide

## Requirements

- Docker & Docker Compose
- 4GB RAM minimum (8GB recommended with Elasticsearch)
- SSL certificates for production

## Quick Start

```bash
cd docs/deployment
docker-compose up -d
```

## Production Checklist

1. Configure environment variables
2. Set up SSL/TLS
3. Configure backup storage (S3/Azure)
4. Set up monitoring and alerts
5. Enable Elasticsearch security
6. Configure Redis persistence

## Environment Variables

- `REDIS_URL`: Redis connection string
- `ELASTICSEARCH_URL`: Elasticsearch URL
- `DATABASE_URL`: PostgreSQL connection string
- `SMTP_HOST`, `SMTP_USER`, `SMTP_PASS`: Email settings
- `SENDGRID_API_KEY`: Alternative email adapter

## Scaling

- Run multiple WebCMS app instances behind a load balancer
- Use managed Redis (ElastiCache) and PostgreSQL (RDS)
- Use managed Elasticsearch service
