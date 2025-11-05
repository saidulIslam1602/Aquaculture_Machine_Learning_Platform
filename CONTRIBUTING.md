# 🤝 Contributing to Agricultural IoT Platform

Thank you for your interest in contributing to the Agricultural IoT Platform! This document provides guidelines for contributing to this enterprise-grade data engineering project.

## 🎯 Project Overview

This platform demonstrates advanced data engineering capabilities for agricultural IoT applications, featuring:
- Apache Airflow ETL orchestration
- Kafka Streams real-time processing
- PySpark batch analytics with Delta Lake
- Comprehensive data quality management
- Complete data lineage tracking

## 📋 Development Standards

### Code Quality Requirements
- **Python 3.10+** with type hints
- **PEP 8** compliance with Black formatting
- **Comprehensive testing** with pytest (90%+ coverage)
- **Documentation** for all public APIs
- **Security** best practices (no secrets in code)

### Architecture Principles
- **Microservices** architecture with clear boundaries
- **Event-driven** design with proper decoupling
- **Observability** with comprehensive logging and metrics
- **Scalability** designed for production workloads
- **Reliability** with proper error handling and retries

## 🛠️ Development Setup

### Prerequisites
```bash
# Required tools
- Docker & Docker Compose
- Python 3.10+
- Git
- Make (optional)
```

### Local Development
```bash
# 1. Clone the repository
git clone https://github.com/saidulIslam1602/Agricultural-IoT-Platform.git
cd Agricultural-IoT-Platform

# 2. Set up Python environment
python -m venv venv
source venv/bin/activate  # Linux/Mac
# or
venv\Scripts\activate  # Windows

# 3. Install dependencies
pip install -r requirements.txt
pip install -r requirements-dev.txt

# 4. Start local services
docker-compose up -d

# 5. Run tests
pytest tests/ -v --cov=services
```

## 🔄 Contribution Workflow

### 1. Issue Creation
- Check existing issues before creating new ones
- Use issue templates for bugs and feature requests
- Provide detailed descriptions and reproduction steps
- Label issues appropriately (bug, enhancement, documentation)

### 2. Branch Strategy
```bash
# Create feature branch from main
git checkout main
git pull origin main
git checkout -b feature/your-feature-name

# For bug fixes
git checkout -b fix/issue-description

# For documentation
git checkout -b docs/documentation-update
```

### 3. Development Process
- Write tests before implementing features (TDD)
- Follow existing code patterns and conventions
- Update documentation for API changes
- Add appropriate logging and error handling
- Ensure all tests pass locally

### 4. Commit Standards
Use [Conventional Commits](https://www.conventionalcommits.org/):

```bash
# Feature commits
git commit -m "feat: add real-time anomaly detection for livestock"

# Bug fixes
git commit -m "fix: resolve TimescaleDB connection timeout issue"

# Documentation
git commit -m "docs: update API documentation for data quality endpoints"

# Breaking changes
git commit -m "feat!: migrate to Apache Airflow 2.8.0"
```

### 5. Pull Request Process
- Create PR against `main` branch
- Fill out PR template completely
- Ensure CI/CD pipeline passes
- Request review from maintainers
- Address review feedback promptly

## 🧪 Testing Guidelines

### Test Categories
- **Unit Tests**: Individual component testing
- **Integration Tests**: Service interaction testing
- **End-to-End Tests**: Complete workflow testing
- **Performance Tests**: Load and stress testing

### Test Requirements
```bash
# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=services --cov-report=html

# Run specific test categories
pytest tests/unit/ -v
pytest tests/integration/ -v
pytest tests/e2e/ -v
```

### Test Data
- Use factories for test data generation
- Mock external services appropriately
- Clean up test data after tests complete
- Use realistic but anonymized agricultural data

## 📚 Documentation Standards

### Code Documentation
- **Docstrings**: All public functions and classes
- **Type Hints**: All function parameters and returns
- **Comments**: Complex business logic and algorithms
- **README**: Each major component directory

### API Documentation
- **OpenAPI/Swagger** specifications
- **Request/Response** examples
- **Error Codes** and handling
- **Authentication** requirements

## 🔒 Security Guidelines

### Security Requirements
- **No Secrets**: Never commit API keys, passwords, or tokens
- **Input Validation**: Validate all external inputs
- **SQL Injection**: Use parameterized queries only
- **Authentication**: Implement proper auth for all endpoints
- **HTTPS**: All external communications must use TLS

### Security Review Process
- Security review required for authentication changes
- Dependency vulnerability scanning with safety
- Regular security audits for production deployments
- Incident response procedures documented

## 🚀 Performance Guidelines

### Performance Standards
- **API Response**: <100ms for 95th percentile
- **Database Queries**: <50ms for simple queries
- **Batch Processing**: Process 1M+ records efficiently
- **Memory Usage**: Optimize for production constraints

### Monitoring Requirements
- **Metrics**: Expose Prometheus metrics for all services
- **Logging**: Structured JSON logging with correlation IDs
- **Tracing**: Distributed tracing for complex workflows
- **Alerting**: Define SLOs and error budgets

## 🎯 Domain-Specific Guidelines

### Agricultural IoT Considerations
- **Data Privacy**: Respect farmer data privacy requirements
- **Regulatory Compliance**: Consider agricultural regulations
- **Seasonal Patterns**: Account for agricultural cycles
- **Equipment Constraints**: Consider IoT device limitations

### Livestock Monitoring
- **Animal Welfare**: Prioritize animal health and safety
- **Veterinary Standards**: Follow veterinary best practices
- **Species Differences**: Account for different animal behaviors
- **Real-time Alerts**: Critical health alerts must be immediate

## 📞 Getting Help

### Communication Channels
- **Issues**: GitHub Issues for bugs and feature requests
- **Discussions**: GitHub Discussions for questions
- **Email**: Direct contact for security issues
- **Documentation**: Comprehensive docs in `/docs` directory

### Maintainer Response Times
- **Critical Issues**: <24 hours
- **Bug Reports**: <48 hours
- **Feature Requests**: <1 week
- **Pull Reviews**: <3 business days

## 🏆 Recognition

### Contributor Recognition
- Contributors listed in CONTRIBUTORS.md
- Significant contributions highlighted in releases
- Technical blog posts for major features
- Conference presentation opportunities

### Code of Conduct
This project follows the [Contributor Covenant Code of Conduct](CODE_OF_CONDUCT.md). Please read and follow these guidelines to ensure a welcoming environment for all contributors.

---

**Thank you for contributing to the Agricultural IoT Platform!**

This project showcases enterprise-grade data engineering practices and welcomes contributions that maintain these high standards. Your contributions help demonstrate the platform's collaborative development capabilities to potential employers and technical evaluators.

For questions about contributing, please open a GitHub Discussion or contact the maintainers directly.
