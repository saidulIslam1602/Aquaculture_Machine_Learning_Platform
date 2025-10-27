#!/bin/bash

# =============================================================================
# ENTERPRISE HEALTH CHECK SCRIPT - AQUACULTURE PLATFORM MONITORING
# =============================================================================
#
# WHAT IS THIS SCRIPT?
# This script acts as a "doctor" for the enterprise API service, continuously
# checking the health of all components to ensure everything is working properly.
# Think of it as a comprehensive medical checkup that runs automatically.
#
# WHAT DOES A HEALTH CHECK DO?
# Health checks are like taking the "pulse" of the application:
# - Verifies the API service is responding to requests
# - Tests database connections (PostgreSQL, SQL Server, Redis)
# - Checks SSL certificates haven't expired
# - Monitors system resources (CPU, memory, disk space)
# - Validates enterprise integrations (LDAP, authentication systems)
# - Ensures compliance and audit systems are working
#
# WHY ARE ENTERPRISE HEALTH CHECKS IMPORTANT?
# Enterprise environments need more thorough monitoring because:
# - Multiple systems must work together (databases, authentication, monitoring)
# - Compliance requirements demand continuous monitoring
# - Early detection prevents costly downtime
# - Automated alerts help teams respond quickly to issues
# - Regulatory audits require proof of system monitoring
#
# WHAT GETS CHECKED?
# - Application Health: API endpoints responding correctly
# - Database Connectivity: All database connections working
# - Security Systems: SSL certificates valid, LDAP accessible
# - Performance Metrics: Response times within acceptable limits
# - Compliance Systems: Audit logging and monitoring active
# - Resource Usage: CPU, memory, and disk space adequate
#
# HOW IT WORKS:
# 1. Script runs every 30 seconds (configured in Dockerfile)
# 2. Performs series of health checks in order of importance
# 3. Logs results for monitoring and compliance
# 4. Returns success (0) or failure (1) to Docker/Kubernetes
# 5. Failed health checks trigger container restart or alerts
#
# AUTHOR: DevOps Team
# VERSION: 1.0.0
# UPDATED: 2024-10-26
# =============================================================================

set -euo pipefail

# Enterprise health check configuration
readonly SCRIPT_NAME="$(basename "$0")"
readonly HEALTH_LOG="/app/logs/health.log"
readonly HEALTH_TIMEOUT="${HEALTH_TIMEOUT:-10}"
readonly HEALTH_RETRIES="${HEALTH_RETRIES:-3}"

# Enterprise service endpoints
readonly API_ENDPOINT="${API_ENDPOINT:-https://localhost:8443}"
readonly HEALTH_ENDPOINT="${API_ENDPOINT}/health"
readonly METRICS_ENDPOINT="${API_ENDPOINT}/metrics"
readonly READINESS_ENDPOINT="${API_ENDPOINT}/ready"

# Enterprise database configuration
readonly DATABASE_URL="${DATABASE_URL:-}"
readonly SQLSERVER_URL="${SQLSERVER_URL:-}"
readonly REDIS_URL="${REDIS_URL:-}"

# Enterprise security configuration
readonly SSL_ENABLED="${SSL_ENABLED:-true}"
readonly SSL_CERT_PATH="${SSL_CERT_PATH:-/app/ssl/server.crt}"
readonly LDAP_SERVER="${LDAP_SERVER:-}"

# Enterprise compliance configuration
readonly SOX_COMPLIANCE="${SOX_COMPLIANCE:-true}"
readonly GDPR_COMPLIANCE="${GDPR_COMPLIANCE:-true}"
readonly AUDIT_LOGGING="${AUDIT_LOGGING:-true}"

# Health check results
declare -A HEALTH_RESULTS
OVERALL_HEALTH="healthy"

# ============================================================================
# ENTERPRISE LOGGING FUNCTIONS
# ============================================================================

