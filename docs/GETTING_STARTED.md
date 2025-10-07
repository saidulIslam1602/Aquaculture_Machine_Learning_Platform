# 🚀 Getting Started with Aquaculture ML Platform

## Quick Start Guide

This guide will help you get the platform running in under 5 minutes.

## Prerequisites

Ensure you have these installed:

```bash
# Check Docker
docker --version
# Should show: Docker version 20.10.x or higher

# Check Docker Compose
docker-compose --version
# Should show: Docker Compose version 2.x or higher
```

If not installed:
- **Docker**: https://docs.docker.com/get-docker/
- **Docker Compose**: https://docs.docker.com/compose/install/

## Step 1: Setup Environment

```bash
# Navigate to project directory
cd /home/saidul/Desktop/fishCulturing/aquaculture-ml-platform

# Copy environment configuration
cp .env.example .env

# (Optional) Edit .env if you want to change any settings
nano .env
```

## Step 2: Start Services

```bash
# Start all services in background
docker-compose up -d

# This will start:
# - PostgreSQL (database)
# - Redis (cache)
# - Kafka + Zookeeper (messaging)
# - API service
# - ML service
# - Worker service
# - Prometheus (metrics)
# - Grafana (dashboards)
```

## Step 3: Verify Services

```bash
# Check all services are running
docker-compose ps

# Should show all services as "Up" or "healthy"

# Check API health
curl http://localhost:8000/health

# Should return: {"status":"healthy",...}
```

## Step 4: Access Services

Open in your browser:

- **API Documentation**: http://localhost:8000/docs
- **Grafana Dashboards**: http://localhost:3000 (admin/admin)
- **Prometheus Metrics**: http://localhost:9090

## Step 5: Test Authentication

### Register a User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "demo@example.com",
    "username": "demo",
    "password": "demo12345",
    "full_name": "Demo User"
  }'
```

### Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=demo&password=demo12345"
```

Save the `access_token` from the response!

## Common Commands

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api

# Restart services
docker-compose restart

# Stop services
docker-compose stop

# Stop and remove containers (keeps data)
docker-compose down

# Remove everything including data
docker-compose down -v
```

## Troubleshooting

### Services not starting?

```bash
# Check logs
docker-compose logs

# Rebuild and restart
docker-compose up -d --build
```

### Port already in use?

```bash
# Find what's using the port
sudo lsof -i :8000

# Kill the process or change port in docker-compose.yml
```

### Database connection issues?

```bash
# Check PostgreSQL is ready
docker-compose exec postgres pg_isready -U aquaculture

# Connect to database
docker-compose exec postgres psql -U aquaculture -d aquaculture_db
```

## Next Steps

- Read [SETUP.md](SETUP.md) for detailed configuration
- Read [PHASE1_COMPLETE.md](PHASE1_COMPLETE.md) for what's included
- Explore API at http://localhost:8000/docs
- Set up Grafana dashboards at http://localhost:3000

## Need Help?

1. Check the logs: `docker-compose logs -f`
2. Verify health: `curl http://localhost:8000/health/detailed`
3. Review documentation in `docs/` folder

---

**You're all set! 🎉**
