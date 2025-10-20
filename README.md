# 🐟 Aquaculture ML Platform

A production-grade machine learning platform for real-time fish classification and health monitoring in aquaculture environments.

## 🎯 Project Focus: Data Engineering & Infrastructure

This project demonstrates **production-grade data engineering and platform infrastructure** for ML deployment at scale - the core skills required for a Senior ML/Data Engineer role.

### What's Implemented (Production-Ready) ✅

**Infrastructure & Orchestration:**
- Kubernetes with HPA, network policies, and service mesh ready
- Docker multi-stage builds with security best practices
- Terraform infrastructure as code for AWS (EKS, RDS, MSK, S3)
- NGINX ingress with TLS termination and rate limiting

**Data Engineering:**
- Real-time streaming with Kafka and consumer groups
- Distributed task processing with Celery workers
- PostgreSQL with optimized schema, indexes, and migrations
- Redis for caching and distributed rate limiting
- Data pipeline architecture ready for ETL workflows

**API & Security:**
- FastAPI with JWT authentication and RBAC
- Request validation with Pydantic
- Rate limiting with token bucket algorithm
- Comprehensive error handling and logging
- API versioning and OpenAPI documentation

**Observability & Monitoring:**
- Prometheus for metrics collection
- Grafana dashboards for visualization
- Real-time performance tracking (p50, p95, p99)
- Structured JSON logging
- Health checks and alerting rules

**DevOps & Automation:**
- GitHub Actions CI/CD with multi-stage pipeline
- Automated testing (unit, integration, load)
- Security scanning with Trivy
- Blue-green deployment support
- Database migrations with Alembic

**Frontend:**
- React 18 + TypeScript 5 dashboard
- Material-UI for professional design
- Real-time metrics visualization
- Responsive and accessible UI

### ML Integration Points (Architecture Ready) 🔧

The following components are structured and ready for ML model deployment:
- ML inference endpoints defined with proper request/response schemas
- Model manager with versioning, caching, and health monitoring
- Inference engine with batching and optimization support
- Integration points marked with TODOs for clarity

**This showcases data engineering and platform capabilities required for deploying ML at scale in production environments.**

---

## 🎯 Features

- **Real-time Fish Classification**: Process underwater camera feeds with low latency
- **Scalable Architecture**: Kubernetes-based microservices that scale horizontally
- **Production-Ready API**: FastAPI with JWT authentication, rate limiting, and monitoring
- **Data Pipeline**: Apache Kafka for streaming, PostgreSQL for storage
- **ML Operations**: Model versioning, A/B testing, performance monitoring
- **Observability**: Prometheus metrics, Grafana dashboards, distributed tracing
- **CI/CD**: Automated testing, building, and deployment

## 🏗️ Architecture

```
┌─────────────────────────────────────────────────────────────┐
│                     Load Balancer / Ingress                  │
└────────────────────┬────────────────────────────────────────┘
                     │
        ┌────────────┼────────────┐
        │            │            │
   ┌────▼───┐   ┌───▼────┐   ┌──▼─────┐
   │  API   │   │   ML   │   │ Worker │
   │Service │   │Service │   │Service │
   └────┬───┘   └───┬────┘   └──┬─────┘
        │           │            │
        └───────────┼────────────┘
                    │
        ┌───────────┼───────────┐
        │           │           │
   ┌────▼────┐ ┌───▼────┐ ┌───▼────┐
   │PostgreSQL│ │ Redis  │ │ Kafka  │
   └─────────┘ └────────┘ └────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+
- (Optional) Kubernetes cluster for production

### Local Development

1. **Clone and setup**:
```bash
git clone <your-repo>
cd aquaculture-ml-platform
cp .env.example .env
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Check service health**:
```bash
curl http://localhost:8000/health
```

4. **Access services**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090

### Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# Run tests
pytest tests/

# Run linting
black .
flake8 .
mypy .
```

## 📦 Services

### API Service
- **Port**: 8000
- **Tech**: FastAPI, Pydantic, JWT
- **Features**: Authentication, rate limiting, API versioning

### ML Service
- **Port**: 8001
- **Tech**: PyTorch, TorchServe
- **Features**: Model serving, batch inference, A/B testing

### Worker Service
- **Tech**: Celery, Kafka
- **Features**: Async task processing, stream processing

### Data Pipeline
- **Tech**: Apache Kafka, PostgreSQL
- **Features**: Real-time data ingestion, ETL

## 🗄️ Database Schema

### PostgreSQL Tables
- `users`: User accounts and authentication
- `fish_species`: Fish species metadata
- `predictions`: Model predictions and results
- `models`: ML model versions and metadata
- `audit_logs`: System audit trail

### Redis Keys
- `cache:*`: Cached API responses
- `ratelimit:*`: Rate limiting counters
- `session:*`: User sessions

## 🔧 Configuration

Configuration is managed through environment variables and config files:

- `.env`: Local development settings
- `config/production.yaml`: Production configuration
- `config/staging.yaml`: Staging configuration

Key environment variables:
```bash
# Database
DATABASE_URL=postgresql://user:pass@localhost:5432/aquaculture
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
JWT_SECRET=your-jwt-secret-here

# ML
MODEL_PATH=/models/fish_classifier_v1.pth
BATCH_SIZE=32

# Monitoring
PROMETHEUS_ENABLED=true
LOG_LEVEL=INFO
```

## 🧪 Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test suite
pytest tests/unit/
pytest tests/integration/

# Run load tests
locust -f tests/load/locustfile.py
```