log_health() {
    local level="$1"
    local message="$2"
    local timestamp=$(date -Iseconds)
    echo "[${timestamp}] [${level}] [HEALTH] ${message}" | tee -a "${HEALTH_LOG}"
}

log_health_metric() {
    local metric_name="$1"
    local metric_value="$2"
    local metric_status="$3"
    local timestamp=$(date -Iseconds)
    
    local health_metric="{\"timestamp\":\"${timestamp}\",\"metric\":\"${metric_name}\",\"value\":\"${metric_value}\",\"status\":\"${metric_status}\",\"service\":\"api\"}"
    echo "${health_metric}" >> "/app/logs/health-metrics.log"
}

# ============================================================================
# ENTERPRISE HEALTH CHECK FUNCTIONS
# ============================================================================

check_application_health() {
    log_health "INFO" "Checking enterprise application health..."
    
    local retry_count=0
    local health_status="unhealthy"
    
    while [[ $retry_count -lt $HEALTH_RETRIES ]]; do
        if curl -f -s -k --connect-timeout "${HEALTH_TIMEOUT}" "${HEALTH_ENDPOINT}" > /dev/null 2>&1; then
            health_status="healthy"
            break
        fi
        
        ((retry_count++))
        sleep 1
    done
    
    HEALTH_RESULTS["application"]="${health_status}"
    log_health_metric "application_health" "${health_status}" "${health_status}"
    
    if [[ "${health_status}" != "healthy" ]]; then
        log_health "ERROR" "Application health check failed after ${HEALTH_RETRIES} retries"
        OVERALL_HEALTH="unhealthy"
        return 1
    fi
    
    log_health "INFO" "Application health check passed"
    return 0
}

check_database_connectivity() {
    log_health "INFO" "Checking enterprise database connectivity..."
    
    # Check PostgreSQL connectivity
    if [[ -n "${DATABASE_URL}" ]]; then
        log_health "INFO" "Checking PostgreSQL connectivity..."
        
        if python3 -c "
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
        connect_timeout=5
    )
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.fetchone()
    cursor.close()
    conn.close()
    print('healthy')
except Exception:
    print('unhealthy')
        " 2>/dev/null | grep -q "healthy"; then
            HEALTH_RESULTS["postgresql"]="healthy"
            log_health_metric "postgresql_connectivity" "healthy" "healthy"
            log_health "INFO" "PostgreSQL connectivity check passed"
        else
            HEALTH_RESULTS["postgresql"]="unhealthy"
            log_health_metric "postgresql_connectivity" "unhealthy" "unhealthy"
            log_health "ERROR" "PostgreSQL connectivity check failed"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
    
    # Check SQL Server connectivity
    if [[ -n "${SQLSERVER_URL}" ]]; then
        log_health "INFO" "Checking SQL Server connectivity..."
        
        if python3 -c "
import pyodbc
import sys
from urllib.parse import urlparse, parse_qs

try:
    url = urlparse('${SQLSERVER_URL}')
    driver = parse_qs(url.query).get('driver', ['ODBC Driver 17 for SQL Server'])[0]
    
    conn_str = f'DRIVER={{{driver}}};SERVER={url.hostname},{url.port or 1433};DATABASE={url.path[1:]};UID={url.username};PWD={url.password};Encrypt=yes;TrustServerCertificate=yes;Connection Timeout=5;'
    
    conn = pyodbc.connect(conn_str)
    cursor = conn.cursor()
    cursor.execute('SELECT 1')
    cursor.fetchone()
    cursor.close()
    conn.close()
    print('healthy')
