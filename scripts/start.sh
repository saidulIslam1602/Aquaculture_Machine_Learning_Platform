#!/bin/bash

# Aquaculture ML Platform - Startup Script

set -e

echo "[INFO] Starting Aquaculture ML Platform..."

# Check if Docker is installed
if ! command -v docker &> /dev/null; then
    echo "[ERROR] Docker is not installed. Please install Docker first."
    exit 1
fi

# Check if Docker Compose is installed
if ! command -v docker-compose &> /dev/null; then
    echo "[ERROR] Docker Compose is not installed. Please install Docker Compose first."
    exit 1
fi

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "[INFO] Creating .env file from .env.example..."
    cp .env.example .env
    echo "[WARN] Please review and update .env file with your configuration"
fi

# Create necessary directories
echo "[INFO] Creating necessary directories..."
mkdir -p data/{raw,processed,models}
mkdir -p logs

# Start services
echo "[INFO] Starting Docker containers..."
docker-compose up -d

# Wait for services to be healthy
echo "[INFO] Waiting for services to be healthy..."
sleep 10

# Check service health
echo "[INFO] Checking service health..."
curl -f http://localhost:8000/health || echo "[WARN] API service not responding yet"
curl -f http://localhost:9090/-/healthy || echo "[WARN] Prometheus not responding yet"
curl -f http://localhost:3000/api/health || echo "[WARN] Grafana not responding yet"

echo ""
echo "[SUCCESS] Aquaculture ML Platform is starting up!"
echo ""
echo "Access points:"
echo "  - API:        http://localhost:8000"
echo "  - API Docs:   http://localhost:8000/docs"
echo "  - Prometheus: http://localhost:9090"
echo "  - Grafana:    http://localhost:3000 (admin/admin)"
echo ""
echo "View logs with: docker-compose logs -f"
echo "Stop services with: docker-compose down"
echo ""
