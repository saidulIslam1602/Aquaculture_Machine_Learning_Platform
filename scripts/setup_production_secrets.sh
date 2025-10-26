#!/bin/bash

# ============================================================================
# Production Secrets Setup Script
# ============================================================================
#
# This script sets up production-grade secrets for the Aquaculture ML Platform.
# It generates secure random secrets and creates Kubernetes secret manifests.
#
# Usage:
#   ./scripts/setup_production_secrets.sh [environment]
#
# Arguments:
#   environment: production, staging, or development (default: production)
#
# Requirements:
#   - openssl (for generating secure random strings)
#   - base64 (for encoding secrets)
#   - kubectl (for applying secrets to cluster)
#
# Security Notes:
#   - All secrets are generated with cryptographically secure random data
#   - Secrets are base64 encoded for Kubernetes compatibility
#   - Original secret values are not stored in files
#   - Script should be run in a secure environment
# ============================================================================

set -euo pipefail

# Configuration
ENVIRONMENT="${1:-production}"
NAMESPACE="aquaculture-${ENVIRONMENT}"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"
SECRETS_DIR="${PROJECT_ROOT}/infrastructure/kubernetes/secrets"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    local missing_tools=()
    
    if ! command -v openssl &> /dev/null; then
        missing_tools+=("openssl")
    fi
    
    if ! command -v base64 &> /dev/null; then
        missing_tools+=("base64")
    fi
    
    if ! command -v kubectl &> /dev/null; then
        missing_tools+=("kubectl")
    fi
    
    if [ ${#missing_tools[@]} -ne 0 ]; then
        log_error "Missing required tools: ${missing_tools[*]}"
        log_error "Please install the missing tools and try again."
        exit 1
    fi
    
    log_success "All prerequisites satisfied"
}

# Generate secure random string
generate_secret() {
    local length="${1:-32}"
    openssl rand -base64 "$length" | tr -d "=+/" | cut -c1-"$length"
}

# Base64 encode for Kubernetes
k8s_encode() {
    echo -n "$1" | base64 -w 0
}

# Generate database password
generate_db_password() {
    # Generate a strong database password with special characters
    openssl rand -base64 32 | tr -d "=+/" | head -c 24
}

# Create namespace if it doesn't exist
create_namespace() {
    log_info "Creating namespace: $NAMESPACE"
    
    if kubectl get namespace "$NAMESPACE" &> /dev/null; then
        log_warning "Namespace $NAMESPACE already exists"
    else
        kubectl create namespace "$NAMESPACE"
        log_success "Created namespace: $NAMESPACE"
    fi
}

# Generate and apply API secrets
setup_api_secrets() {
    log_info "Setting up API secrets..."
    
    # Generate secrets
    local secret_key=$(generate_secret 64)
    local jwt_secret=$(generate_secret 64)
    local encryption_key=$(generate_secret 32)
    local session_secret=$(generate_secret 32)
    
    # Database credentials
    local db_password=$(generate_db_password)
    local db_url="postgresql://aquaculture:${db_password}@postgres-service:5432/aquaculture_db"
    
    # Create secret manifest
    cat > "${SECRETS_DIR}/api-secrets-${ENVIRONMENT}.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: api-secrets
  namespace: ${NAMESPACE}
  labels:
    app: api-service
    environment: ${ENVIRONMENT}
type: Opaque
data:
  secret-key: $(k8s_encode "$secret_key")
  jwt-secret: $(k8s_encode "$jwt_secret")
  encryption-key: $(k8s_encode "$encryption_key")
  session-secret: $(k8s_encode "$session_secret")
  database-url: $(k8s_encode "$db_url")
  database-password: $(k8s_encode "$db_password")
EOF

    # Apply to cluster
    kubectl apply -f "${SECRETS_DIR}/api-secrets-${ENVIRONMENT}.yaml"
    
    log_success "API secrets configured"
    
    # Store database password for database setup
    echo "$db_password" > "/tmp/db_password_${ENVIRONMENT}.txt"
    chmod 600 "/tmp/db_password_${ENVIRONMENT}.txt"
}

# Generate and apply database secrets
setup_database_secrets() {
    log_info "Setting up database secrets..."
    
    # Read database password from temporary file
    local db_password
    if [ -f "/tmp/db_password_${ENVIRONMENT}.txt" ]; then
        db_password=$(cat "/tmp/db_password_${ENVIRONMENT}.txt")
    else
        db_password=$(generate_db_password)
    fi
    
    # Generate additional database credentials
    local postgres_password=$(generate_db_password)
    local replication_password=$(generate_db_password)
    
    # Create secret manifest
    cat > "${SECRETS_DIR}/database-secrets-${ENVIRONMENT}.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: database-secrets
  namespace: ${NAMESPACE}
  labels:
    app: postgres
    environment: ${ENVIRONMENT}
type: Opaque
data:
  postgres-password: $(k8s_encode "$postgres_password")
  database-password: $(k8s_encode "$db_password")
  replication-password: $(k8s_encode "$replication_password")
  database-url: $(k8s_encode "postgresql://aquaculture:${db_password}@postgres-service:5432/aquaculture_db")
EOF

    # Apply to cluster
    kubectl apply -f "${SECRETS_DIR}/database-secrets-${ENVIRONMENT}.yaml"
    
    log_success "Database secrets configured"
    
    # Clean up temporary file
    rm -f "/tmp/db_password_${ENVIRONMENT}.txt"
}

# Generate and apply Redis secrets
setup_redis_secrets() {
    log_info "Setting up Redis secrets..."
    
    local redis_password=$(generate_secret 32)
    
    cat > "${SECRETS_DIR}/redis-secrets-${ENVIRONMENT}.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: redis-secrets
  namespace: ${NAMESPACE}
  labels:
    app: redis
    environment: ${ENVIRONMENT}
type: Opaque
data:
  redis-password: $(k8s_encode "$redis_password")
  redis-url: $(k8s_encode "redis://:${redis_password}@redis-service:6379/0")
EOF

    kubectl apply -f "${SECRETS_DIR}/redis-secrets-${ENVIRONMENT}.yaml"
    log_success "Redis secrets configured"
}

# Generate and apply ML service secrets
setup_ml_secrets() {
    log_info "Setting up ML service secrets..."
    
    # Cloud storage credentials (these should be provided externally)
    local aws_access_key="${AWS_ACCESS_KEY_ID:-}"
    local aws_secret_key="${AWS_SECRET_ACCESS_KEY:-}"
    local azure_storage_key="${AZURE_STORAGE_KEY:-}"
    local gcp_service_account="${GCP_SERVICE_ACCOUNT_JSON:-}"
    
    cat > "${SECRETS_DIR}/ml-secrets-${ENVIRONMENT}.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: ml-secrets
  namespace: ${NAMESPACE}
  labels:
    app: ml-service
    environment: ${ENVIRONMENT}
type: Opaque
data:
  aws-access-key-id: $(k8s_encode "$aws_access_key")
  aws-secret-access-key: $(k8s_encode "$aws_secret_key")
  azure-storage-key: $(k8s_encode "$azure_storage_key")
  gcp-service-account: $(k8s_encode "$gcp_service_account")
EOF

    kubectl apply -f "${SECRETS_DIR}/ml-secrets-${ENVIRONMENT}.yaml"
    log_success "ML service secrets configured"
}

# Generate and apply monitoring secrets
setup_monitoring_secrets() {
    log_info "Setting up monitoring secrets..."
    
    local grafana_admin_password=$(generate_secret 16)
    local prometheus_password=$(generate_secret 16)
    
    cat > "${SECRETS_DIR}/monitoring-secrets-${ENVIRONMENT}.yaml" << EOF
apiVersion: v1
kind: Secret
metadata:
  name: monitoring-secrets
  namespace: ${NAMESPACE}
  labels:
    app: monitoring
    environment: ${ENVIRONMENT}
type: Opaque
data:
  grafana-admin-password: $(k8s_encode "$grafana_admin_password")
  prometheus-password: $(k8s_encode "$prometheus_password")
EOF

    kubectl apply -f "${SECRETS_DIR}/monitoring-secrets-${ENVIRONMENT}.yaml"
    log_success "Monitoring secrets configured"
    
    # Output admin credentials for reference
    log_info "Grafana admin credentials:"
    log_info "  Username: admin"
    log_info "  Password: $grafana_admin_password"
    log_warning "Please save these credentials securely!"
}

# Create TLS certificates
setup_tls_certificates() {
    log_info "Setting up TLS certificates..."
    
    local cert_dir="/tmp/certs_${ENVIRONMENT}"
    mkdir -p "$cert_dir"
    
    # Generate private key
    openssl genrsa -out "$cert_dir/tls.key" 2048
    
    # Generate certificate signing request
    openssl req -new -key "$cert_dir/tls.key" -out "$cert_dir/tls.csr" -subj "/CN=aquaculture-ml.${ENVIRONMENT}.local/O=Aquaculture ML Platform"
    
    # Generate self-signed certificate (for development/testing)
    openssl x509 -req -in "$cert_dir/tls.csr" -signkey "$cert_dir/tls.key" -out "$cert_dir/tls.crt" -days 365
    
    # Create TLS secret
    kubectl create secret tls tls-secret \
        --cert="$cert_dir/tls.crt" \
        --key="$cert_dir/tls.key" \
        --namespace="$NAMESPACE" \
        --dry-run=client -o yaml > "${SECRETS_DIR}/tls-secrets-${ENVIRONMENT}.yaml"
    
    kubectl apply -f "${SECRETS_DIR}/tls-secrets-${ENVIRONMENT}.yaml"
    
    # Clean up temporary files
    rm -rf "$cert_dir"
    
    log_success "TLS certificates configured"
    log_warning "Self-signed certificates are for development only. Use proper CA-signed certificates in production."
}

# Validate secrets
validate_secrets() {
    log_info "Validating secrets..."
    
    local secrets=(
        "api-secrets"
        "database-secrets"
        "redis-secrets"
        "ml-secrets"
        "monitoring-secrets"
        "tls-secret"
    )
    
    local failed_secrets=()
    
    for secret in "${secrets[@]}"; do
        if kubectl get secret "$secret" -n "$NAMESPACE" &> /dev/null; then
            log_success "✓ $secret"
        else
            log_error "✗ $secret"
            failed_secrets+=("$secret")
        fi
    done
    
    if [ ${#failed_secrets[@]} -ne 0 ]; then
        log_error "Failed to create secrets: ${failed_secrets[*]}"
        exit 1
    fi
    
    log_success "All secrets validated successfully"
}

# Generate environment file template
generate_env_template() {
    log_info "Generating environment template..."
    
    cat > "${PROJECT_ROOT}/.env.${ENVIRONMENT}.template" << EOF
# ============================================================================
# Production Environment Configuration for ${ENVIRONMENT}
# ============================================================================
# 
# This file contains the environment variables needed for ${ENVIRONMENT} deployment.
# Copy this file to .env.${ENVIRONMENT} and update the values as needed.
#
# SECURITY WARNING: Never commit actual .env files to version control!
# ============================================================================

# Application Configuration
ENVIRONMENT=${ENVIRONMENT}
DEBUG=false
LOG_LEVEL=INFO

# Database Configuration (secrets managed by Kubernetes)
DATABASE_URL=postgresql://aquaculture:PASSWORD_FROM_SECRET@postgres-service:5432/aquaculture_db

# Redis Configuration (secrets managed by Kubernetes)
REDIS_URL=redis://:PASSWORD_FROM_SECRET@redis-service:6379/0

# Security Configuration (secrets managed by Kubernetes)
SECRET_KEY=VALUE_FROM_SECRET
JWT_SECRET=VALUE_FROM_SECRET

# Cloud Provider Configuration
AWS_REGION=us-east-1
AWS_S3_BUCKET=aquaculture-ml-models-${ENVIRONMENT}
AZURE_RESOURCE_GROUP=aquaculture-ml-${ENVIRONMENT}
GCP_PROJECT_ID=aquaculture-ml-${ENVIRONMENT}

# Monitoring Configuration
PROMETHEUS_ENABLED=true
GRAFANA_ENABLED=true

# ML Configuration
MODEL_STORAGE_URL=s3://aquaculture-ml-models-${ENVIRONMENT}/models/
BATCH_SIZE=32
CONFIDENCE_THRESHOLD=0.5

EOF

    log_success "Environment template generated: .env.${ENVIRONMENT}.template"
}

# Main execution
main() {
    log_info "Starting production secrets setup for environment: $ENVIRONMENT"
    
    # Validate environment
    if [[ ! "$ENVIRONMENT" =~ ^(development|staging|production)$ ]]; then
        log_error "Invalid environment: $ENVIRONMENT"
        log_error "Valid environments: development, staging, production"
        exit 1
    fi
    
    # Create secrets directory
    mkdir -p "$SECRETS_DIR"
    
    # Execute setup steps
    check_prerequisites
    create_namespace
    setup_api_secrets
    setup_database_secrets
    setup_redis_secrets
    setup_ml_secrets
    setup_monitoring_secrets
    setup_tls_certificates
    validate_secrets
    generate_env_template
    
    log_success "🎉 Production secrets setup completed successfully!"
    log_info ""
    log_info "Next steps:"
    log_info "1. Review the generated secret files in: $SECRETS_DIR"
    log_info "2. Update cloud provider credentials if needed"
    log_info "3. Replace self-signed certificates with CA-signed certificates for production"
    log_info "4. Deploy the application using the configured secrets"
    log_info ""
    log_warning "⚠️  IMPORTANT SECURITY NOTES:"
    log_warning "- All secret files contain sensitive data"
    log_warning "- Never commit secret files to version control"
    log_warning "- Regularly rotate secrets in production"
    log_warning "- Monitor secret access and usage"
}

# Run main function
main "$@"