except Exception:
    print('unhealthy')
        " 2>/dev/null | grep -q "healthy"; then
            HEALTH_RESULTS["sqlserver"]="healthy"
            log_health_metric "sqlserver_connectivity" "healthy" "healthy"
            log_health "INFO" "SQL Server connectivity check passed"
        else
            HEALTH_RESULTS["sqlserver"]="unhealthy"
            log_health_metric "sqlserver_connectivity" "unhealthy" "unhealthy"
            log_health "ERROR" "SQL Server connectivity check failed"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
    
    # Check Redis connectivity
    if [[ -n "${REDIS_URL}" ]]; then
        log_health "INFO" "Checking Redis connectivity..."
        
        if python3 -c "
import redis
import sys
from urllib.parse import urlparse

try:
    url = urlparse('${REDIS_URL}')
    r = redis.Redis(
        host=url.hostname,
        port=url.port or 6379,
        password=url.password,
        socket_connect_timeout=5
    )
    r.ping()
    print('healthy')
except Exception:
    print('unhealthy')
        " 2>/dev/null | grep -q "healthy"; then
            HEALTH_RESULTS["redis"]="healthy"
            log_health_metric "redis_connectivity" "healthy" "healthy"
            log_health "INFO" "Redis connectivity check passed"
        else
            HEALTH_RESULTS["redis"]="unhealthy"
            log_health_metric "redis_connectivity" "unhealthy" "unhealthy"
            log_health "ERROR" "Redis connectivity check failed"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
}

check_ssl_certificate_health() {
    if [[ "${SSL_ENABLED}" == "true" && -f "${SSL_CERT_PATH}" ]]; then
        log_health "INFO" "Checking SSL certificate health..."
        
        # Check certificate expiration
        local cert_expiry
        cert_expiry=$(openssl x509 -in "${SSL_CERT_PATH}" -noout -enddate 2>/dev/null | cut -d= -f2)
        
        if [[ -n "${cert_expiry}" ]]; then
            local expiry_epoch
            expiry_epoch=$(date -d "${cert_expiry}" +%s 2>/dev/null)
            local current_epoch
            current_epoch=$(date +%s)
            local days_until_expiry=$(( (expiry_epoch - current_epoch) / 86400 ))
            
            if [[ $days_until_expiry -gt 30 ]]; then
                HEALTH_RESULTS["ssl_certificate"]="healthy"
                log_health_metric "ssl_certificate_days_until_expiry" "${days_until_expiry}" "healthy"
                log_health "INFO" "SSL certificate is valid (expires in ${days_until_expiry} days)"
            elif [[ $days_until_expiry -gt 7 ]]; then
                HEALTH_RESULTS["ssl_certificate"]="warning"
                log_health_metric "ssl_certificate_days_until_expiry" "${days_until_expiry}" "warning"
                log_health "WARN" "SSL certificate expires soon (${days_until_expiry} days)"
            else
                HEALTH_RESULTS["ssl_certificate"]="unhealthy"
                log_health_metric "ssl_certificate_days_until_expiry" "${days_until_expiry}" "unhealthy"
                log_health "ERROR" "SSL certificate expires very soon (${days_until_expiry} days)"
                OVERALL_HEALTH="unhealthy"
            fi
        else
            HEALTH_RESULTS["ssl_certificate"]="unhealthy"
            log_health_metric "ssl_certificate_validity" "invalid" "unhealthy"
            log_health "ERROR" "SSL certificate is invalid or unreadable"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
}

check_ldap_connectivity() {
    if [[ -n "${LDAP_SERVER}" ]]; then
        log_health "INFO" "Checking LDAP connectivity..."
        
        if python3 -c "
import ldap3
import sys
from urllib.parse import urlparse

try:
    url = urlparse('${LDAP_SERVER}')
    server = ldap3.Server(f'{url.scheme}://{url.hostname}:{url.port or 389}', get_info=ldap3.ALL, connect_timeout=5)
    conn = ldap3.Connection(server, auto_bind=True, authentication=ldap3.ANONYMOUS)
    conn.unbind()
    print('healthy')
except Exception:
    print('unhealthy')
        " 2>/dev/null | grep -q "healthy"; then
            HEALTH_RESULTS["ldap"]="healthy"
            log_health_metric "ldap_connectivity" "healthy" "healthy"
            log_health "INFO" "LDAP connectivity check passed"
        else
            HEALTH_RESULTS["ldap"]="unhealthy"
            log_health_metric "ldap_connectivity" "unhealthy" "unhealthy"
            log_health "ERROR" "LDAP connectivity check failed"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
}

