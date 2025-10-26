# 🐟 Aquaculture ML Platform

<!--
============================================================================
PROJECT OVERVIEW AND ARCHITECTURE DOCUMENTATION
============================================================================

The Aquaculture ML Platform is an enterprise-grade, cloud-native machine
learning platform designed for real-time fish species classification and
aquaculture health monitoring at industrial scale.

PROJECT VISION:
To demonstrate production-ready ML engineering practices, infrastructure
design, and DevOps excellence required for senior-level ML/Data Engineering
roles in enterprise environments.

KEY DIFFERENTIATORS:
- Full-stack ML platform with production infrastructure
- Cloud-native architecture with Kubernetes orchestration
- Real-time streaming data processing capabilities
- Comprehensive observability and monitoring stack
- Enterprise security and compliance features
- Scalable microservices architecture

TECHNOLOGY SHOWCASE:
- Modern Python ecosystem (FastAPI, SQLAlchemy, Celery)
- React TypeScript frontend with Material-UI
- Container orchestration with Docker and Kubernetes
- **Enterprise Terraform Infrastructure**: Multi-environment AWS infrastructure with EKS, RDS, ElastiCache, MSK, S3, ECR, enterprise databases, GPU nodes, and advanced security
- **Sophisticated Jenkins CI/CD with Kubernetes integration**
- CI/CD automation with GitHub Actions
- Monitoring with Prometheus and Grafana
- Security scanning with Trivy vulnerability detection
============================================================================
-->

A **production-grade, cloud-native machine learning platform** for real-time fish classification and health monitoring in aquaculture environments, featuring sophisticated Jenkins CI/CD with Kubernetes integration, comprehensive security scanning, and enterprise-level ML engineering practices.

## 🎯 Project Focus: Enterprise ML Engineering & Cloud Infrastructure

This platform demonstrates **world-class data engineering and ML infrastructure practices** required for **Senior ML/Data Engineer** roles at scale, featuring production-ready architecture patterns used by leading technology companies.

### What's Implemented (Production-Ready) ✅

**Infrastructure & Orchestration:**
- Kubernetes with HPA, network policies, and service mesh ready
- Docker multi-stage builds with security best practices
- **Sophisticated Terraform Infrastructure**: Enterprise-grade AWS infrastructure with multi-database support, GPU nodes, enterprise security, and compliance features
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
- **Jenkins CI/CD with Kubernetes integration (v1.1.0)** - Sophisticated pipeline with dynamic agents
- GitHub Actions CI/CD with multi-stage pipeline
- Automated testing (unit, integration, load)
- Security scanning with Trivy vulnerability detection
- Container security scanning and compliance
- Blue-green deployment support
- Database migrations with Alembic
- Multi-environment deployment (staging/production)

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
- **CI/CD**: Jenkins Kubernetes pipeline with security scanning, multi-environment deployment

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

## 🚀 Jenkins CI/CD Pipeline

### Sophisticated Kubernetes Integration

The platform features a **production-grade Jenkins CI/CD pipeline** with advanced Kubernetes integration:

#### Pipeline Features
- **Dynamic Kubernetes Agents**: Jenkins agents run as pods in Kubernetes cluster
- **Multi-Container Build Environment**: Docker-in-Docker, Python, kubectl, Trivy security scanner
- **Comprehensive Security Scanning**: Container vulnerability detection with Trivy
- **Multi-Environment Deployment**: Staging and production with approval gates
- **Code Quality Pipeline**: Black, Flake8, Pylint, MyPy analysis
- **Docker Image Management**: Automated building, scanning, and registry pushing
- **GitHub Integration**: Automatic builds on code commits

#### Pipeline Stages
1. **Code Quality**: Linting, formatting, type checking
2. **Security Scanning**: Vulnerability detection and compliance
3. **Docker Build**: Multi-stage container builds
4. **Container Security**: Trivy vulnerability scanning
5. **Registry Push**: Automated image publishing
6. **Staging Deployment**: Automated staging environment deployment
7. **Production Deployment**: Manual approval-gated production deployment

#### Jenkins Configuration
- **Pipeline Job**: `aquaculture-pipeline`
- **Kubernetes Cloud**: Dynamic agent provisioning
- **Credentials Management**: Docker registry, Kubernetes tokens, kubeconfig
- **RBAC Integration**: Kubernetes service account with proper permissions
- **Monitoring**: Complete build tracking and reporting

### Jenkins Setup Documentation
- [Jenkins Setup Guide](jenkins/JENKINS_SETUP_COMPLETE.md)
- [RBAC Configuration](jenkins/jenkins-rbac.yaml)
- [Pipeline Definition](jenkins/Jenkinsfile)

## 🏗️ Enterprise Terraform Infrastructure

### Sophisticated AWS Infrastructure

