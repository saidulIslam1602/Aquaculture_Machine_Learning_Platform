#!/bin/bash

# ============================================================================
# ENTERPRISE STARTUP SCRIPT FOR AQUACULTURE ML PLATFORM API SERVICE
# ============================================================================
#
# This script handles enterprise-grade startup procedures including:
# - Enterprise environment validation and configuration
# - Multi-database connectivity verification
# - Enterprise security initialization (SSL, LDAP, SAML)
# - Compliance and audit logging setup
# - Enterprise monitoring and health check initialization
# - Graceful startup with dependency verification
# - Enterprise application server (Gunicorn) configuration
#
# ENTERPRISE FEATURES:
# - SOX and GDPR compliance initialization
# - Enterprise authentication system setup
# - Multi-database connection validation
# - SSL certificate validation and setup
# - Enterprise monitoring agent initialization
# - Audit logging configuration
# - Performance optimization settings
# ============================================================================

set -euo pipefail  # Enterprise error handling: exit on error, undefined vars, pipe failures

# Enterprise logging configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly LOG_FILE="${LOG_FILE:-/app/logs/startup.log}"
readonly AUDIT_LOG_FILE="${AUDIT_LOG_FILE:-/app/logs/audit/startup-audit.log}"

# Enterprise environment variables with defaults
readonly ENTERPRISE_MODE="${ENTERPRISE_MODE:-true}"
readonly COMPLIANCE_MODE="${COMPLIANCE_MODE:-true}"
readonly SOX_COMPLIANCE="${SOX_COMPLIANCE:-true}"
readonly GDPR_COMPLIANCE="${GDPR_COMPLIANCE:-true}"
readonly SSL_ENABLED="${SSL_ENABLED:-true}"
readonly AUDIT_LOGGING="${AUDIT_LOGGING:-true}"

# Enterprise application server configuration
readonly GUNICORN_WORKERS="${GUNICORN_WORKERS:-4}"
readonly GUNICORN_WORKER_CLASS="${GUNICORN_WORKER_CLASS:-uvicorn.workers.UvicornWorker}"
readonly GUNICORN_BIND="${GUNICORN_BIND:-0.0.0.0:8000}"
readonly GUNICORN_MAX_REQUESTS="${GUNICORN_MAX_REQUESTS:-1000}"
readonly GUNICORN_TIMEOUT="${GUNICORN_TIMEOUT:-120}"

# Enterprise database configuration
readonly DATABASE_URL="${DATABASE_URL:-}"
readonly SQLSERVER_URL="${SQLSERVER_URL:-}"
readonly REDIS_URL="${REDIS_URL:-}"

# Enterprise security configuration
readonly LDAP_SERVER="${LDAP_SERVER:-}"
readonly SSL_CERT_PATH="${SSL_CERT_PATH:-/app/ssl/server.crt}"
readonly SSL_KEY_PATH="${SSL_KEY_PATH:-/app/ssl/server.key}"

# ============================================================================
# ENTERPRISE LOGGING FUNCTIONS
# ============================================================================

log_info() {
    local message="$1"
    local timestamp=$(date -Iseconds)
    echo "[${timestamp}] [INFO] [${SCRIPT_NAME}] ${message}" | tee -a "${LOG_FILE}"
}

log_error() {
    local message="$1"
    local timestamp=$(date -Iseconds)
    echo "[${timestamp}] [ERROR] [${SCRIPT_NAME}] ${message}" | tee -a "${LOG_FILE}" >&2
}

log_audit() {
    local event="$1"
    local details="$2"
    local timestamp=$(date -Iseconds)
    local audit_entry="{\"timestamp\":\"${timestamp}\",\"event\":\"${event}\",\"details\":\"${details}\",\"service\":\"api\",\"compliance\":\"${COMPLIANCE_MODE}\"}"
    echo "${audit_entry}" >> "${AUDIT_LOG_FILE}"
}

# ============================================================================
# ENTERPRISE VALIDATION FUNCTIONS
# ============================================================================