## 📊 Monitoring

### Metrics
- Request latency (p50, p95, p99)
- Throughput (requests/second)
- Error rates
- Model inference time
- Database query performance

### Dashboards
- System Overview: `monitoring/grafana/dashboards/overview.json`
- API Performance: `monitoring/grafana/dashboards/api.json`
- ML Metrics: `monitoring/grafana/dashboards/ml.json`

### Alerts
- High error rate (>5%)
- High latency (p95 > 500ms)
- Low throughput (<100 req/s)
- Model performance degradation

## 🚢 Deployment

### Docker Compose (Development)
```bash
docker-compose up -d
```

### Kubernetes (Production)
```bash
# Apply configurations
kubectl apply -f infrastructure/kubernetes/

# Check deployment
kubectl get pods -n aquaculture

# View logs
kubectl logs -f deployment/api-service -n aquaculture
```

### Terraform (Infrastructure)
```bash
cd infrastructure/terraform
terraform init
terraform plan
terraform apply
```

### GitHub Actions Secrets

The CI/CD pipeline requires the following secrets to be configured in your GitHub repository:

#### Required Secrets
- `SLACK_WEBHOOK_URL`: Slack webhook URL for CI/CD notifications
- `KUBE_CONFIG_PRODUCTION`: Kubernetes config for production deployment
- `KUBE_CONFIG_STAGING`: Kubernetes config for staging deployment

#### Optional Secrets
- `DOCKER_REGISTRY_TOKEN`: Token for private Docker registry (if using)
- `SONAR_TOKEN`: SonarCloud token for code quality analysis (if enabled)

#### Setting up Secrets
1. Go to your GitHub repository
2. Navigate to Settings → Secrets and variables → Actions
3. Click "New repository secret"
4. Add each required secret with its corresponding value

**Example Slack Webhook Setup:**
1. Create a Slack app at https://api.slack.com/apps
2. Add incoming webhook integration
3. Copy the webhook URL
4. Add it as `SLACK_WEBHOOK_URL` secret in GitHub

## 🔐 Security

- JWT-based authentication
- API key management
- Rate limiting (100 req/min per user)
- Input validation with Pydantic
- SQL injection protection (SQLAlchemy ORM)
- CORS configuration
- TLS/SSL in production
- Secret management with environment variables

## 📈 Performance

### Real-time Metrics

Access actual performance metrics at: `GET /api/v1/metrics/performance`

The application tracks and reports:
- **Latency Percentiles**: p50, p95, p99 (measured in real-time)
- **Throughput**: Requests per second (sliding window)
- **Error Rate**: Percentage of failed requests
- **Uptime**: Application uptime in seconds

Example response:
```json
{
  "latency_mean_ms": 45.2,
  "latency_p50_ms": 38.5,
  "latency_p95_ms": 89.3,
  "latency_p99_ms": 145.7,
  "throughput_rps": 234.5,
  "error_rate": 0.0012,
  "total_requests": 15420,
  "uptime_seconds": 86400
}
```

### Expected Performance (Production)

Based on architecture and implementation:
- **API latency**: 30-80ms (p95) - FastAPI + async I/O
- **Inference time**: 50-150ms per image - PyTorch with GPU
- **Throughput**: 500-2000 req/s - With horizontal scaling
- **Database queries**: 5-20ms (p95) - Connection pooling + indexes

Actual performance depends on:
- Hardware (CPU/GPU specs)
- Network latency
- Database load
- Model complexity
- Concurrent users

### Optimization Features
- Redis caching for frequent queries (sub-millisecond)
- Database connection pooling (20 connections)
- Async I/O with FastAPI (non-blocking)
- Model optimization ready (quantization, pruning)
- Batch processing for high throughput (32 images/batch)
- Horizontal pod autoscaling (3-20 replicas)

## 🛠️ Development

### Code Style
- Black for formatting
- Flake8 for linting
- mypy for type checking
- isort for import sorting

### Git Workflow
1. Create feature branch: `git checkout -b feature/your-feature`
2. Make changes and commit: `git commit -m "feat: add feature"`
3. Push and create PR: `git push origin feature/your-feature`
4. Wait for CI/CD checks to pass
5. Request review and merge

### Commit Convention
- `feat:` New feature
- `fix:` Bug fix
- `docs:` Documentation
- `test:` Tests
- `refactor:` Code refactoring
- `perf:` Performance improvement
- `chore:` Maintenance

## 📚 Documentation

- [Getting Started](docs/GETTING_STARTED.md) - Quick start guide
- [Setup Guide](docs/SETUP.md) - Detailed setup instructions
- [Phase 1 Complete](docs/PHASE1_COMPLETE.md) - What's included and achievements
- [API Reference](http://localhost:8000/docs) - Interactive API documentation
- [Architecture](docs/architecture.md) - System architecture (coming soon)
- [Database Schema](docs/database.md) - Database design (coming soon)

## 🤝 Contributing

1. Fork the repository
2. Create your feature branch
3. Commit your changes
4. Push to the branch
5. Create a Pull Request

## 📄 License

MIT License - see LICENSE file for details

## 👥 Team

Built for sustainable aquaculture and precision fish farming.

## 🔗 Links

- [Documentation](docs/)
- [Issue Tracker](issues/)
- [Changelog](CHANGELOG.md)

---

**Status**: 🚧 In Development | **Version**: 0.1.0 | **Last Updated**: October 2025
