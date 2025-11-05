# Contributing to Aquaculture Machine Learning Platform

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Workflow](#development-workflow)
- [Code Standards](#code-standards)
- [Testing Guidelines](#testing-guidelines)
- [Documentation Standards](#documentation-standards)
- [Pull Request Process](#pull-request-process)
- [Issue Reporting](#issue-reporting)

## Code of Conduct

This project adheres to professional software development standards. By participating, you are expected to uphold these standards and contribute to a collaborative and respectful environment.

### Expected Behavior

- Use welcoming and inclusive language
- Be respectful of differing viewpoints and experiences
- Gracefully accept constructive criticism
- Focus on what is best for the community and project
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment, discrimination, or inappropriate conduct
- Publishing private information without consent
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Other conduct inappropriate in a professional setting

## Getting Started

### Prerequisites

Before contributing, ensure you have the following installed:

- Python 3.10 or higher
- Docker 20.10+
- Docker Compose 2.0+
- Git 2.30+
- Node.js 18+ (for frontend development)

### Development Environment Setup

1. **Fork and clone the repository:**
```bash
git clone https://github.com/your-username/Aquaculture-ML-Platform.git
cd Aquaculture-ML-Platform
```

2. **Set up Python virtual environment:**
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
pip install -r requirements-dev.txt
```

3. **Install pre-commit hooks:**
```bash
pre-commit install
```

4. **Start development services:**
```bash
docker-compose up -d
```

5. **Run database migrations:**
```bash
python -m alembic upgrade head
```

6. **Verify setup:**
```bash
pytest tests/unit/
```

## Development Workflow

### Branch Strategy

We follow the Git Flow branching model:

- **main**: Production-ready code
- **develop**: Integration branch for features
- **feature/**: Feature development branches
- **hotfix/**: Critical production fixes
- **release/**: Release preparation branches

### Feature Development Process

1. **Create feature branch:**
```bash
git checkout develop
git pull origin develop
git checkout -b feature/your-feature-name
```

2. **Implement changes:**
   - Write code following project standards
   - Add comprehensive tests
   - Update documentation as needed

3. **Commit changes:**
```bash
git add .
git commit -m "feat: add new feature description"
```

4. **Push and create pull request:**
```bash
git push origin feature/your-feature-name
```

### Commit Message Convention

We use Conventional Commits specification:

```
<type>[optional scope]: <description>

[optional body]

[optional footer(s)]
```

**Types:**
- `feat`: New feature
- `fix`: Bug fix
- `docs`: Documentation changes
- `style`: Code style changes (formatting, etc.)
- `refactor`: Code refactoring
- `test`: Adding or updating tests
- `chore`: Maintenance tasks

**Examples:**
```
feat(api): add livestock health monitoring endpoint
fix(database): resolve connection pool timeout issue
docs(readme): update installation instructions
test(integration): add comprehensive API test suite
```

## Code Standards

### Python Code Style

We enforce strict code quality standards:

**Formatting:**
- Use Black for code formatting
- Use isort for import sorting
- Maximum line length: 100 characters
- Use type hints for all function parameters and return values

**Linting:**
- Flake8 for style guide enforcement
- Pylint for code quality analysis
- MyPy for static type checking
- Bandit for security vulnerability scanning

**Example:**
```python
from typing import List, Optional
from datetime import datetime

from pydantic import BaseModel


class LivestockData(BaseModel):
    """
    Data model for livestock monitoring information.
    
    Attributes:
        livestock_id: Unique identifier for the livestock
        timestamp: When the data was recorded
        health_score: Calculated health score (0.0 to 1.0)
        location: GPS coordinates of the livestock
        temperature: Body temperature in Celsius
        activity_level: Activity level indicator
    """
    livestock_id: str
    timestamp: datetime
    health_score: float
    location: Optional[tuple[float, float]] = None
    temperature: Optional[float] = None
    activity_level: Optional[str] = None

    class Config:
        """Pydantic model configuration."""
        json_encoders = {
            datetime: lambda v: v.isoformat()
        }


def calculate_health_score(
    temperature: float,
    activity_level: str,
    historical_data: List[LivestockData]
) -> float:
    """
    Calculate livestock health score based on multiple factors.
    
    Args:
        temperature: Current body temperature in Celsius
        activity_level: Current activity level (low, normal, high)
        historical_data: Historical health data for trend analysis
        
    Returns:
        Health score between 0.0 (poor) and 1.0 (excellent)
        
    Raises:
        ValueError: If temperature is outside valid range
        
    Example:
        >>> score = calculate_health_score(38.5, "normal", [])
        >>> assert 0.0 <= score <= 1.0
    """
    if not 35.0 <= temperature <= 42.0:
        raise ValueError(f"Invalid temperature: {temperature}")
    
    # Implementation details...
    return 0.85
```

### JavaScript/TypeScript Standards

For frontend development:

- Use Prettier for code formatting
- Use ESLint for linting
- Follow React best practices
- Use TypeScript for type safety

### SQL Standards

- Use lowercase for SQL keywords
- Use snake_case for table and column names
- Include appropriate indexes and constraints
- Document complex queries with comments

## Testing Guidelines

### Test Structure

We maintain comprehensive test coverage across multiple levels:

**Unit Tests:**
- Test individual functions and classes
- Mock external dependencies
- Aim for 90%+ code coverage
- Fast execution (< 1 second per test)

**Integration Tests:**
- Test service interactions
- Use test databases and containers
- Validate API endpoints end-to-end
- Test data pipeline components

**Load Tests:**
- Performance testing with Locust
- Scalability validation
- Resource utilization analysis
- SLA compliance verification

### Test Organization

```
tests/
├── unit/                   # Unit tests
│   ├── test_api.py
│   ├── test_models.py
│   └── test_utils.py
├── integration/            # Integration tests
│   ├── test_api_endpoints.py
│   ├── test_database.py
│   └── test_ml_pipeline.py
├── load/                   # Load tests
│   └── locustfile.py
├── smoke/                  # Smoke tests
│   └── test_api_smoke.py
└── conftest.py            # Pytest configuration
```

### Writing Tests

**Example Unit Test:**
```python
import pytest
from unittest.mock import Mock, patch

from services.api.utils.health_analysis import calculate_health_score
from services.api.models.livestock import LivestockData


class TestHealthAnalysis:
    """Test suite for health analysis functionality."""
    
    def test_calculate_health_score_normal_temperature(self):
        """Test health score calculation with normal temperature."""
        # Arrange
        temperature = 38.5
        activity_level = "normal"
        historical_data = []
        
        # Act
        score = calculate_health_score(temperature, activity_level, historical_data)
        
        # Assert
        assert 0.0 <= score <= 1.0
        assert isinstance(score, float)
    
    def test_calculate_health_score_invalid_temperature(self):
        """Test health score calculation with invalid temperature."""
        # Arrange
        temperature = 50.0  # Invalid temperature
        activity_level = "normal"
        historical_data = []
        
        # Act & Assert
        with pytest.raises(ValueError, match="Invalid temperature"):
            calculate_health_score(temperature, activity_level, historical_data)
    
    @patch('services.api.utils.health_analysis.get_baseline_metrics')
    def test_calculate_health_score_with_historical_data(self, mock_baseline):
        """Test health score calculation with historical data."""
        # Arrange
        mock_baseline.return_value = {"avg_temp": 38.0, "std_temp": 0.5}
        temperature = 38.2
        activity_level = "normal"
        historical_data = [
            LivestockData(
                livestock_id="test-001",
                timestamp=datetime.now(),
                health_score=0.8,
                temperature=38.0
            )
        ]
        
        # Act
        score = calculate_health_score(temperature, activity_level, historical_data)
        
        # Assert
        assert score > 0.7  # Should be relatively high
        mock_baseline.assert_called_once()
```

### Running Tests

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=services --cov-report=html

# Run specific test categories
pytest tests/unit/
pytest tests/integration/
pytest tests/load/

# Run tests in parallel
pytest -n auto

# Run tests with verbose output
pytest -v
```

## Documentation Standards

### Code Documentation

**Docstring Format:**
We use Google-style docstrings:

```python
def process_sensor_data(
    sensor_data: Dict[str, Any],
    validation_rules: Optional[List[str]] = None
) -> ProcessedData:
    """
    Process raw sensor data and apply validation rules.
    
    This function takes raw sensor data from IoT devices and processes it
    according to the specified validation rules. It handles data cleaning,
    normalization, and quality checks.
    
    Args:
        sensor_data: Raw sensor data dictionary containing measurements
        validation_rules: Optional list of validation rule names to apply
        
    Returns:
        ProcessedData object containing cleaned and validated sensor data
        
    Raises:
        ValidationError: If sensor data fails validation checks
        DataProcessingError: If data processing encounters an error
        
    Example:
        >>> raw_data = {"temperature": 25.5, "humidity": 60.2}
        >>> processed = process_sensor_data(raw_data, ["temperature_range"])
        >>> assert processed.is_valid
        
    Note:
        This function is designed to handle large volumes of sensor data
        efficiently. For batch processing, consider using the batch
        processing utilities in the spark module.
    """
```

### API Documentation

All API endpoints must include:
- Clear endpoint description
- Parameter documentation
- Response schema documentation
- Example requests and responses
- Error code documentation

### README Updates

When adding new features:
- Update the main README.md
- Add feature-specific documentation
- Update installation instructions if needed
- Include configuration examples

## Pull Request Process

### Before Submitting

1. **Ensure all tests pass:**
```bash
pytest
```

2. **Run code quality checks:**
```bash
black --check .
isort --check-only .
flake8 .
mypy services/
```

3. **Update documentation:**
   - Add/update docstrings
   - Update README if needed
   - Add changelog entry

4. **Verify CI pipeline:**
   - All automated checks pass
   - No security vulnerabilities
   - Code coverage maintained

### Pull Request Template

When creating a pull request, include:

```markdown
## Description
Brief description of changes made.

## Type of Change
- [ ] Bug fix (non-breaking change that fixes an issue)
- [ ] New feature (non-breaking change that adds functionality)
- [ ] Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] Documentation update

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Documentation updated
- [ ] Tests added for new functionality
- [ ] All tests pass
- [ ] No new security vulnerabilities introduced
```

### Review Process

All pull requests require:
- Automated CI/CD pipeline success
- Code review approval from at least one maintainer
- Documentation review for user-facing changes
- Security review for security-related changes

### Merge Requirements

- All conversations resolved
- All required checks passing
- Up-to-date with target branch
- Squash and merge for feature branches
- Merge commit for release branches

## Issue Reporting

### Bug Reports

When reporting bugs, include:

1. **Environment information:**
   - Operating system and version
   - Python version
   - Docker version
   - Relevant package versions

2. **Steps to reproduce:**
   - Detailed step-by-step instructions
   - Sample data or configuration
   - Expected vs. actual behavior

3. **Additional context:**
   - Error messages and stack traces
   - Log files (sanitized of sensitive data)
   - Screenshots if applicable

### Feature Requests

When requesting features:

1. **Problem description:**
   - What problem does this solve?
   - Who would benefit from this feature?
   - Current workarounds being used

2. **Proposed solution:**
   - Detailed description of desired functionality
   - API design considerations
   - Integration points with existing features

3. **Additional context:**
   - Similar features in other projects
   - Implementation considerations
   - Potential breaking changes

### Security Issues

For security vulnerabilities:
- Do NOT create public issues
- Email security concerns to: security@aquaculture-platform.com
- Include detailed reproduction steps
- Allow reasonable time for response before disclosure

## Development Tools

### Recommended IDE Setup

**Visual Studio Code Extensions:**
- Python
- Pylance
- Black Formatter
- isort
- Docker
- Kubernetes
- GitLens

**PyCharm Configuration:**
- Enable Black integration
- Configure isort
- Set up pytest as test runner
- Enable type checking with MyPy

### Debugging

**Local Development:**
```bash
# Debug API service
python -m debugpy --listen 5678 --wait-for-client services/api/main.py

# Debug with Docker
docker-compose -f docker-compose.debug.yml up
```

**Production Debugging:**
- Use structured logging
- Leverage distributed tracing
- Monitor with Prometheus/Grafana
- Analyze logs with centralized logging

## Release Process

### Version Management

We follow Semantic Versioning (SemVer):
- MAJOR.MINOR.PATCH
- MAJOR: Breaking changes
- MINOR: New features (backward compatible)
- PATCH: Bug fixes (backward compatible)

### Release Checklist

1. Update version in `version.py`
2. Update CHANGELOG.md
3. Create release branch
4. Run full test suite
5. Update documentation
6. Create release PR
7. Tag release after merge
8. Deploy to staging
9. Validate staging deployment
10. Deploy to production

## Getting Help

### Resources

- **Documentation:** [docs/](docs/)
- **API Reference:** [API Documentation](http://localhost:8000/docs)
- **Architecture Guide:** [docs/ARCHITECTURE.md](docs/ARCHITECTURE.md)
- **Deployment Guide:** [docs/DEPLOYMENT.md](docs/DEPLOYMENT.md)

### Communication Channels

- **Issues:** GitHub Issues for bug reports and feature requests
- **Discussions:** GitHub Discussions for questions and ideas
- **Email:** maintainers@aquaculture-platform.com for direct contact

### Maintainers

Current project maintainers:
- **Lead Maintainer:** [Your Name] (your.email@domain.com)
- **DevOps Lead:** [DevOps Lead] (devops@domain.com)
- **ML Lead:** [ML Lead] (ml@domain.com)

Thank you for contributing to the Aquaculture Machine Learning Platform!