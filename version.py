#!/usr/bin/env python3
"""
Version Management for Aquaculture Machine Learning Platform

This module provides centralized version information and build metadata
for the Aquaculture ML Platform. It follows Semantic Versioning (SemVer)
principles and integrates with CI/CD pipelines for automated versioning.

The version information is used by:
- Jenkins CI/CD pipeline for build tagging and deployment
- Docker image labeling and container metadata
- API version headers and documentation
- Kubernetes deployment labels and annotations
- Monitoring and observability systems
- Package management and dependency resolution

Semantic Versioning Format: MAJOR.MINOR.PATCH[-BUILD]
- MAJOR: Breaking changes that require migration
- MINOR: New features that are backward compatible
- PATCH: Bug fixes and security updates
- BUILD: Build metadata and pre-release identifiers

Author: Aquaculture ML Platform Team
License: MIT
Repository: https://github.com/saidulIslam1602/Aquaculture-ML-Platform
"""

__version__ = "2.1.0"
__build__ = "stable"
__author__ = "Agricultural IoT Team"
__email__ = "devops@agricultural-iot.com"
__description__ = "Complete End-to-End Agricultural IoT Data Engineering Platform"

# Version components for semantic versioning
VERSION_MAJOR = 2
VERSION_MINOR = 1
VERSION_PATCH = 0
VERSION_BUILD = "stable"

# Build metadata
BUILD_DATE = "2024-11-05"
PLATFORM_NAME = "Aquaculture ML Platform"
PLATFORM_CODENAME = "Neptune"

# Feature flags for different deployment environments
FEATURES = {
    "airflow_orchestration": True,
    "kafka_streaming": True,
    "spark_processing": True,
    "ml_inference": True,
    "data_quality": True,
    "monitoring": True,
    "frontend_dashboard": True,
    "bigquery_integration": True,
    "dbt_transformations": True,
}

# Environment-specific configurations
ENVIRONMENTS = {
    "development": {
        "debug": True,
        "log_level": "DEBUG",
        "enable_profiling": True,
    },
    "staging": {
        "debug": False,
        "log_level": "INFO",
        "enable_profiling": False,
    },
    "production": {
        "debug": False,
        "log_level": "WARNING",
        "enable_profiling": False,
    }
}

def get_version():
    """Get the full version string."""
    return f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_BUILD}"

def get_build_info():
    """Get comprehensive build information."""
    return {
        "version": __version__,
        "build": __build__,
        "build_date": BUILD_DATE,
        "platform": PLATFORM_NAME,
        "codename": PLATFORM_CODENAME,
        "features": FEATURES,
    }

if __name__ == "__main__":
    print(f"Aquaculture ML Platform v{__version__}")
    print(f"Build: {__build__}")
    print(f"Date: {BUILD_DATE}")
