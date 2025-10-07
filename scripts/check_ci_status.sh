#!/bin/bash

# CI/CD Pipeline Diagnostic Script
# Checks the status and configuration of GitHub Actions pipeline

set -e

echo "========================================="
echo "CI/CD PIPELINE DIAGNOSTIC TOOL"
echo "========================================="
echo ""

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Check if we're in a git repository
if [ ! -d .git ]; then
    echo -e "${RED}[ERROR]${NC} Not in a git repository"
    exit 1
fi

echo "[INFO] Repository: $(git remote get-url origin 2>/dev/null || echo 'No remote configured')"
echo "[INFO] Current branch: $(git branch --show-current)"
echo "[INFO] Latest commit: $(git log -1 --oneline)"
echo ""

# Check if GitHub Actions workflow exists
echo "========================================="
echo "CHECKING WORKFLOW CONFIGURATION"
echo "========================================="
echo ""

if [ -f .github/workflows/ci.yml ]; then
    echo -e "${GREEN}✓${NC} CI/CD workflow file exists: .github/workflows/ci.yml"
    
    # Check workflow syntax
    echo "[INFO] Checking workflow syntax..."
    
    # Count jobs
    job_count=$(grep -c "^  [a-z-]*:$" .github/workflows/ci.yml || echo "0")
    echo "[INFO] Number of jobs defined: $job_count"
    
    # List jobs
    echo "[INFO] Jobs in pipeline:"
    grep "^  [a-z-]*:" .github/workflows/ci.yml | sed 's/:$//' | sed 's/^/  - /'
    
else
    echo -e "${RED}✗${NC} CI/CD workflow file not found"
    exit 1
fi

echo ""

# Check trigger conditions
echo "========================================="
echo "CHECKING TRIGGER CONDITIONS"
echo "========================================="
echo ""

echo "[INFO] Workflow triggers on:"
grep -A 5 "^on:" .github/workflows/ci.yml | grep -E "push:|pull_request:|workflow_dispatch:" | sed 's/^/  - /'

echo ""

# Check required files for CI/CD
echo "========================================="
echo "CHECKING REQUIRED FILES"
echo "========================================="
echo ""

files_to_check=(
    "requirements.txt"
    "requirements-dev.txt"
    "pytest.ini"
    "docker-compose.yml"
    "infrastructure/docker/Dockerfile.api"
    "infrastructure/docker/Dockerfile.ml"
    "infrastructure/docker/Dockerfile.frontend"
    "tests/unit/test_api.py"
    "tests/conftest.py"
)

for file in "${files_to_check[@]}"; do
    if [ -f "$file" ]; then
        echo -e "${GREEN}✓${NC} $file"
    else
        echo -e "${RED}✗${NC} $file (missing)"
    fi
done

echo ""

# Check Python files
echo "========================================="
echo "CHECKING PYTHON CODE"
echo "========================================="
echo ""

python_files=$(find services -name "*.py" -type f | wc -l)
echo "[INFO] Python files: $python_files"

# Quick syntax check
echo "[INFO] Running syntax check on Python files..."
syntax_errors=0
for file in $(find services -name "*.py" -type f | head -10); do
    if ! python3 -m py_compile "$file" 2>/dev/null; then
        echo -e "${RED}✗${NC} Syntax error in: $file"
        syntax_errors=$((syntax_errors + 1))
    fi
done

if [ $syntax_errors -eq 0 ]; then
    echo -e "${GREEN}✓${NC} No syntax errors found"
else
    echo -e "${RED}✗${NC} Found $syntax_errors syntax errors"
fi

echo ""

# Check Docker Compose
echo "========================================="
echo "CHECKING DOCKER CONFIGURATION"
echo "========================================="
echo ""

if command -v docker &> /dev/null; then
    if docker compose config > /dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} docker-compose.yml is valid"
        
        # Count services
        service_count=$(docker compose config --services | wc -l)
        echo "[INFO] Number of services: $service_count"
        echo "[INFO] Services:"
        docker compose config --services | sed 's/^/  - /'
    else
        echo -e "${RED}✗${NC} docker-compose.yml has errors"
    fi
else
    echo -e "${YELLOW}⚠${NC} Docker not installed, skipping validation"
fi

echo ""

# Check if GitHub Actions has run
echo "========================================="
echo "GITHUB ACTIONS STATUS"
echo "========================================="
echo ""

echo "[INFO] To check GitHub Actions status:"
echo "  1. Visit: https://github.com/$(git remote get-url origin | sed 's/.*github.com[:/]//' | sed 's/.git$//')/actions"
echo "  2. Or run: gh run list (requires GitHub CLI)"
echo ""

# Check for common CI/CD issues
echo "========================================="
echo "COMMON CI/CD ISSUES CHECK"
echo "========================================="
echo ""

issues_found=0

# Check for missing __init__.py
echo "[INFO] Checking for missing __init__.py files..."
missing_init=0
for dir in $(find services -type d ! -path "*/\.*" ! -path "*/node_modules/*" ! -path "*/venv/*"); do
    if [ -n "$(find "$dir" -maxdepth 1 -name "*.py" ! -name "__init__.py" 2>/dev/null)" ]; then
        if [ ! -f "$dir/__init__.py" ]; then
            echo -e "${YELLOW}⚠${NC} Missing __init__.py in: $dir"
            missing_init=$((missing_init + 1))
        fi
    fi
done

if [ $missing_init -eq 0 ]; then
    echo -e "${GREEN}✓${NC} All Python packages have __init__.py"
else
    echo -e "${YELLOW}⚠${NC} Found $missing_init directories missing __init__.py"
    issues_found=$((issues_found + 1))
fi

# Check for large files that might cause issues
echo ""
echo "[INFO] Checking for large files..."
large_files=$(find . -type f -size +50M ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/venv/*" 2>/dev/null | wc -l)
if [ $large_files -gt 0 ]; then
    echo -e "${YELLOW}⚠${NC} Found $large_files files larger than 50MB"
    find . -type f -size +50M ! -path "*/node_modules/*" ! -path "*/.git/*" ! -path "*/venv/*" 2>/dev/null | head -5 | sed 's/^/  - /'
    issues_found=$((issues_found + 1))
else
    echo -e "${GREEN}✓${NC} No large files found"
fi

echo ""

# Summary
echo "========================================="
echo "DIAGNOSTIC SUMMARY"
echo "========================================="
echo ""

if [ $issues_found -eq 0 ]; then
    echo -e "${GREEN}✓ No critical issues found${NC}"
    echo "[INFO] CI/CD pipeline should work correctly"
    echo ""
    echo "If GitHub Actions is not running:"
    echo "  1. Check GitHub Actions is enabled in repository settings"
    echo "  2. Verify you have push access to the repository"
    echo "  3. Check Actions tab: https://github.com/OWNER/REPO/actions"
    echo "  4. Manually trigger: Actions tab → CI/CD Pipeline → Run workflow"
else
    echo -e "${YELLOW}⚠ Found $issues_found potential issues${NC}"
    echo "[INFO] Review warnings above"
fi

echo ""
echo "========================================="
echo "DIAGNOSTIC COMPLETE"
echo "========================================="