The platform features **enterprise-grade Terraform infrastructure** designed for production-scale ML workloads:

#### Core Infrastructure
- **VPC Architecture**: Multi-AZ Virtual Private Cloud with public/private/database subnets
- **EKS Cluster**: Managed Kubernetes with auto-scaling node groups and GPU support
- **Database Layer**: PostgreSQL RDS with Multi-AZ, encryption, and Performance Insights
- **Caching Layer**: ElastiCache Redis cluster with automatic failover
- **Messaging**: MSK Kafka cluster with TLS encryption and CloudWatch logging
- **Storage**: S3 buckets with versioning, KMS encryption, and lifecycle policies
- **Container Registry**: ECR repositories for all microservices
- **Load Balancing**: Application Load Balancer with SSL termination

#### Enterprise Database Support
- **PostgreSQL**: Primary database with Multi-AZ and encryption
- **SQL Server**: Enterprise database support with RDS
- **Oracle**: Enterprise Oracle database support
- **Multi-Database Architecture**: Support for hybrid database environments

#### GPU and ML Infrastructure
- **GPU Node Groups**: Dedicated GPU nodes for ML inference workloads
- **NVIDIA T4 Support**: Optimized for ML model serving
- **Auto-scaling**: GPU nodes scale based on ML workload demand
- **Resource Isolation**: GPU workloads isolated from general compute

#### Advanced Security Features
- **KMS Encryption**: Dedicated encryption keys for Kafka, RDS, S3
- **Network Security**: Comprehensive security groups and VPC Flow Logs
- **Enterprise Security**: WAF, GuardDuty, Secrets Manager integration
- **Compliance**: CloudTrail, Config, audit logging capabilities
- **Authentication**: LDAP, SAML, enterprise authentication support

#### Environment Management
- **Development**: Cost-optimized single-AZ deployment
- **Staging**: Balanced performance and cost with Multi-AZ
- **Production**: High availability with enterprise features enabled
- **Environment-Specific Sizing**: Automatic resource sizing per environment

#### Monitoring and Observability
- **CloudWatch Integration**: Comprehensive logging and monitoring
- **X-Ray Tracing**: Distributed tracing for microservices
- **Custom Dashboards**: Environment-specific monitoring dashboards
- **Alerting**: Automated alerting for infrastructure health

### Infrastructure Documentation
- [Terraform Infrastructure Guide](infrastructure/terraform/README.md)
- [Configuration Examples](infrastructure/terraform/terraform.tfvars.example)
- [Enterprise Features Guide](docs/TERRAFORM_COMPLETE_GUIDE.md)
- [Environment Configuration](infrastructure/terraform/locals.tf)

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

### Terraform (Enterprise Infrastructure)

The platform features **sophisticated Terraform infrastructure** with enterprise-grade capabilities:

#### Infrastructure Components
- **VPC**: Multi-AZ Virtual Private Cloud with public/private/database subnets
- **EKS**: Managed Kubernetes cluster with GPU nodes for ML inference
- **RDS**: PostgreSQL with Multi-AZ, encryption, Performance Insights
- **ElastiCache**: Redis cluster with automatic failover
- **MSK**: Managed Kafka with TLS encryption
- **S3**: Multiple buckets with versioning and KMS encryption
- **ECR**: Container registries for all services
- **ALB**: Application Load Balancer with SSL termination

#### Enterprise Features
- **Multi-Database Support**: PostgreSQL, SQL Server, Oracle
- **GPU Nodes**: Dedicated GPU nodes for ML inference workloads
- **Enterprise Security**: WAF, GuardDuty, Secrets Manager, LDAP/SAML
- **Compliance**: CloudTrail, Config, audit logging
- **Advanced Monitoring**: CloudWatch, X-Ray, custom dashboards

#### Environment Support
- **Development**: Cost-optimized with single AZ
- **Staging**: Balanced performance and cost
- **Production**: High availability with Multi-AZ and enterprise features

#### Quick Start
```bash
cd infrastructure/terraform
cp terraform.tfvars.example terraform.tfvars
# Edit terraform.tfvars with your configuration
terraform init
terraform plan
terraform apply
```

#### Advanced Configuration
```bash
# Environment-specific deployment
terraform apply -var="environment=production"

# Enable enterprise features
terraform apply -var="enable_enterprise_databases=true" -var="enable_enterprise_security=true"

# Custom instance sizing
terraform apply -var-file="production.tfvars"
```

#### Documentation
- [Terraform Infrastructure Guide](infrastructure/terraform/README.md)
- [Configuration Examples](infrastructure/terraform/terraform.tfvars.example)
- [Enterprise Features Documentation](docs/TERRAFORM_COMPLETE_GUIDE.md)

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

**Status**: ✅ Production Ready | **Version**: 1.1.0 "Poseidon" | **Last Updated**: October 2024
