# 🌾 Agricultural IoT Platform - Complete End-to-End Data Engineering Solution

A comprehensive, enterprise-grade **end-to-end data engineering platform** for agricultural IoT data processing, livestock monitoring, and precision agriculture analytics. This platform showcases the complete modern data engineering stack with ETL orchestration, stream processing, data quality management, and advanced analytics.

## 🎯 Project Focus: Complete Data Platform Engineering

This project demonstrates **enterprise-level end-to-end data engineering** for agricultural IoT deployment at scale, featuring:

- **ETL Orchestration**: Apache Airflow with comprehensive workflow management
- **Stream Processing**: Real-time Kafka Streams with anomaly detection
- **Batch Processing**: PySpark with Delta Lake for large-scale analytics
- **Data Quality**: Great Expectations framework with automated validation
- **Data Lineage**: Complete tracking and catalog management
- **Modern Data Stack**: TimescaleDB → dbt → BigQuery pipeline
- **Monitoring**: Comprehensive observability with Prometheus/Grafana

## 🏗️ Complete Data Engineering Architecture

### **End-to-End Data Pipeline Components**

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   IoT Sensors   │───▶│  Kafka Streams   │───▶│   TimescaleDB   │───▶│   dbt Transform  │
│  (Real-time)    │    │ (Stream Process) │    │  (Time-series)  │    │   (Modeling)     │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
                                │                        │                        │
                                ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Anomaly       │    │   PySpark Batch  │    │  Data Quality   │    │    BigQuery      │
│  Detection      │    │   Processing     │    │ (Great Expect.) │    │  (Analytics DW)  │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
         │                        │                        │                        │
         ▼                        ▼                        ▼                        ▼
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐    ┌──────────────────┐
│   Alerting      │    │   Delta Lake     │    │  Data Lineage   │    │   Dashboards     │
│   System        │    │  (Data Lake)     │    │   Tracking      │    │   & Reports      │
└─────────────────┘    └──────────────────┘    └─────────────────┘    └──────────────────┘
```

**🔄 Orchestrated by Apache Airflow** | **📊 Monitored by Prometheus/Grafana** | **🔍 Tracked by Data Catalog**

### What's Implemented (Production-Ready) ✅

**🚀 ETL Orchestration & Workflow Management:**
- Apache Airflow with comprehensive DAG management
- Automated data pipeline scheduling and dependency management
- Error handling, retry logic, and failure notifications
- Integration with TimescaleDB, BigQuery, and external APIs
- Data quality gates and validation checkpoints

**⚡ Real-Time Stream Processing:**
- Kafka Streams with real-time telemetry processing
- Real-time anomaly detection and alerting
- Windowed aggregations and behavioral pattern analysis
- Stream-to-batch integration with exactly-once semantics
- Multi-threaded processing with fault tolerance

**🔥 Large-Scale Batch Processing:**
- PySpark with Delta Lake for ACID transactions
- Advanced agricultural analytics and feature engineering
- ML feature pipeline with automated feature store
- Optimized partitioning and performance tuning
- Integration with data quality validation

**✅ Data Quality & Validation Framework:**
- Great Expectations with custom agricultural expectations
- Automated data profiling and quality scoring
- Business rule validation and statistical anomaly detection
- Data quality reporting and alerting integration
- Schema evolution and drift monitoring

**🔍 Data Lineage & Catalog Management:**
- Comprehensive data lineage tracking across all pipelines
- Automated metadata discovery and catalog management
- Impact analysis and dependency tracking
- Schema change detection and compatibility analysis
- Integration with Apache Atlas (ready)

**Infrastructure & Orchestration:**
- Kubernetes with HPA, network policies, and service mesh ready
- Docker multi-stage builds with security best practices
- Terraform infrastructure as code for AWS (EKS, RDS, MSK, S3)
- NGINX ingress with TLS termination and rate limiting

**Modern Data Stack & Time-Series:**
- TimescaleDB for high-performance time-series data storage
- dbt for data transformation and modeling (staging, marts, tests)
- BigQuery integration for analytics and reporting
- Real-time streaming with Kafka and consumer groups
- Distributed task processing with Celery workers
- Redis for caching and distributed rate limiting
- Automated data quality checks and monitoring

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

### Agricultural IoT Monitoring
- **Livestock Management**: Real-time animal tracking with collar sensors
- **Virtual Fencing**: Automated boundary monitoring and violation alerts
- **Health Analytics**: AI-powered animal health scoring and anomaly detection
- **Aquaculture Monitoring**: Fish classification and tank environment monitoring

### Modern Data Platform
- **Time-Series Processing**: TimescaleDB with automated compression and retention
- **Data Transformation**: dbt models for staging, marts, and business logic
- **Analytics Warehouse**: BigQuery integration for advanced analytics
- **Real-Time Streaming**: Kafka-based event processing and data pipelines

### Production Infrastructure
- **Scalable Architecture**: Kubernetes-based microservices that scale horizontally
- **Production-Ready API**: FastAPI with JWT authentication, rate limiting, and monitoring
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
   ┌────▼─────┐ ┌──▼────┐ ┌───▼────┐
   │TimescaleDB│ │ Redis │ │ Kafka  │
   │(Time-Series│ │(Cache)│ │(Stream)│
   │ + PostGIS) │ └───────┘ └────────┘
   └────┬──────┘
        │
   ┌────▼─────┐     ┌──────────┐
   │   dbt    │────▶│ BigQuery │
   │(Transform)│     │(Analytics)│
   └──────────┘     └──────────┘
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
cd agricultural-iot-platform
cp .env.example .env
```

2. **Start all services**:
```bash
docker-compose up -d
```

3. **Initialize TimescaleDB and run dbt models**:
```bash
# Wait for TimescaleDB to be ready
docker-compose exec timescaledb psql -U agricultural_iot -d agricultural_iot_db -c "SELECT version();"

# Run dbt models
cd dbt
dbt run --profiles-dir .
dbt test --profiles-dir .
```

4. **Check service health**:
```bash
curl http://localhost:8000/health
curl http://localhost:8000/api/v1/livestock/animals?farm_id=DEMO-FARM
```

5. **Access services**:
- API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- Grafana: http://localhost:3000 (admin/admin)
- Prometheus: http://localhost:9090
- TimescaleDB: localhost:5432 (agricultural_iot/agricultural_iot123)

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
