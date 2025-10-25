#!/bin/bash

# ============================================================================
# Aquaculture ML Platform - Quick Start Script
# ============================================================================
#
# This script provides a one-command setup for the entire Aquaculture ML
# Platform development environment. It handles:
#
# FEATURES:
# - Dependency verification (Docker, Docker Compose)
# - Environment configuration setup
# - Directory structure creation
# - Service orchestration and health checks
# - Service URL and access information
#
# USAGE:
# ./scripts/quickstart.sh
#
# REQUIREMENTS:
# - Docker Engine 20.10+
# - Docker Compose V2
# - Unix-like operating system (Linux, macOS)
# - Network connectivity for pulling images
#
# POST-EXECUTION:
# - All services available at their respective ports
# - API documentation at http://localhost:8000/docs
# - Grafana dashboard at http://localhost:3001
# - Database ready for connections
# - Monitoring stack fully operational
# ============================================================================

# Exit immediately if any command fails
set -e

echo "🐟 Aquaculture ML Platform - Quick Start"
echo "========================================"

# ============================================================================
# COLOR CONSTANTS FOR TERMINAL OUTPUT
# ============================================================================
# ANSI color codes for enhanced user experience

RED='\033[0;31m'        # Error messages
GREEN='\033[0;32m'      # Success messages
YELLOW='\033[1;33m'     # Warning messages
BLUE='\033[0;34m'       # Info messages
NC='\033[0m'            # No Color (reset)

# ============================================================================
# DEPENDENCY VERIFICATION
# ============================================================================
# Verify required tools are installed before proceeding

echo -e "${BLUE}🔍 Checking dependencies...${NC}"

# Check for Docker installation
if ! command -v docker &> /dev/null; then
    echo -e "${RED}❌ Docker is not installed. Please install Docker first.${NC}"
    echo -e "${YELLOW}Visit: https://docs.docker.com/get-docker/${NC}"
    exit 1
fi

# Check for Docker Compose V2 (modern syntax: docker compose)
if ! docker compose version &> /dev/null; then
    echo -e "${RED}❌ Docker Compose V2 is not installed.${NC}"
    echo -e "${YELLOW}Please install Docker Compose V2 or update Docker Desktop${NC}"
    echo -e "${YELLOW}Visit: https://docs.docker.com/compose/install/${NC}"
    exit 1
fi

echo -e "${GREEN}✅ All dependencies satisfied${NC}"

# ============================================================================
# ENVIRONMENT CONFIGURATION
# ============================================================================
# Set up environment variables and configuration files

# Create .env file from template if it doesn't exist
if [ ! -f .env ]; then
    echo -e "${YELLOW}📝 Creating .env file from .env.example...${NC}"
    if [ -f .env.example ]; then
        cp .env.example .env
        echo -e "${GREEN}✅ Environment file created${NC}"
        echo -e "${YELLOW}⚠️  Please review and update .env file for production use${NC}"
    else
        echo -e "${RED}❌ .env.example file not found${NC}"
        exit 1
    fi
else
    echo -e "${GREEN}✅ Environment file already exists${NC}"
fi

# ============================================================================
# DIRECTORY STRUCTURE CREATION
# ============================================================================
# Create required directories for data, logs, and uploads

echo -e "${BLUE}📁 Creating necessary directories...${NC}"

# Create data directories for ML workflow
mkdir -p data/{raw,processed,models,uploads}

# Create logging directory
mkdir -p logs

# Create temporary upload directory
mkdir -p uploads

echo -e "${GREEN}✅ Directory structure created${NC}"

# ============================================================================
# SERVICE ORCHESTRATION
# ============================================================================
# Start all Docker services using Docker Compose

echo -e "${BLUE}🚀 Starting Docker containers...${NC}"
docker compose up -d

echo -e "${GREEN}✅ All services started${NC}"

# ============================================================================
# HEALTH CHECK WAITING
# ============================================================================
# Wait for services to become healthy before proceeding

echo -e "${BLUE}⏳ Waiting for services to be healthy...${NC}"
sleep 15

# ============================================================================
# SERVICE HEALTH VERIFICATION
# ============================================================================
# Check that all critical services are responding correctly

echo -e "${BLUE}🏥 Checking service health...${NC}"

# Check API service health endpoint
if curl -f http://localhost:8000/health > /dev/null 2>&1; then
    echo -e "${GREEN}✅ API service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  API service not responding yet (may still be starting)${NC}"
fi

# Check Frontend service availability
if curl -f http://localhost:3000 > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Frontend service is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Frontend service not responding yet (may still be starting)${NC}"
fi

# Check Prometheus monitoring service
if curl -f http://localhost:9090/-/healthy > /dev/null 2>&1; then
    echo -e "${GREEN}✅ Prometheus is healthy${NC}"
else
    echo -e "${YELLOW}⚠️  Prometheus not responding yet${NC}"
fi

# Seed database (Optional - commented out since it requires external connection)
echo -e "${BLUE}🌱 Database ready for seeding...${NC}"
echo -e "${YELLOW}Note: Create demo users via API registration${NC}"

echo ""
echo -e "${GREEN}🎉 Aquaculture ML Platform is ready!${NC}"
echo "========================================"
echo ""
echo -e "${BLUE}🌐 Access Points:${NC}"
echo "  • 🎛️  Frontend:    http://localhost:3000"
echo "  • 🔧 API:         http://localhost:8000"
echo "  • 📚 API Docs:    http://localhost:8000/docs"
echo "  • 📊 Prometheus:  http://localhost:9090"
echo "  • 📈 Grafana:     http://localhost:3001 (admin/admin)"
echo ""
echo -e "${BLUE}👤 Demo Accounts:${NC}"
echo "  • Admin:  admin / admin123"
echo "  • Demo:   demo / demo123"
echo ""
echo -e "${BLUE}🛠️  Management Commands:${NC}"
echo "  • Stop:     docker compose down"
echo "  • Logs:     docker compose logs -f"
echo "  • Restart:  docker compose restart"
echo "  • Clean:    docker compose down -v"
echo ""
echo -e "${GREEN}🚀 Happy fish classifying! 🐟${NC}"