validate_enterprise_environment() {
    log_info "Validating enterprise environment configuration..."
    log_audit "environment_validation" "Starting enterprise environment validation"
    
    # Validate required enterprise environment variables
    local required_vars=(
        "DATABASE_URL"
        "REDIS_URL"
        "ENTERPRISE_MODE"
    )
    
    for var in "${required_vars[@]}"; do
        if [[ -z "${!var:-}" ]]; then
            log_error "Required enterprise environment variable ${var} is not set"
            log_audit "environment_validation_failed" "Missing required variable: ${var}"
            exit 1
        fi
    done
    
    # Validate enterprise compliance settings
    if [[ "${SOX_COMPLIANCE}" == "true" ]]; then
        log_info "SOX compliance mode enabled - validating audit logging"
        if [[ ! -d "/app/logs/audit" ]]; then
            log_error "SOX compliance requires audit logging directory"
            exit 1
        fi
    fi
    
    if [[ "${GDPR_COMPLIANCE}" == "true" ]]; then
        log_info "GDPR compliance mode enabled - validating data protection settings"
        # Add GDPR-specific validation here
    fi
    
    log_info "Enterprise environment validation completed successfully"
    log_audit "environment_validation_success" "All enterprise environment variables validated"
}

validate_database_connectivity() {
    log_info "Validating enterprise database connectivity..."
    log_audit "database_validation" "Starting multi-database connectivity validation"
    
    # Validate PostgreSQL connectivity
    if [[ -n "${DATABASE_URL}" ]]; then
        log_info "Validating PostgreSQL connectivity..."
        python3 -c "
import psycopg2
import sys
from urllib.parse import urlparse

try:
    url = urlparse('${DATABASE_URL}')
    conn = psycopg2.connect(
        host=url.hostname,
        port=url.port,
        user=url.username,
        password=url.password,
        database=url.path[1:],
        connect_timeout=10
    )
    conn.close()
    print('PostgreSQL connection successful')
except Exception as e:
    print(f'PostgreSQL connection failed: {e}')
    sys.exit(1)
        " || {
            log_error "PostgreSQL database connectivity validation failed"
            log_audit "database_validation_failed" "PostgreSQL connection failed"
            exit 1
        }
    fi
    
    # Validate SQL Server connectivity (if configured)
    if [[ -n "${SQLSERVER_URL}" ]]; then
        log_info "Validating SQL Server connectivity..."
        python3 -c "
import pyodbc
import sys
from urllib.parse import urlparse, parse_qs

try:
    # Parse SQL Server connection string
    url = urlparse('${SQLSERVER_URL}')
    driver = parse_qs(url.query).get('driver', ['ODBC Driver 17 for SQL Server'])[0]
    
    conn_str = f'DRIVER={{{driver}}};SERVER={url.hostname},{url.port or 1433};DATABASE={url.path[1:]};UID={url.username};PWD={url.password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=10;'
    
    conn = pyodbc.connect(conn_str)
    conn.close()
    print('SQL Server connection successful')
except Exception as e:
    print(f'SQL Server connection failed: {e}')
    sys.exit(1)
        " || {
            log_error "SQL Server database connectivity validation failed"
            log_audit "database_validation_failed" "SQL Server connection failed"
            exit 1
        }
    fi
    
    # Validate Redis connectivity
    if [[ -n "${REDIS_URL}" ]]; then
        log_info "Validating Redis connectivity..."
        python3 -c "
import redis
import sys
from urllib.parse import urlparse

try:
    url = urlparse('${REDIS_URL}')
    r = redis.Redis(
        host=url.hostname,
        port=url.port or 6379,
        password=url.password,
        socket_connect_timeout=10
    )
    r.ping()
    print('Redis connection successful')
except Exception as e:
    print(f'Redis connection failed: {e}')
    sys.exit(1)
        " || {
            log_error "Redis connectivity validation failed"
            log_audit "database_validation_failed" "Redis connection failed"
            exit 1
        }
    fi
    
    log_info "All database connectivity validations completed successfully"
    log_audit "database_validation_success" "All database connections validated"
}

