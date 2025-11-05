# Aquaculture Machine Learning Platform

[![Python](https://img.shields.io/badge/Python-3.10+-blue.svg)](https://www.python.org/)
[![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.8.0-red.svg)](https://airflow.apache.org/)
[![PySpark](https://img.shields.io/badge/PySpark-3.5.0-orange.svg)](https://spark.apache.org/)
[![Kafka](https://img.shields.io/badge/Apache%20Kafka-Streams-black.svg)](https://kafka.apache.org/)
[![TimescaleDB](https://img.shields.io/badge/TimescaleDB-2.13.0-green.svg)](https://www.timescale.com/)
[![dbt](https://img.shields.io/badge/dbt-1.7.4-FF6B35.svg)](https://www.getdbt.com/)
[![BigQuery](https://img.shields.io/badge/BigQuery-Analytics-4285F4.svg)](https://cloud.google.com/bigquery)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)
[![Build Status](https://img.shields.io/badge/Build-Passing-brightgreen.svg)](https://github.com/saidulIslam1602/Aquaculture-ML-Platform/actions)

## Overview

A comprehensive, enterprise-grade end-to-end data engineering platform for aquaculture IoT data processing, livestock monitoring, and precision agriculture analytics. This platform demonstrates the complete modern data engineering stack with ETL orchestration, stream processing, data quality management, machine learning inference, and advanced analytics capabilities.

This project showcases production-ready implementation of data engineering best practices suitable for senior-level positions in agricultural technology, IoT platforms, and data-intensive applications.

## Architecture

### Data Pipeline Components

The platform implements a complete data engineering architecture with the following components:

```
IoT Sensors → Kafka Streams → TimescaleDB → dbt Transform → BigQuery
     ↓             ↓              ↓             ↓             ↓
Anomaly       PySpark        Data Quality   Data Lineage  Dashboards
Detection     Processing     Validation     Tracking      & Reports
     ↓             ↓              ↓             ↓             ↓
Alerting      Delta Lake     Great          Metadata      Grafana
System        Storage        Expectations   Catalog       Monitoring
```

### Technology Stack

**Data Processing & Storage:**
- **Apache Airflow 2.8.0**: ETL orchestration and workflow management
- **Apache Spark 3.5.0**: Large-scale batch processing with Delta Lake
- **Apache Kafka**: Real-time stream processing and event streaming
- **TimescaleDB 2.13.0**: Time-series data storage and analytics
- **PostgreSQL**: Relational data storage with PostGIS extensions

**Data Transformation & Analytics:**
- **dbt 1.7.4**: Data transformation and modeling
- **Google BigQuery**: Analytics data warehouse
- **Great Expectations**: Data quality validation framework
- **Apache Atlas**: Data lineage and catalog management

**Machine Learning & AI:**
- **PyTorch 2.1.1**: Deep learning framework
- **scikit-learn 1.3.2**: Machine learning algorithms
- **OpenCV**: Computer vision processing
- **FastAPI**: ML model serving and inference API

**Infrastructure & DevOps:**
- **Docker**: Containerization and deployment
- **Kubernetes**: Container orchestration and scaling
- **Jenkins**: CI/CD pipeline automation
- **Prometheus/Grafana**: Monitoring and observability
- **Redis**: Caching and session management

## Features

### Core Data Engineering Capabilities

**ETL Orchestration:**
- Comprehensive Apache Airflow DAG management
- Automated data pipeline scheduling and dependency management
- Error handling, retry logic, and failure notifications
- Integration with TimescaleDB, BigQuery, and external APIs
- Data quality gates and validation checkpoints

**Real-Time Stream Processing:**
- Kafka Streams with real-time telemetry processing
- Real-time anomaly detection and alerting
- Windowed aggregations and behavioral pattern analysis
- Stream-to-batch integration with exactly-once semantics
- Multi-threaded processing with fault tolerance

**Large-Scale Batch Processing:**
- PySpark with Delta Lake for ACID transactions
- Advanced agricultural analytics and feature engineering
- ML feature pipeline with automated feature store
- Optimized partitioning and performance tuning
- Integration with data quality validation

**Data Quality Management:**
- Great Expectations framework implementation
- Automated data validation and profiling
- Data quality metrics and reporting
- Integration with pipeline orchestration
- Custom validation rules for agricultural data

**Machine Learning Operations:**
- Production-ready ML model serving
- Real-time inference API with FastAPI
- Model versioning and deployment automation
- A/B testing framework for model evaluation
- Performance monitoring and drift detection

### Production Features

**Scalability & Performance:**
- Horizontal pod autoscaling (HPA) configuration
- Resource optimization and performance tuning
- Connection pooling and caching strategies
- Optimized database queries and indexing
- Load balancing and traffic management

**Security & Compliance:**
- Role-based access control (RBAC)
- Data encryption at rest and in transit
- Secure credential management
- Audit logging and compliance reporting
- Network security policies

**Monitoring & Observability:**
- Comprehensive metrics collection with Prometheus
- Real-time dashboards with Grafana
- Distributed tracing and logging
- Performance monitoring and alerting
- SLA monitoring and reporting

**DevOps & CI/CD:**
- Jenkins pipeline automation
- Multi-environment deployment (staging/production)
- Blue-green deployment strategies
- Automated testing (unit, integration, smoke)
- Infrastructure as Code (IaC) with Terraform

## Quick Start

### Prerequisites

- Docker 20.10+
- Docker Compose 2.0+
- Python 3.10+
- Kubernetes cluster (for production deployment)
- 8GB+ RAM recommended

### Local Development Setup

1. **Clone the repository:**
```bash
git clone https://github.com/saidulIslam1602/Aquaculture-ML-Platform.git
cd Aquaculture-ML-Platform
```

2. **Start core services:**
```bash
docker-compose up -d
```

3. **Initialize the database:**
```bash
docker-compose exec api python -m alembic upgrade head
```

4. **Access the services:**
- API Documentation: http://localhost:8000/docs
- Grafana Dashboard: http://localhost:3000 (admin/admin)
- Prometheus Metrics: http://localhost:9090

### Production Deployment

1. **Deploy to Kubernetes:**
```bash
kubectl apply -f infrastructure/kubernetes/
```

2. **Configure monitoring:**
```bash
kubectl apply -f monitoring/kubernetes/
```

3. **Verify deployment:**
```bash
kubectl get pods -n aquaculture-prod
```

## Development

### Project Structure

```
├── services/                 # Microservices implementation
│   ├── api/                 # FastAPI REST API service
│   ├── ml-service/          # Machine learning inference service
│   └── worker/              # Background task processing
├── airflow/                 # ETL orchestration workflows
│   └── dags/               # Airflow DAG definitions
├── spark/                   # Batch processing jobs
├── streaming/               # Real-time stream processing
├── data_quality/            # Data validation framework
├── data_catalog/            # Metadata and lineage tracking
├── infrastructure/          # Infrastructure as Code
│   ├── docker/             # Container configurations
│   ├── kubernetes/         # K8s deployment manifests
│   └── terraform/          # Cloud infrastructure
├── monitoring/              # Observability configuration
├── tests/                   # Comprehensive test suite
└── docs/                    # Technical documentation
```

### Code Quality Standards

The project maintains high code quality standards with:

- **Code Formatting**: Black, isort for consistent code style
- **Linting**: Flake8, Pylint for code quality checks
- **Type Checking**: MyPy for static type analysis
- **Security**: Bandit, Semgrep for security vulnerability scanning
- **Testing**: pytest with coverage reporting (80%+ coverage required)
- **Documentation**: Comprehensive docstrings and technical documentation

### Testing Strategy

**Unit Testing:**
- Comprehensive test coverage for all modules
- Mock external dependencies
- Fast execution for development feedback

**Integration Testing:**
- End-to-end API testing
- Database integration testing
- Service interaction validation

**Load Testing:**
- Performance testing with Locust
- Scalability validation
- Resource utilization analysis

**Smoke Testing:**
- Production deployment validation
- Health check verification
- Service availability confirmation

## API Documentation

### Core Endpoints

**Health & Monitoring:**
- `GET /health` - Service health status
- `GET /metrics` - Prometheus metrics
- `GET /ready` - Readiness probe

**Data Management:**
- `POST /api/v1/telemetry` - Submit IoT sensor data
- `GET /api/v1/livestock/{id}` - Retrieve livestock information
- `GET /api/v1/analytics/summary` - Analytics dashboard data

**Machine Learning:**
- `POST /api/v1/ml/predict` - ML model inference
- `GET /api/v1/ml/models` - Available model information
- `POST /api/v1/ml/batch-predict` - Batch prediction processing

### Authentication

The API uses JWT-based authentication with role-based access control:

```bash
# Obtain access token
curl -X POST "http://localhost:8000/auth/login" \
  -H "Content-Type: application/json" \
  -d '{"username": "user", "password": "password"}'

# Use token in requests
curl -X GET "http://localhost:8000/api/v1/livestock" \
  -H "Authorization: Bearer <token>"
```

## Configuration

### Environment Variables

**Database Configuration:**
- `DATABASE_URL`: PostgreSQL connection string
- `TIMESCALEDB_URL`: TimescaleDB connection string
- `REDIS_URL`: Redis connection string

**External Services:**
- `KAFKA_BOOTSTRAP_SERVERS`: Kafka cluster endpoints
- `BIGQUERY_PROJECT_ID`: Google Cloud project ID
- `PROMETHEUS_URL`: Prometheus server URL

**Application Settings:**
- `LOG_LEVEL`: Logging level (DEBUG, INFO, WARNING, ERROR)
- `ENVIRONMENT`: Deployment environment (development, staging, production)
- `SECRET_KEY`: Application secret key for JWT signing

### Performance Tuning

**Database Optimization:**
- Connection pooling configuration
- Query optimization and indexing
- Partitioning strategies for time-series data

**Caching Strategy:**
- Redis caching for frequently accessed data
- Application-level caching for ML model results
- CDN configuration for static assets

**Resource Management:**
- CPU and memory limits for containers
- Horizontal pod autoscaling configuration
- Load balancing and traffic distribution

## Monitoring

### Metrics Collection

The platform collects comprehensive metrics including:

**Application Metrics:**
- Request latency and throughput
- Error rates and success rates
- Database query performance
- ML model inference times

**Infrastructure Metrics:**
- CPU and memory utilization
- Network I/O and disk usage
- Container resource consumption
- Kubernetes cluster health

**Business Metrics:**
- Data processing volumes
- ML model accuracy metrics
- User engagement analytics
- System availability SLAs

### Alerting

Automated alerting is configured for:
- Service availability issues
- Performance degradation
- Data quality violations
- Security incidents
- Resource utilization thresholds

## Deployment

The platform supports automated deployment to staging and production environments through GitHub Actions.

### Deployment Modes

- **Simulation Mode**: Default mode when Kubernetes secrets are not configured
- **Real Deployment Mode**: Activated when proper kubeconfig secrets are provided

### Setting Up Real Deployments

To enable actual Kubernetes deployments instead of simulations:

1. Configure your Kubernetes clusters (staging and production)
2. Set up the required GitHub secrets:
   - `KUBE_CONFIG_STAGING`: Base64-encoded kubeconfig for staging
   - `KUBE_CONFIG_PRODUCTION`: Base64-encoded kubeconfig for production
   - `SLACK_WEBHOOK_URL`: Optional Slack notifications

For detailed setup instructions, see [Deployment Secrets Setup Guide](docs/DEPLOYMENT_SECRETS_SETUP.md).

### Deployment Strategy

- **Staging**: Rolling updates triggered on `develop` branch
- **Production**: Blue-Green deployment triggered on `main` branch

## Contributing

Please read [CONTRIBUTING.md](CONTRIBUTING.md) for details on our code of conduct and the process for submitting pull requests.

### Development Workflow

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Commit your changes (`git commit -m 'Add amazing feature'`)
4. Push to the branch (`git push origin feature/amazing-feature`)
5. Open a Pull Request

### Code Review Process

All code changes require:
- Automated CI/CD pipeline success
- Code review approval from maintainers
- Documentation updates for new features
- Test coverage maintenance (80%+ required)

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Support

For support and questions:
- Create an issue in the GitHub repository
- Review the [documentation](docs/)
- Check the [FAQ](docs/FAQ.md)

## Acknowledgments

- Apache Software Foundation for Airflow, Spark, and Kafka
- TimescaleDB team for time-series database capabilities
- dbt Labs for data transformation framework
- Kubernetes community for container orchestration
- Prometheus and Grafana teams for monitoring solutions