check_resource_utilization() {
    log_health "INFO" "Checking resource utilization..."
    
    # Check memory usage
    local memory_usage
    memory_usage=$(free | awk 'NR==2{printf "%.1f", $3*100/$2}')
    
    if (( $(echo "${memory_usage} < 80" | bc -l) )); then
        HEALTH_RESULTS["memory_usage"]="healthy"
        log_health_metric "memory_usage_percent" "${memory_usage}" "healthy"
    elif (( $(echo "${memory_usage} < 90" | bc -l) )); then
        HEALTH_RESULTS["memory_usage"]="warning"
        log_health_metric "memory_usage_percent" "${memory_usage}" "warning"
        log_health "WARN" "High memory usage: ${memory_usage}%"
    else
        HEALTH_RESULTS["memory_usage"]="unhealthy"
        log_health_metric "memory_usage_percent" "${memory_usage}" "unhealthy"
        log_health "ERROR" "Critical memory usage: ${memory_usage}%"
        OVERALL_HEALTH="unhealthy"
    fi
    
    # Check disk usage
    local disk_usage
    disk_usage=$(df /app | awk 'NR==2{print $5}' | sed 's/%//')
    
    if [[ $disk_usage -lt 80 ]]; then
        HEALTH_RESULTS["disk_usage"]="healthy"
        log_health_metric "disk_usage_percent" "${disk_usage}" "healthy"
    elif [[ $disk_usage -lt 90 ]]; then
        HEALTH_RESULTS["disk_usage"]="warning"
        log_health_metric "disk_usage_percent" "${disk_usage}" "warning"
        log_health "WARN" "High disk usage: ${disk_usage}%"
    else
        HEALTH_RESULTS["disk_usage"]="unhealthy"
        log_health_metric "disk_usage_percent" "${disk_usage}" "unhealthy"
        log_health "ERROR" "Critical disk usage: ${disk_usage}%"
        OVERALL_HEALTH="unhealthy"
    fi
    
    # Check CPU load
    local cpu_load
    cpu_load=$(uptime | awk -F'load average:' '{print $2}' | awk '{print $1}' | sed 's/,//')
    
    log_health_metric "cpu_load_1min" "${cpu_load}" "healthy"
    log_health "INFO" "Current CPU load: ${cpu_load}"
}

check_compliance_systems() {
    log_health "INFO" "Checking enterprise compliance systems..."
    
    # Check audit logging system
    if [[ "${AUDIT_LOGGING}" == "true" ]]; then
        if [[ -d "/app/logs/audit" && -w "/app/logs/audit" ]]; then
            HEALTH_RESULTS["audit_logging"]="healthy"
            log_health_metric "audit_logging_status" "healthy" "healthy"
            log_health "INFO" "Audit logging system is healthy"
        else
            HEALTH_RESULTS["audit_logging"]="unhealthy"
            log_health_metric "audit_logging_status" "unhealthy" "unhealthy"
            log_health "ERROR" "Audit logging system is not accessible"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
    
    # Check SOX compliance requirements
    if [[ "${SOX_COMPLIANCE}" == "true" ]]; then
        local sox_checks=0
        local sox_passed=0
        
        # Check audit trail accessibility
        if [[ -f "/app/logs/audit/audit.log" ]]; then
            ((sox_passed++))
        fi
        ((sox_checks++))
        
        # Check data retention policies
        if [[ -d "/app/logs/audit" ]]; then
            ((sox_passed++))
        fi
        ((sox_checks++))
        
        local sox_compliance_rate=$((sox_passed * 100 / sox_checks))
        
        if [[ $sox_compliance_rate -eq 100 ]]; then
            HEALTH_RESULTS["sox_compliance"]="healthy"
            log_health_metric "sox_compliance_rate" "${sox_compliance_rate}" "healthy"
        else
            HEALTH_RESULTS["sox_compliance"]="unhealthy"
            log_health_metric "sox_compliance_rate" "${sox_compliance_rate}" "unhealthy"
            log_health "ERROR" "SOX compliance requirements not met (${sox_compliance_rate}%)"
            OVERALL_HEALTH="unhealthy"
        fi
    fi
}

