"""
Basic test suite for Agricultural IoT Platform

This module provides basic tests to ensure the CI/CD pipeline
can run successfully and validate core functionality.
"""

import pytest
import sys
import os

# Add the project root to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))


class TestBasicFunctionality:
    """Basic functionality tests for the platform."""
    
    def test_python_version(self):
        """Test that Python version is compatible."""
        assert sys.version_info >= (3, 9), "Python 3.9+ is required"
    
    def test_import_basic_modules(self):
        """Test that basic Python modules can be imported."""
        import json
        import datetime
        import logging
        
        assert json is not None
        assert datetime is not None
        assert logging is not None
    
    def test_project_structure(self):
        """Test that basic project structure exists."""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        
        # Check for key directories
        assert os.path.exists(os.path.join(project_root, 'services'))
        assert os.path.exists(os.path.join(project_root, 'requirements.txt'))
        assert os.path.exists(os.path.join(project_root, 'README.md'))
    
    def test_requirements_file_exists(self):
        """Test that requirements.txt exists and is readable."""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        requirements_path = os.path.join(project_root, 'requirements.txt')
        
        assert os.path.exists(requirements_path)
        
        with open(requirements_path, 'r') as f:
            content = f.read()
            assert len(content) > 0
            assert 'fastapi' in content.lower()


class TestDataEngineeringComponents:
    """Test data engineering component imports."""
    
    def test_can_import_pandas(self):
        """Test pandas import for data processing."""
        try:
            import pandas as pd
            assert pd is not None
        except ImportError:
            pytest.skip("Pandas not available in test environment")
    
    def test_can_import_sqlalchemy(self):
        """Test SQLAlchemy import for database operations."""
        try:
            import sqlalchemy
            assert sqlalchemy is not None
        except ImportError:
            pytest.skip("SQLAlchemy not available in test environment")
    
    def test_can_import_fastapi(self):
        """Test FastAPI import for web framework."""
        try:
            import fastapi
            assert fastapi is not None
        except ImportError:
            pytest.skip("FastAPI not available in test environment")


class TestConfigurationFiles:
    """Test configuration and setup files."""
    
    def test_docker_compose_exists(self):
        """Test that docker-compose.yml exists."""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        docker_compose_path = os.path.join(project_root, 'docker-compose.yml')
        
        assert os.path.exists(docker_compose_path)
    
    def test_readme_exists_and_has_content(self):
        """Test that README.md exists and has meaningful content."""
        project_root = os.path.join(os.path.dirname(__file__), '..', '..')
        readme_path = os.path.join(project_root, 'README.md')
        
        assert os.path.exists(readme_path)
        
        with open(readme_path, 'r') as f:
            content = f.read()
            assert len(content) > 100  # Should have substantial content
            assert 'Agricultural IoT' in content


if __name__ == '__main__':
    pytest.main([__file__])
