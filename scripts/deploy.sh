
#!/bin/bash
# WebCMS Admin Panel - Production Deployment Script

set -e

echo "=========================================="
echo "WebCMS Admin Panel - Deployment"
echo "=========================================="

# Configuration
APP_NAME="webcms"
DOCKER_COMPOSE_FILE="docker-compose.yml"
ENV_FILE=".env"

# Check prerequisites
echo "Checking prerequisites..."
command -v docker >/dev/null 2>&1 || { echo "Docker required but not installed"; exit 1; }
command -v docker-compose >/dev/null 2>&1 || { echo "Docker Compose required but not installed"; exit 1; }

# Create environment file if not exists
if [ ! -f "$ENV_FILE" ]; then
    echo "Creating environment file..."
    cat > "$ENV_FILE" << EOF
# WebCMS Environment Configuration
FLASK_ENV=production
JWT_SECRET_KEY=$(openssl rand -hex 32)
ADMIN_API_KEY=$(openssl rand -hex 32)
DATABASE_URL=sqlite:///data/webcms.db
CACHE_TYPE=redis
REDIS_URL=redis://redis:6379/0
EOF
    echo "Created $ENV_FILE - please review and customize"
fi

# Create required directories
echo "Creating directories..."
mkdir -p data uploads logs backups ssl

# Set permissions
chmod 755 data uploads logs backups

# Generate SSL certificates if not exists
if [ ! -f "ssl/cert.pem" ]; then
    echo "Generating self-signed SSL certificates..."
    openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
        -keyout ssl/key.pem \
        -out ssl/cert.pem \
        -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
    echo "Generated self-signed certificates - replace with real certificates for production"
fi

# Pull latest images
echo "Pulling latest images..."
docker-compose -f "$DOCKER_COMPOSE_FILE" pull

# Build and start services
echo "Building and starting services..."
docker-compose -f "$DOCKER_COMPOSE_FILE" up -d --build

# Wait for services
echo "Waiting for services to start..."
sleep 10

# Health check
echo "Performing health check..."
if curl -f http://localhost:5000/health >/dev/null 2>&1; then
    echo "✓ Application is healthy"
else
    echo "✗ Health check failed"
    docker-compose -f "$DOCKER_COMPOSE_FILE" logs
    exit 1
fi

# Show status
echo ""
echo "=========================================="
echo "Deployment Complete!"
echo "=========================================="
echo "Application URL: https://localhost"
echo "Admin Panel: https://localhost/admin"
echo "Health Check: http://localhost:5000/health"
echo ""
echo "Useful commands:"
echo "  docker-compose logs -f    # View logs"
echo "  docker-compose ps         # Check status"
echo "  docker-compose down       # Stop services"
echo "=========================================="
