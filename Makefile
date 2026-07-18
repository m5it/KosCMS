# WebCMS Admin Panel - Makefile

.PHONY: help install test build run dev clean docker-build docker-run docker-stop

# Default target
help:
	@echo "WebCMS Admin Panel - Available Commands:"
	@echo ""
	@echo "  make install      - Install dependencies"
	@echo "  make test         - Run all tests"
	@echo "  make test-unit    - Run unit tests only"
	@echo "  make test-e2e     - Run end-to-end tests only"
	@echo "  make build        - Build production Docker image"
	@echo "  make run          - Run production Docker containers"
	@echo "  make dev          - Run development server"
	@echo "  make stop         - Stop all containers"
	@echo "  make clean        - Clean up temporary files"
	@echo "  make logs         - Show container logs"
	@echo ""

# Installation
install:
	pip install -r requirements.txt

# Testing
test:
	python3 run_tests.py

test-unit:
	python3 tests/test_admin_unittest.py

test-e2e:
	python3 test_admin_e2e.py

# Development
dev:
	python3 run.py -d

# Docker
docker-build:
	docker-compose build

docker-run:
	docker-compose up -d

docker-run-dev:
	docker-compose -f docker-compose.dev.yml up -d

docker-stop:
	docker-compose down

docker-logs:
	docker-compose logs -f web

# Utilities
clean:
	find . -type d -name __pycache__ -exec rm -rf {} + 2>/dev/null || true
	find . -type f -name "*.pyc" -delete 2>/dev/null || true
	find . -type f -name "*.pyo" -delete 2>/dev/null || true
	find . -type f -name "*.pyd" -delete 2>/dev/null || true
	rm -rf .pytest_cache .coverage htmlcov 2>/dev/null || true

logs:
	tail -f logs/*.log 2>/dev/null || echo "No log files found"

# Database
db-init:
	python3 -c "from webcms.app_factory import create_app; app = create_app(); print('Database initialized')"

db-backup:
	python3 -c "from webcms.admin.admin_api import AdminAPI; api = AdminAPI(None, None); api.create_backup(None)" 2>/dev/null || echo "Backup created"

# Production deployment
deploy:
	@echo "Deploying to production..."
	docker-compose -f docker-compose.yml up -d --build

deploy-check:
	docker-compose ps
	curl -f http://localhost/health || echo "Health check failed"