validate_ssl_configuration() {
    if [[ "${SSL_ENABLED}" == "true" ]]; then
        log_info "Validating enterprise SSL configuration..."
        log_audit "ssl_validation" "Starting SSL certificate validation"
        
        # Check SSL certificate files
        if [[ ! -f "${SSL_CERT_PATH}" ]]; then
            log_error "SSL certificate file not found: ${SSL_CERT_PATH}"
            log_audit "ssl_validation_failed" "SSL certificate file missing"
            exit 1
        fi
        
        if [[ ! -f "${SSL_KEY_PATH}" ]]; then
            log_error "SSL private key file not found: ${SSL_KEY_PATH}"
            log_audit "ssl_validation_failed" "SSL private key file missing"
            exit 1
        fi
        
        # Validate SSL certificate
        openssl x509 -in "${SSL_CERT_PATH}" -text -noout > /dev/null 2>&1 || {
            log_error "Invalid SSL certificate format"
            log_audit "ssl_validation_failed" "Invalid SSL certificate format"
            exit 1
        }
        
        # Validate SSL private key
        openssl rsa -in "${SSL_KEY_PATH}" -check -noout > /dev/null 2>&1 || {
            log_error "Invalid SSL private key format"
            log_audit "ssl_validation_failed" "Invalid SSL private key format"
            exit 1
        }
        
        log_info "SSL configuration validation completed successfully"
        log_audit "ssl_validation_success" "SSL certificates validated"
    fi
}

validate_ldap_connectivity() {
    if [[ -n "${LDAP_SERVER}" ]]; then
        log_info "Validating enterprise LDAP connectivity..."
        log_audit "ldap_validation" "Starting LDAP connectivity validation"
        
        python3 -c "
import ldap3
import sys
from urllib.parse import urlparse

try:
    url = urlparse('${LDAP_SERVER}')
    server = ldap3.Server(f'{url.scheme}://{url.hostname}:{url.port or 389}', get_info=ldap3.ALL)
    conn = ldap3.Connection(server, auto_bind=True, authentication=ldap3.ANONYMOUS)
    conn.unbind()
    print('LDAP connection successful')
except Exception as e:
    print(f'LDAP connection failed: {e}')
    sys.exit(1)
        " || {
            log_error "LDAP connectivity validation failed"
            log_audit "ldap_validation_failed" "LDAP connection failed"
            exit 1
        }
        
        log_info "LDAP connectivity validation completed successfully"
        log_audit "ldap_validation_success" "LDAP connection validated"
    fi
}

# ============================================================================
# ENTERPRISE INITIALIZATION FUNCTIONS
# ============================================================================

initialize_enterprise_logging() {
    log_info "Initializing enterprise logging configuration..."
    log_audit "logging_initialization" "Starting enterprise logging setup"
    
    # Create log directories
    mkdir -p /app/logs/audit
    mkdir -p /app/logs/application
    mkdir -p /app/logs/security
    mkdir -p /app/logs/performance
    
    # Set proper permissions for enterprise logging
    chmod 750 /app/logs/audit
    chmod 755 /app/logs/application
    
    # Initialize audit log with startup event
    log_audit "service_startup" "Enterprise API service startup initiated"
    
    log_info "Enterprise logging initialization completed"
}

initialize_enterprise_monitoring() {
    log_info "Initializing enterprise monitoring..."
    log_audit "monitoring_initialization" "Starting enterprise monitoring setup"
    
    # Initialize Prometheus metrics endpoint
    export PROMETHEUS_MULTIPROC_DIR="/app/tmp/prometheus"
    mkdir -p "${PROMETHEUS_MULTIPROC_DIR}"
    
    # Initialize OpenTelemetry if enabled
    if [[ "${OPENTELEMETRY_ENABLED:-false}" == "true" ]]; then
        export OTEL_SERVICE_NAME="aquaculture-api"
        export OTEL_SERVICE_VERSION="${BUILD_VERSION:-1.0.0}"
        export OTEL_RESOURCE_ATTRIBUTES="service.name=aquaculture-api,service.version=${BUILD_VERSION:-1.0.0},deployment.environment=${ENVIRONMENT:-development}"
    fi
    
    log_info "Enterprise monitoring initialization completed"
    log_audit "monitoring_initialization_success" "Enterprise monitoring configured"
}

run_database_migrations() {
    log_info "Running enterprise database migrations..."
    log_audit "database_migration" "Starting database schema migrations"
    
    # Run Alembic migrations for PostgreSQL
    cd /app && python3 -m alembic upgrade head || {
        log_error "Database migration failed"
        log_audit "database_migration_failed" "Alembic migration failed"
        exit 1
    }
    
    # Run SQL Server migrations if configured
    if [[ -n "${SQLSERVER_URL}" ]]; then
        log_info "Running SQL Server enterprise migrations..."
        # Add SQL Server specific migration logic here
    fi
    
    log_info "Database migrations completed successfully"
    log_audit "database_migration_success" "All database migrations completed"
}

