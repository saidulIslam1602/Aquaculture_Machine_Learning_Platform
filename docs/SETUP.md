# 🚀 Aquaculture ML Platform - Setup Guide

## Phase 1 Complete! ✅

You now have a **production-grade foundation** with:
- ✅ Docker & Docker Compose configuration
- ✅ PostgreSQL database with proper schema
- ✅ Redis for caching
- ✅ Kafka for message streaming
- ✅ FastAPI with JWT authentication
- ✅ Prometheus + Grafana monitoring
- ✅ Proper project structure

## 📋 Prerequisites

Before starting, ensure you have:

1. **Docker** (20.10+)
   ```bash
   docker --version
   ```

2. **Docker Compose** (2.0+)
   ```bash
   docker-compose --version
   ```

3. **Git**
   ```bash
   git --version
   ```

## 🏁 Quick Start

### 1. Clone and Setup

```bash
cd /home/saidul/Desktop/fishCulturing/aquaculture-ml-platform

# Copy environment file
cp .env.example .env

# Review and update .env if needed
nano .env
```

### 2. Start All Services

```bash
# Option A: Use the startup script
./scripts/start.sh

# Option B: Manual start
docker-compose up -d
```

### 3. Verify Services

```bash
# Check running containers
docker-compose ps

# Check API health
curl http://localhost:8000/health

# Check detailed health
curl http://localhost:8000/health/detailed
```

### 4. Access Services

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (login: admin/admin)

## 📊 Service Details

### PostgreSQL Database
- **Port**: 5432
- **Database**: aquaculture_db
- **User**: aquaculture
- **Password**: aquaculture123 (change in production!)

### Redis Cache
- **Port**: 6379
- **No password** (add in production!)

### Kafka
- **Port**: 9092
- **Topics**: fish-predictions, fish-images

### API Service
- **Port**: 8000
- **Features**:
  - JWT Authentication
  - Rate Limiting
  - Prometheus Metrics
  - OpenAPI Documentation

## 🔐 Authentication

### Register a New User

```bash
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{
    "email": "user@example.com",
    "username": "testuser",
    "password": "securepassword123",
    "full_name": "Test User"
  }'
```

### Login and Get Token

```bash
curl -X POST http://localhost:8000/api/v1/auth/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=testuser&password=securepassword123"
```

Response:
```json
{
  "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "token_type": "bearer"
}
```

### Use Token for Authenticated Requests

```bash
TOKEN="your-access-token-here"

curl -X GET http://localhost:8000/api/v1/protected-endpoint \
  -H "Authorization: Bearer $TOKEN"
```

## 📈 Monitoring

### Prometheus

1. Open http://localhost:9090
2. Try these queries:
   ```
   # Request rate
   rate(http_requests_total[5m])
   
   # Request duration
   http_request_duration_seconds_bucket
   
   # Active connections
   process_open_fds
   ```

### Grafana

1. Open http://localhost:3000
2. Login with admin/admin
3. Change password when prompted
4. Prometheus datasource is pre-configured
5. Import dashboards from `monitoring/grafana/dashboards/`

## 🗄️ Database Management

### Connect to PostgreSQL

```bash
# Using Docker
docker-compose exec postgres psql -U aquaculture -d aquaculture_db

# Or using psql directly
psql postgresql://aquaculture:aquaculture123@localhost:5432/aquaculture_db
```

### View Tables

```sql
\dt
SELECT * FROM users;
SELECT * FROM fish_species;
```

### Connect to Redis

```bash
# Using Docker
docker-compose exec redis redis-cli

# Commands
PING
KEYS *
GET key_name
```

## 🐛 Troubleshooting

### Services Not Starting

```bash
# View logs
docker-compose logs -f

# View specific service logs
docker-compose logs -f api
docker-compose logs -f postgres

# Restart services
docker-compose restart

# Rebuild and restart
docker-compose up -d --build
```

### Database Connection Issues

```bash
# Check if PostgreSQL is ready
docker-compose exec postgres pg_isready -U aquaculture

# Check database logs
docker-compose logs postgres
```

### Port Already in Use

```bash
# Find process using port
sudo lsof -i :8000
sudo lsof -i :5432

# Kill process
kill -9 <PID>

# Or change port in docker-compose.yml
```

## 🧹 Cleanup

### Stop Services

```bash
# Stop containers (keeps data)
docker-compose stop

# Stop and remove containers (keeps volumes)
docker-compose down

# Remove everything including volumes (⚠️ deletes data!)
docker-compose down -v
```

### Remove Images

```bash
docker-compose down --rmi all
```

## 📚 Next Steps

### Phase 2: Add ML Model Service

1. Create ML model training pipeline
2. Implement model serving with TorchServe
3. Add inference endpoints
4. Implement batch prediction

### Phase 3: Add Frontend

1. Create React + TypeScript dashboard
2. Add real-time updates with WebSockets
3. Implement data visualization

### Phase 4: Deploy to Cloud

1. Set up AWS/GCP account
2. Create Kubernetes cluster
3. Deploy with Terraform
4. Set up CI/CD pipeline

## 🔧 Development

### Install Python Dependencies Locally

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt
```

### Run Tests

```bash
pytest tests/
pytest --cov=services tests/
```

### Code Quality

```bash
# Format code
black services/

# Lint code
flake8 services/

# Type checking
mypy services/
```

## 📖 Documentation

- [Architecture](docs/architecture.md)
- [API Reference](http://localhost:8000/docs)
- [Database Schema](docs/database.md)
- [Deployment Guide](docs/deployment.md)

## 🆘 Getting Help

1. Check logs: `docker-compose logs -f`
2. Check service health: `curl http://localhost:8000/health/detailed`
3. Review documentation in `docs/`
4. Check GitHub issues

## ✅ Verification Checklist

- [ ] All containers running: `docker-compose ps`
- [ ] API responding: `curl http://localhost:8000/health`
- [ ] Database accessible: `docker-compose exec postgres psql -U aquaculture -d aquaculture_db -c "SELECT 1"`
- [ ] Redis accessible: `docker-compose exec redis redis-cli ping`
- [ ] Prometheus accessible: http://localhost:9090
- [ ] Grafana accessible: http://localhost:3000
- [ ] API docs accessible: http://localhost:8000/docs
- [ ] Can register user
- [ ] Can login and get token
- [ ] Can access authenticated endpoints

---

**🎉 Congratulations! You've completed Phase 1!**

Your project now has a solid production-grade foundation. This is already **10x better** than the original amateur project and demonstrates:

- ✅ Docker & containerization skills
- ✅ Database design and management
- ✅ API development with authentication
- ✅ Monitoring and observability
- ✅ Production-ready architecture

**Next**: Continue with Phase 2 to add ML capabilities!