check_monitoring_systems() {
    log_health "INFO" "Checking enterprise monitoring systems..."
    
    # Check Prometheus metrics endpoint
    if curl -f -s -k --connect-timeout 5 "${METRICS_ENDPOINT}" > /dev/null 2>&1; then
        HEALTH_RESULTS["prometheus_metrics"]="healthy"
        log_health_metric "prometheus_metrics_status" "healthy" "healthy"
        log_health "INFO" "Prometheus metrics endpoint is healthy"
    else
        HEALTH_RESULTS["prometheus_metrics"]="unhealthy"
        log_health_metric "prometheus_metrics_status" "unhealthy" "unhealthy"
        log_health "ERROR" "Prometheus metrics endpoint is not accessible"
        OVERALL_HEALTH="unhealthy"
    fi
    
    # Check application readiness
    if curl -f -s -k --connect-timeout 5 "${READINESS_ENDPOINT}" > /dev/null 2>&1; then
        HEALTH_RESULTS["application_readiness"]="healthy"
        log_health_metric "application_readiness_status" "healthy" "healthy"
        log_health "INFO" "Application readiness check passed"
    else
        HEALTH_RESULTS["application_readiness"]="unhealthy"
        log_health_metric "application_readiness_status" "unhealthy" "unhealthy"
        log_health "ERROR" "Application readiness check failed"
        OVERALL_HEALTH="unhealthy"
    fi
}

# ============================================================================
# MAIN ENTERPRISE HEALTH CHECK EXECUTION
# ============================================================================

generate_health_report() {
    log_health "INFO" "Generating enterprise health report..."
    
    local health_report="{"
    health_report+="\"timestamp\":\"$(date -Iseconds)\","
    health_report+="\"overall_health\":\"${OVERALL_HEALTH}\","
    health_report+="\"enterprise_mode\":\"${ENTERPRISE_MODE:-true}\","
    health_report+="\"compliance_mode\":\"${COMPLIANCE_MODE:-true}\","
    health_report+="\"checks\":{"
    
    local first=true
    for check in "${!HEALTH_RESULTS[@]}"; do
        if [[ "${first}" == "false" ]]; then
            health_report+=","
        fi
        health_report+="\"${check}\":\"${HEALTH_RESULTS[$check]}\""
        first=false
    done
    
    health_report+="}}"
    
    echo "${health_report}" > "/app/logs/health-report.json"
    log_health "INFO" "Health report generated: ${health_report}"
}

main() {
    log_health "INFO" "Starting enterprise health check..."
    
    # Initialize health check log
    mkdir -p "$(dirname "${HEALTH_LOG}")"
    mkdir -p "/app/logs"
    
    # Execute all health checks
    check_application_health
    check_database_connectivity
    check_ssl_certificate_health
    check_ldap_connectivity
    check_resource_utilization
    check_compliance_systems
    check_monitoring_systems
    
    # Generate final health report
    generate_health_report
    
    log_health "INFO" "Enterprise health check completed - Overall status: ${OVERALL_HEALTH}"
    
    # Exit with appropriate code
    if [[ "${OVERALL_HEALTH}" == "healthy" ]]; then
        exit 0
    else
        exit 1
    fi
}

# Execute main function
main "$@"