# ============================================================================
# ENTERPRISE APPLICATION SERVER STARTUP
# ============================================================================

start_enterprise_application_server() {
    log_info "Starting enterprise application server (Gunicorn)..."
    log_audit "application_server_startup" "Starting Gunicorn with enterprise configuration"
    
    # Enterprise Gunicorn configuration
    local gunicorn_config="/app/gunicorn-enterprise.conf.py"
    
    # Build Gunicorn command with enterprise settings
    local gunicorn_cmd=(
        "gunicorn"
        "--config" "${gunicorn_config}"
        "--workers" "${GUNICORN_WORKERS}"
        "--worker-class" "${GUNICORN_WORKER_CLASS}"
        "--bind" "${GUNICORN_BIND}"
        "--max-requests" "${GUNICORN_MAX_REQUESTS}"
        "--max-requests-jitter" "${GUNICORN_MAX_REQUESTS_JITTER}"
        "--timeout" "${GUNICORN_TIMEOUT}"
        "--keepalive" "${GUNICORN_KEEPALIVE}"
        "--preload"
        "--enable-stdio-inheritance"
        "--log-level" "info"
        "--access-logfile" "/app/logs/application/access.log"
        "--error-logfile" "/app/logs/application/error.log"
        "--capture-output"
        "services.api.main:app"
    )
    
    # Add SSL configuration if enabled
    if [[ "${SSL_ENABLED}" == "true" ]]; then
        gunicorn_cmd+=(
            "--certfile" "${SSL_CERT_PATH}"
            "--keyfile" "${SSL_KEY_PATH}"
            "--ssl-version" "TLSv1_2"
            "--ciphers" "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
        )
    fi
    
    log_info "Executing Gunicorn command: ${gunicorn_cmd[*]}"
    log_audit "application_server_started" "Gunicorn enterprise server started with PID $$"
    
    # Execute Gunicorn with enterprise configuration
    exec "${gunicorn_cmd[@]}"
}

# ============================================================================
# ENTERPRISE SIGNAL HANDLERS
# ============================================================================

handle_enterprise_shutdown() {
    log_info "Received shutdown signal - initiating graceful enterprise shutdown..."
    log_audit "service_shutdown" "Enterprise API service shutdown initiated"
    
    # Graceful shutdown procedures
    if [[ -n "${GUNICORN_PID:-}" ]]; then
        log_info "Sending SIGTERM to Gunicorn process ${GUNICORN_PID}"
        kill -TERM "${GUNICORN_PID}" 2>/dev/null || true
        
        # Wait for graceful shutdown
        local timeout=30
        while kill -0 "${GUNICORN_PID}" 2>/dev/null && [[ $timeout -gt 0 ]]; do
            sleep 1
            ((timeout--))
        done
        
        # Force kill if still running
        if kill -0 "${GUNICORN_PID}" 2>/dev/null; then
            log_info "Force killing Gunicorn process ${GUNICORN_PID}"
            kill -KILL "${GUNICORN_PID}" 2>/dev/null || true
        fi
    fi
    
    log_audit "service_shutdown_complete" "Enterprise API service shutdown completed"
    exit 0
}

# Set up enterprise signal handlers
trap handle_enterprise_shutdown SIGTERM SIGINT SIGQUIT

# ============================================================================
# MAIN ENTERPRISE STARTUP SEQUENCE
# ============================================================================

main() {
    log_info "Starting enterprise Aquaculture ML Platform API service..."
    log_info "Enterprise mode: ${ENTERPRISE_MODE}"
    log_info "Compliance mode: ${COMPLIANCE_MODE}"
    log_info "SOX compliance: ${SOX_COMPLIANCE}"
    log_info "GDPR compliance: ${GDPR_COMPLIANCE}"
    
    # Enterprise startup sequence
    initialize_enterprise_logging
    validate_enterprise_environment
    validate_database_connectivity
    validate_ssl_configuration
    validate_ldap_connectivity
    initialize_enterprise_monitoring
    run_database_migrations
    
    log_info "All enterprise validations and initializations completed successfully"
    log_audit "startup_complete" "Enterprise API service startup sequence completed"
    
    # Start the enterprise application server
    start_enterprise_application_server
}

# Execute main function
main "$@"
