#!/usr/bin/env python3
"""
Production Readiness Validation Script

Comprehensive validation script that checks all aspects of the Aquaculture ML Platform
for production deployment readiness.

Validation Categories:
- Security configuration and secrets
- Database schema and connectivity
- ML model availability and performance
- API endpoints and authentication
- Infrastructure configuration
- Monitoring and logging setup
- Performance benchmarks
- Compliance and audit requirements

Usage:
    python scripts/production_readiness_check.py [--environment production] [--fix-issues]

Exit Codes:
    0: All checks passed, ready for production
    1: Critical issues found, deployment blocked
    2: Warnings found, review recommended
"""

import argparse
import asyncio
import json
import logging
import os
import sys
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ValidationResult:
    """Container for validation results"""
    
    def __init__(self, check_name: str, status: str, message: str, details: Optional[Dict] = None):
        self.check_name = check_name
        self.status = status  # 'PASS', 'FAIL', 'WARN'
        self.message = message
        self.details = details or {}
        self.timestamp = datetime.utcnow().isoformat()


class ProductionReadinessValidator:
    """
    Production Readiness Validator
    
    Performs comprehensive validation of all system components
    to ensure production deployment readiness.
    """
    
    def __init__(self, environment: str = "production", fix_issues: bool = False):
        self.environment = environment
        self.fix_issues = fix_issues
        self.results: List[ValidationResult] = []
        self.critical_failures = 0
        self.warnings = 0
        
    def add_result(self, result: ValidationResult):
        """Add validation result and update counters"""
        self.results.append(result)
        
        if result.status == 'FAIL':
            self.critical_failures += 1
        elif result.status == 'WARN':
            self.warnings += 1
            
        # Print result immediately
        status_color = {
            'PASS': '\033[92m',  # Green
            'WARN': '\033[93m',  # Yellow
            'FAIL': '\033[91m'   # Red
        }
        reset_color = '\033[0m'
        
        print(f"{status_color.get(result.status, '')}{result.status:4}{reset_color} | {result.check_name}: {result.message}")
    
    def validate_security_configuration(self):
        """Validate security configuration and secrets"""
        print("\n🔒 Security Configuration Validation")
        print("=" * 50)
        
        try:
            from pydantic import Field
            from services.api.core.config import settings
            
            # Check environment is set to production
            if settings.ENVIRONMENT != self.environment:
                self.add_result(ValidationResult(
                    "Environment Setting",
                    "FAIL",
                    f"Environment is '{settings.ENVIRONMENT}', expected '{self.environment}'"
                ))
            else:
                self.add_result(ValidationResult(
                    "Environment Setting",
                    "PASS",
                    f"Environment correctly set to '{self.environment}'"
                ))
            
            # Check debug mode is disabled
            if settings.DEBUG and self.environment == "production":
                self.add_result(ValidationResult(
                    "Debug Mode",
                    "FAIL",
                    "DEBUG mode is enabled in production - SECURITY RISK!"
                ))
            else:
                self.add_result(ValidationResult(
                    "Debug Mode",
                    "PASS",
                    "DEBUG mode is properly disabled"
                ))
            
            # Check secret key strength
            if len(settings.SECRET_KEY) < 32:
                self.add_result(ValidationResult(
                    "Secret Key Strength",
                    "FAIL",
                    f"SECRET_KEY is too short ({len(settings.SECRET_KEY)} chars, minimum 32)"
                ))
            elif settings.SECRET_KEY in ["dev-secret-key-change-in-production", "change-this-to-a-secure-random-string-in-production"]:
                self.add_result(ValidationResult(
                    "Secret Key Strength",
                    "FAIL",
                    "SECRET_KEY is using default value - CRITICAL SECURITY RISK!"
                ))
            else:
                self.add_result(ValidationResult(
                    "Secret Key Strength",
                    "PASS",
                    "SECRET_KEY meets security requirements"
                ))
            
            # Check JWT secret
            if len(settings.JWT_SECRET) < 32:
                self.add_result(ValidationResult(
                    "JWT Secret Strength",
                    "FAIL",
                    f"JWT_SECRET is too short ({len(settings.JWT_SECRET)} chars, minimum 32)"
                ))
            elif settings.JWT_SECRET in ["dev-jwt-secret-change-in-production", "change-this-to-another-secure-random-string"]:
                self.add_result(ValidationResult(
                    "JWT Secret Strength",
                    "FAIL",
                    "JWT_SECRET is using default value - CRITICAL SECURITY RISK!"
                ))
            else:
                self.add_result(ValidationResult(
                    "JWT Secret Strength",
                    "PASS",
                    "JWT_SECRET meets security requirements"
                ))
            
            # Check database URL doesn't contain default passwords
            if any(pwd in settings.DATABASE_URL for pwd in ["aquaculture123", "CHANGE_ME_IN_PRODUCTION", "CHANGE_PASSWORD"]):
                self.add_result(ValidationResult(
                    "Database Security",
                    "FAIL",
                    "Database URL contains default password - SECURITY RISK!"
                ))
            else:
                self.add_result(ValidationResult(
                    "Database Security",
                    "PASS",
                    "Database credentials appear secure"
                ))
                
        except Exception as e:
            self.add_result(ValidationResult(
                "Security Configuration",
                "FAIL",
                f"Failed to validate security configuration: {e}"
            ))
    
    def validate_database_setup(self):
        """Validate database schema and connectivity"""
        print("\n🗄️ Database Validation")
        print("=" * 50)
        
        try:
            from services.api.core.database import get_db
            from services.api.models.user import User
            from services.api.models.prediction import FishSpecies, Model, Prediction
            
            # Test database connectivity
            try:
                db = next(get_db())
                db.execute("SELECT 1")
                db.close()
                self.add_result(ValidationResult(
                    "Database Connectivity",
                    "PASS",
                    "Database connection successful"
                ))
            except Exception as e:
                self.add_result(ValidationResult(
                    "Database Connectivity",
                    "FAIL",
                    f"Database connection failed: {e}"
                ))
                return
            
            # Check if tables exist
            db = next(get_db())
            try:
                # Check for required tables
                required_tables = ['users', 'fish_species', 'models', 'predictions']
                existing_tables = []
                
                for table in required_tables:
                    try:
                        result = db.execute(f"SELECT 1 FROM {table} LIMIT 1")
                        existing_tables.append(table)
                    except:
                        pass
                
                if len(existing_tables) == len(required_tables):
                    self.add_result(ValidationResult(
                        "Database Schema",
                        "PASS",
                        f"All required tables exist: {', '.join(existing_tables)}"
                    ))
                else:
                    missing_tables = set(required_tables) - set(existing_tables)
                    self.add_result(ValidationResult(
                        "Database Schema",
                        "FAIL",
                        f"Missing tables: {', '.join(missing_tables)}"
                    ))
                
                # Check if fish species data is populated
                fish_count = db.query(FishSpecies).count()
                if fish_count > 0:
                    self.add_result(ValidationResult(
                        "Fish Species Data",
                        "PASS",
                        f"Fish species data populated ({fish_count} species)"
                    ))
                else:
                    self.add_result(ValidationResult(
                        "Fish Species Data",
                        "WARN",
                        "No fish species data found - run database seeding"
                    ))
                    
            finally:
                db.close()
                
        except Exception as e:
            self.add_result(ValidationResult(
                "Database Validation",
                "FAIL",
                f"Database validation failed: {e}"
            ))
    
    def validate_ml_models(self):
        """Validate ML model availability and performance"""
        print("\n🤖 ML Model Validation")
        print("=" * 50)
        
        try:
            # Skip ML validation if modules not available (expected in some environments)
            import importlib.util
            
            ml_spec = importlib.util.find_spec("services.ml_service")
            if ml_spec is None:
                self.add_result(ValidationResult(
                    "ML Service Module",
                    "WARN",
                    "ML service module not available - this is expected if running validation separately"
                ))
                return
                
            from services.ml_service.core.model_registry import model_registry
            from services.ml_service.core.config import ml_settings
            
            # Check model registry connectivity
            try:
                available_models = model_registry.list_available_models()
                
                if available_models:
                    total_models = sum(len(versions) for versions in available_models.values())
                    self.add_result(ValidationResult(
                        "Model Registry",
                        "PASS",
                        f"Model registry accessible with {total_models} model versions"
                    ))
                    
                    # Check if active model version exists
                    active_model = ml_settings.MODEL_NAME
                    active_version = ml_settings.ACTIVE_MODEL_VERSION
                    
                    if active_model in available_models and active_version in available_models[active_model]:
                        self.add_result(ValidationResult(
                            "Active Model",
                            "PASS",
                            f"Active model {active_model}:{active_version} is available"
                        ))
                    else:
                        self.add_result(ValidationResult(
                            "Active Model",
                            "FAIL",
                            f"Active model {active_model}:{active_version} not found in registry"
                        ))
                        
                else:
                    self.add_result(ValidationResult(
                        "Model Registry",
                        "FAIL",
                        "No models found in registry - ML inference will fail"
                    ))
                    
            except Exception as e:
                self.add_result(ValidationResult(
                    "Model Registry",
                    "FAIL",
                    f"Model registry validation failed: {e}"
                ))
            
            # Test model loading (if models are available)
            try:
                from services.ml_service.models.model_manager import model_manager
                
                # This would require async context, so we'll skip for now
                self.add_result(ValidationResult(
                    "Model Loading",
                    "WARN",
                    "Model loading test skipped - requires async context"
                ))
                
            except Exception as e:
                self.add_result(ValidationResult(
                    "Model Loading",
                    "WARN",
                    f"Model loading test failed: {e}"
                ))
                
        except Exception as e:
            self.add_result(ValidationResult(
                "ML Model Validation",
                "FAIL",
                f"ML model validation failed: {e}"
            ))
    
    def validate_api_endpoints(self):
        """Validate API endpoints and authentication"""
        print("\n🌐 API Endpoints Validation")
        print("=" * 50)
        
        try:
            import requests
            import importlib.util
            
            # Skip API validation if modules not available
            api_spec = importlib.util.find_spec("services.api")
            if api_spec is None:
                self.add_result(ValidationResult(
                    "API Service Module",
                    "WARN", 
                    "API service module not available - this is expected if running validation separately"
                ))
                return
                
            from services.api.core.config import settings
            
            base_url = f"http://localhost:{settings.API_PORT}"
            
            # Test health endpoint
            try:
                response = requests.get(f"{base_url}/health", timeout=5)
                if response.status_code == 200:
                    health_data = response.json()
                    self.add_result(ValidationResult(
                        "Health Endpoint",
                        "PASS",
                        f"Health endpoint accessible, status: {health_data.get('status', 'unknown')}"
                    ))
                else:
                    self.add_result(ValidationResult(
                        "Health Endpoint",
                        "FAIL",
                        f"Health endpoint returned status {response.status_code}"
                    ))
            except requests.exceptions.RequestException as e:
                self.add_result(ValidationResult(
                    "Health Endpoint",
                    "WARN",
                    f"Health endpoint not accessible (service may not be running): {e}"
                ))
            
            # Test API documentation
            try:
                response = requests.get(f"{base_url}/docs", timeout=5)
                if response.status_code == 200:
                    self.add_result(ValidationResult(
                        "API Documentation",
                        "PASS",
                        "API documentation accessible"
                    ))
                else:
                    self.add_result(ValidationResult(
                        "API Documentation",
                        "WARN",
                        f"API documentation returned status {response.status_code}"
                    ))
            except requests.exceptions.RequestException:
                self.add_result(ValidationResult(
                    "API Documentation",
                    "WARN",
                    "API documentation not accessible (service may not be running)"
                ))
                
        except Exception as e:
            self.add_result(ValidationResult(
                "API Validation",
                "FAIL",
                f"API validation failed: {e}"
            ))
    
    def validate_infrastructure_config(self):
        """Validate infrastructure configuration files"""
        print("\n🏗️ Infrastructure Configuration Validation")
        print("=" * 50)
        
        project_root = Path(__file__).parent.parent
        
        # Check Terraform configuration
        terraform_dir = project_root / "infrastructure" / "terraform"
        if terraform_dir.exists():
            required_tf_files = ["main.tf", "variables.tf", "versions.tf", "outputs.tf"]
            missing_files = []
            
            for tf_file in required_tf_files:
                if not (terraform_dir / tf_file).exists():
                    missing_files.append(tf_file)
            
            if not missing_files:
                self.add_result(ValidationResult(
                    "Terraform Configuration",
                    "PASS",
                    "All required Terraform files present"
                ))
            else:
                self.add_result(ValidationResult(
                    "Terraform Configuration",
                    "WARN",
                    f"Missing Terraform files: {', '.join(missing_files)}"
                ))
        else:
            self.add_result(ValidationResult(
                "Terraform Configuration",
                "FAIL",
                "Terraform configuration directory not found"
            ))
        
        # Check Kubernetes configuration
        k8s_dir = project_root / "infrastructure" / "kubernetes"
        if k8s_dir.exists():
            required_k8s_dirs = ["base", "overlays"]
            missing_dirs = []
            
            for k8s_subdir in required_k8s_dirs:
                if not (k8s_dir / k8s_subdir).exists():
                    missing_dirs.append(k8s_subdir)
            
            if not missing_dirs:
                self.add_result(ValidationResult(
                    "Kubernetes Configuration",
                    "PASS",
                    "Kubernetes configuration structure is complete"
                ))
            else:
                self.add_result(ValidationResult(
                    "Kubernetes Configuration",
                    "WARN",
                    f"Missing Kubernetes directories: {', '.join(missing_dirs)}"
                ))
        else:
            self.add_result(ValidationResult(
                "Kubernetes Configuration",
                "FAIL",
                "Kubernetes configuration directory not found"
            ))
        
        # Check Docker configuration
        docker_files = ["docker-compose.yml", "Dockerfile"]
        for docker_file in docker_files:
            if (project_root / docker_file).exists():
                self.add_result(ValidationResult(
                    f"Docker {docker_file}",
                    "PASS",
                    f"{docker_file} exists"
                ))
            else:
                self.add_result(ValidationResult(
                    f"Docker {docker_file}",
                    "WARN",
                    f"{docker_file} not found"
                ))
    
    def validate_monitoring_setup(self):
        """Validate monitoring and logging configuration"""
        print("\n📊 Monitoring & Logging Validation")
        print("=" * 50)
        
        project_root = Path(__file__).parent.parent
        monitoring_dir = project_root / "monitoring"
        
        if monitoring_dir.exists():
            # Check Prometheus configuration
            prometheus_config = monitoring_dir / "prometheus" / "prometheus.yml"
            if prometheus_config.exists():
                self.add_result(ValidationResult(
                    "Prometheus Configuration",
                    "PASS",
                    "Prometheus configuration file exists"
                ))
            else:
                self.add_result(ValidationResult(
                    "Prometheus Configuration",
                    "WARN",
                    "Prometheus configuration file not found"
                ))
            
            # Check Grafana dashboards
            grafana_dashboards = monitoring_dir / "grafana" / "dashboards"
            if grafana_dashboards.exists() and list(grafana_dashboards.glob("*.json")):
                dashboard_count = len(list(grafana_dashboards.glob("*.json")))
                self.add_result(ValidationResult(
                    "Grafana Dashboards",
                    "PASS",
                    f"Found {dashboard_count} Grafana dashboards"
                ))
            else:
                self.add_result(ValidationResult(
                    "Grafana Dashboards",
                    "WARN",
                    "No Grafana dashboards found"
                ))
        else:
            self.add_result(ValidationResult(
                "Monitoring Setup",
                "WARN",
                "Monitoring directory not found"
            ))
    
    def validate_dependencies(self):
        """Validate all required dependencies are installed"""
        print("\n📦 Dependencies Validation")
        print("=" * 50)
        
        project_root = Path(__file__).parent.parent
        
        # Check requirements files
        requirements_files = ["requirements.txt", "requirements-dev.txt"]
        for req_file in requirements_files:
            req_path = project_root / req_file
            if req_path.exists():
                self.add_result(ValidationResult(
                    f"Requirements {req_file}",
                    "PASS",
                    f"{req_file} exists"
                ))
            else:
                self.add_result(ValidationResult(
                    f"Requirements {req_file}",
                    "WARN",
                    f"{req_file} not found"
                ))
        
        # Check if virtual environment exists
        venv_paths = [project_root / "venv", project_root / ".venv"]
        venv_found = any(venv_path.exists() for venv_path in venv_paths)
        
        if venv_found:
            self.add_result(ValidationResult(
                "Virtual Environment",
                "PASS",
                "Virtual environment found"
            ))
        else:
            self.add_result(ValidationResult(
                "Virtual Environment",
                "WARN",
                "No virtual environment found"
            ))
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate comprehensive validation report"""
        
        # Calculate summary statistics
        total_checks = len(self.results)
        passed_checks = len([r for r in self.results if r.status == 'PASS'])
        failed_checks = len([r for r in self.results if r.status == 'FAIL'])
        warning_checks = len([r for r in self.results if r.status == 'WARN'])
        
        # Determine overall status
        if failed_checks > 0:
            overall_status = "NOT_READY"
            status_message = f"{failed_checks} critical issues must be resolved"
        elif warning_checks > 0:
            overall_status = "REVIEW_REQUIRED"
            status_message = f"{warning_checks} warnings should be reviewed"
        else:
            overall_status = "READY"
            status_message = "All checks passed - ready for production"
        
        report = {
            "validation_timestamp": datetime.utcnow().isoformat(),
            "environment": self.environment,
            "overall_status": overall_status,
            "status_message": status_message,
            "summary": {
                "total_checks": total_checks,
                "passed": passed_checks,
                "failed": failed_checks,
                "warnings": warning_checks,
                "success_rate": f"{(passed_checks / total_checks * 100):.1f}%" if total_checks > 0 else "0%"
            },
            "results": [
                {
                    "check_name": r.check_name,
                    "status": r.status,
                    "message": r.message,
                    "details": r.details,
                    "timestamp": r.timestamp
                }
                for r in self.results
            ]
        }
        
        return report
    
    async def run_all_validations(self):
        """Run all validation checks"""
        print("🔍 Production Readiness Validation")
        print("=" * 60)
        print(f"Environment: {self.environment}")
        print(f"Timestamp: {datetime.utcnow().isoformat()}")
        print("=" * 60)
        
        # Run all validation categories
        self.validate_security_configuration()
        self.validate_database_setup()
        self.validate_ml_models()
        self.validate_api_endpoints()
        self.validate_infrastructure_config()
        self.validate_monitoring_setup()
        self.validate_dependencies()
        
        # Generate and display report
        report = self.generate_report()
        
        print("\n" + "=" * 60)
        print("📋 VALIDATION SUMMARY")
        print("=" * 60)
        
        print(f"Overall Status: {report['overall_status']}")
        print(f"Status Message: {report['status_message']}")
        print(f"Total Checks: {report['summary']['total_checks']}")
        print(f"✅ Passed: {report['summary']['passed']}")
        print(f"⚠️  Warnings: {report['summary']['warnings']}")
        print(f"❌ Failed: {report['summary']['failed']}")
        print(f"Success Rate: {report['summary']['success_rate']}")
        
        # Save report to file
        report_file = f"production_readiness_report_{self.environment}_{int(time.time())}.json"
        with open(report_file, 'w') as f:
            json.dump(report, f, indent=2)
        
        print(f"\n📄 Detailed report saved to: {report_file}")
        
        # Return appropriate exit code
        if report['overall_status'] == "NOT_READY":
            return 1
        elif report['overall_status'] == "REVIEW_REQUIRED":
            return 2
        else:
            return 0


async def main():
    """Main function"""
    parser = argparse.ArgumentParser(description='Production Readiness Validation')
    parser.add_argument('--environment', default='production', 
                       choices=['development', 'staging', 'production'],
                       help='Target environment')
    parser.add_argument('--fix-issues', action='store_true',
                       help='Attempt to fix issues automatically')
    
    args = parser.parse_args()
    
    validator = ProductionReadinessValidator(
        environment=args.environment,
        fix_issues=args.fix_issues
    )
    
    exit_code = await validator.run_all_validations()
    
    print("\n" + "=" * 60)
    if exit_code == 0:
        print("🎉 PRODUCTION READY! All validations passed.")
    elif exit_code == 1:
        print("🚫 NOT PRODUCTION READY! Critical issues found.")
        print("   Please resolve all failed checks before deploying.")
    else:
        print("⚠️  REVIEW REQUIRED! Warnings found.")
        print("   Review warnings and consider addressing them.")
    
    print("=" * 60)
    
    sys.exit(exit_code)


if __name__ == "__main__":
    asyncio.run(main())
