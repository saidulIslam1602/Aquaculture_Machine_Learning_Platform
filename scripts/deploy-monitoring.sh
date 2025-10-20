#!/bin/bash

# Enhanced Monitoring Deployment Script for Aquaculture ML Platform
# Deploys comprehensive observability stack with Prometheus, Grafana, Alertmanager, and ELK

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
MONITORING_NAMESPACE="monitoring"
APP_NAMESPACE="aquaculture-prod"
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(dirname "$SCRIPT_DIR")"

# Functions
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

check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check if Docker is running
    if ! docker info >/dev/null 2>&1; then
        log_error "Docker is not running. Please start Docker and try again."
        exit 1
    fi
    
    # Check if docker-compose is available
    if ! command -v docker-compose &> /dev/null; then
        log_error "docker-compose is not installed. Please install it and try again."
        exit 1
    fi
    
    # Check if kubectl is available (for Kubernetes deployment)
    if command -v kubectl &> /dev/null; then
        log_info "kubectl found - Kubernetes deployment available"
        KUBECTL_AVAILABLE=true
    else
        log_warning "kubectl not found - Kubernetes deployment will be skipped"
        KUBECTL_AVAILABLE=false
    fi
    
    log_success "Prerequisites check completed"
}

create_directories() {
    log_info "Creating monitoring directories..."
    
    mkdir -p "$PROJECT_ROOT/monitoring/prometheus/rules"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards"
    mkdir -p "$PROJECT_ROOT/monitoring/grafana/provisioning/datasources"
    mkdir -p "$PROJECT_ROOT/monitoring/alertmanager"
    mkdir -p "$PROJECT_ROOT/monitoring/elk/elasticsearch/config"
    mkdir -p "$PROJECT_ROOT/monitoring/elk/logstash/config"
    mkdir -p "$PROJECT_ROOT/monitoring/elk/kibana/config"
    mkdir -p "$PROJECT_ROOT/monitoring/elk/filebeat/config"
    mkdir -p "$PROJECT_ROOT/data/prometheus"
    mkdir -p "$PROJECT_ROOT/data/grafana"
    mkdir -p "$PROJECT_ROOT/data/elasticsearch"
    mkdir -p "$PROJECT_ROOT/data/kibana"
    
    log_success "Directories created"
}

setup_grafana_provisioning() {
    log_info "Setting up Grafana provisioning..."
    
    # Create datasource configuration
    cat > "$PROJECT_ROOT/monitoring/grafana/provisioning/datasources/prometheus.yml" << EOF
apiVersion: 1

datasources:
  - name: Prometheus
    type: prometheus
    access: proxy
    url: http://prometheus:9090
    isDefault: true
    editable: true
    jsonData:
      timeInterval: "15s"
      queryTimeout: "60s"
      httpMethod: "POST"
    
  - name: Elasticsearch
    type: elasticsearch
    access: proxy
    url: http://elasticsearch:9200
    database: "aquaculture-*"
    jsonData:
      esVersion: "8.0.0"
      timeField: "@timestamp"
      interval: "Daily"
      logMessageField: "message"
      logLevelField: "level"
EOF

    # Create dashboard provisioning
    cat > "$PROJECT_ROOT/monitoring/grafana/provisioning/dashboards/dashboards.yml" << EOF
apiVersion: 1

providers:
  - name: 'Aquaculture Dashboards'
    orgId: 1
    folder: 'Aquaculture ML Platform'
    type: file
    disableDeletion: false
    updateIntervalSeconds: 10
    allowUiUpdates: true
    options:
      path: /var/lib/grafana/dashboards
EOF

    log_success "Grafana provisioning configured"
}

deploy_docker_monitoring() {
    log_info "Deploying monitoring stack with Docker Compose..."
    
    cd "$PROJECT_ROOT"
    
    # Deploy main monitoring stack
    log_info "Starting Prometheus, Grafana, and Alertmanager..."
    docker-compose -f docker-compose.yml up -d prometheus grafana alertmanager node-exporter cadvisor redis-exporter postgres-exporter jaeger
    
    # Wait for services to be ready
    log_info "Waiting for services to be ready..."
    sleep 30
    
    # Check service health
    check_service_health "Prometheus" "http://localhost:9090/-/healthy"
    check_service_health "Grafana" "http://localhost:3000/api/health"
    check_service_health "Alertmanager" "http://localhost:9093/-/healthy"
    
    log_success "Main monitoring stack deployed successfully"
}

deploy_elk_stack() {
    log_info "Deploying ELK stack..."
    
    cd "$PROJECT_ROOT/monitoring/elk"
    
    # Deploy ELK stack
    docker-compose -f docker-compose-elk.yml up -d
    
    # Wait for Elasticsearch to be ready
    log_info "Waiting for Elasticsearch to be ready..."
    wait_for_elasticsearch
    
    # Wait for Kibana to be ready
    log_info "Waiting for Kibana to be ready..."
    wait_for_kibana
    
    log_success "ELK stack deployed successfully"
}

deploy_kubernetes_monitoring() {
    if [ "$KUBECTL_AVAILABLE" = false ]; then
        log_warning "Skipping Kubernetes deployment - kubectl not available"
        return
    fi
    
    log_info "Deploying Kubernetes monitoring resources..."
    
    # Create namespaces
    kubectl create namespace "$MONITORING_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    kubectl create namespace "$APP_NAMESPACE" --dry-run=client -o yaml | kubectl apply -f -
    
    # Deploy ServiceMonitors and PrometheusRules
    kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/enhanced-servicemonitor.yaml" -n "$APP_NAMESPACE"
    kubectl apply -f "$PROJECT_ROOT/infrastructure/kubernetes/prometheus-rules.yaml" -n "$APP_NAMESPACE"
    
    log_success "Kubernetes monitoring resources deployed"
}

check_service_health() {
    local service_name="$1"
    local health_url="$2"
    local max_attempts=30
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "$health_url" >/dev/null 2>&1; then
            log_success "$service_name is healthy"
            return 0
        fi
        
        log_info "Waiting for $service_name to be ready (attempt $attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done
    
    log_error "$service_name health check failed after $max_attempts attempts"
    return 1
}

wait_for_elasticsearch() {
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:9200/_cluster/health" >/dev/null 2>&1; then
            log_success "Elasticsearch is ready"
            return 0
        fi
        
        log_info "Waiting for Elasticsearch (attempt $attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Elasticsearch failed to start after $max_attempts attempts"
    return 1
}

wait_for_kibana() {
    local max_attempts=60
    local attempt=1
    
    while [ $attempt -le $max_attempts ]; do
        if curl -f -s "http://localhost:5601/api/status" >/dev/null 2>&1; then
            log_success "Kibana is ready"
            return 0
        fi
        
        log_info "Waiting for Kibana (attempt $attempt/$max_attempts)..."
        sleep 10
        ((attempt++))
    done
    
    log_error "Kibana failed to start after $max_attempts attempts"
    return 1
}

setup_kibana_dashboards() {
    log_info "Setting up Kibana dashboards and index patterns..."
    
    # Wait a bit more for Kibana to fully initialize
    sleep 30
    
    # Create index patterns
    curl -X POST "localhost:5601/api/saved_objects/index-pattern/aquaculture-api" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d '{
            "attributes": {
                "title": "aquaculture-api-*",
                "timeFieldName": "@timestamp"
            }
        }' || log_warning "Failed to create API index pattern"
    
    curl -X POST "localhost:5601/api/saved_objects/index-pattern/aquaculture-ml" \
        -H "Content-Type: application/json" \
        -H "kbn-xsrf: true" \
        -d '{
            "attributes": {
                "title": "aquaculture-ml-*",
                "timeFieldName": "@timestamp"
            }
        }' || log_warning "Failed to create ML index pattern"
    
    log_success "Kibana setup completed"
}

print_access_info() {
    log_success "Monitoring stack deployment completed!"
    echo
    echo "Access Information:"
    echo "=================="
    echo "🔍 Prometheus:    http://localhost:9090"
    echo "📊 Grafana:       http://localhost:3000 (admin/admin)"
    echo "🚨 Alertmanager:  http://localhost:9093"
    echo "📈 Kibana:        http://localhost:5601"
    echo "🔍 Elasticsearch: http://localhost:9200"
    echo "🔍 Jaeger:        http://localhost:16686"
    echo
    echo "Default Credentials:"
    echo "==================="
    echo "Grafana: admin/admin (change on first login)"
    echo
    echo "Health Check Commands:"
    echo "====================="
    echo "curl http://localhost:9090/-/healthy    # Prometheus"
    echo "curl http://localhost:3000/api/health   # Grafana"
    echo "curl http://localhost:9093/-/healthy    # Alertmanager"
    echo "curl http://localhost:9200/_cluster/health  # Elasticsearch"
    echo "curl http://localhost:5601/api/status   # Kibana"
    echo
}

cleanup_on_error() {
    log_error "Deployment failed. Cleaning up..."
    docker-compose -f "$PROJECT_ROOT/docker-compose.yml" down || true
    docker-compose -f "$PROJECT_ROOT/monitoring/elk/docker-compose-elk.yml" down || true
}

main() {
    log_info "Starting enhanced monitoring deployment for Aquaculture ML Platform"
    
    # Set up error handling
    trap cleanup_on_error ERR
    
    # Main deployment steps
    check_prerequisites
    create_directories
    setup_grafana_provisioning
    
    # Deploy monitoring components
    deploy_docker_monitoring
    
    # Deploy ELK stack if requested
    if [[ "${1:-}" == "--with-elk" ]] || [[ "${1:-}" == "--full" ]]; then
        deploy_elk_stack
        setup_kibana_dashboards
    fi
    
    # Deploy Kubernetes resources if available
    if [[ "${1:-}" == "--with-k8s" ]] || [[ "${1:-}" == "--full" ]]; then
        deploy_kubernetes_monitoring
    fi
    
    print_access_info
    
    log_success "Deployment completed successfully!"
}

# Script usage
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    case "${1:-}" in
        --help|-h)
            echo "Usage: $0 [OPTIONS]"
            echo
            echo "Options:"
            echo "  --full      Deploy complete monitoring stack (Docker + ELK + K8s)"
            echo "  --with-elk  Deploy Docker monitoring + ELK stack"
            echo "  --with-k8s  Deploy Docker monitoring + Kubernetes resources"
            echo "  --help      Show this help message"
            echo
            echo "Default: Deploy Docker monitoring stack only"
            exit 0
            ;;
        *)
            main "$@"
            ;;
    esac
fi
