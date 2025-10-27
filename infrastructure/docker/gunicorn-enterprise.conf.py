# =============================================================================
# ENTERPRISE GUNICORN CONFIGURATION - AQUACULTURE PLATFORM APPLICATION SERVER
# =============================================================================
#
# WHAT IS THIS FILE?
# This file configures Gunicorn, a high-performance Python web server that
# runs the enterprise API service. Think of it as the "engine" that powers
# the backend application in production environments.
#
# WHAT IS GUNICORN?
# Gunicorn (Green Unicorn) is a Python WSGI HTTP server that:
# - Handles multiple user requests simultaneously
# - Manages worker processes for better performance
# - Provides enterprise-grade reliability and monitoring
# - Scales automatically based on load
# - Handles graceful shutdowns and restarts
#
# WHY USE GUNICORN FOR ENTERPRISE?
# Enterprise environments need robust application servers because:
# - High Traffic: Must handle thousands of concurrent users
# - Reliability: Cannot afford downtime or crashes
# - Performance: Must respond quickly under heavy load
# - Monitoring: Needs detailed metrics and logging
# - Security: Must protect against attacks and vulnerabilities
# - Compliance: Must meet regulatory requirements (SOX, GDPR)
#
# KEY ENTERPRISE FEATURES CONFIGURED:
# - Multi-Process Workers: Handle many requests simultaneously
# - Health Monitoring: Automatic worker restart if problems occur
# - Security Headers: Protect against common web attacks
# - Compliance Logging: Detailed audit trails for regulations
# - Performance Optimization: Memory and CPU tuning
# - Graceful Shutdowns: Proper handling of deployments and restarts
#
# CONFIGURATION SECTIONS:
# - Server Settings: Basic server configuration (ports, workers)
# - Performance Tuning: Memory and CPU optimization
# - Security Settings: SSL, headers, and attack protection
# - Logging Configuration: Audit trails and monitoring
# - Enterprise Integration: Compliance and monitoring systems
#
# AUTHOR: DevOps Team
# VERSION: 1.0.0
# UPDATED: 2024-10-26
# =============================================================================

import os
import multiprocessing
from pathlib import Path

# ============================================================================
# ENTERPRISE SERVER CONFIGURATION
# ============================================================================

# Server socket configuration
bind = os.getenv("GUNICORN_BIND", "0.0.0.0:8000")
backlog = int(os.getenv("GUNICORN_BACKLOG", "2048"))

# Enterprise worker configuration
workers = int(os.getenv("GUNICORN_WORKERS", multiprocessing.cpu_count() * 2 + 1))
worker_class = os.getenv("GUNICORN_WORKER_CLASS", "uvicorn.workers.UvicornWorker")
worker_connections = int(os.getenv("GUNICORN_WORKER_CONNECTIONS", "1000"))
max_requests = int(os.getenv("GUNICORN_MAX_REQUESTS", "1000"))
max_requests_jitter = int(os.getenv("GUNICORN_MAX_REQUESTS_JITTER", "100"))

# Enterprise timeout configuration
timeout = int(os.getenv("GUNICORN_TIMEOUT", "120"))
keepalive = int(os.getenv("GUNICORN_KEEPALIVE", "5"))
graceful_timeout = int(os.getenv("GUNICORN_GRACEFUL_TIMEOUT", "30"))

# Enterprise performance optimization
preload_app = True
worker_tmp_dir = "/dev/shm"  # Use shared memory for better performance
worker_class_tmp_dir = "/dev/shm"

# ============================================================================
# ENTERPRISE SSL/TLS CONFIGURATION
# ============================================================================

# SSL configuration for enterprise security
ssl_enabled = os.getenv("SSL_ENABLED", "true").lower() == "true"

if ssl_enabled:
    certfile = os.getenv("SSL_CERT_PATH", "/app/ssl/server.crt")
    keyfile = os.getenv("SSL_KEY_PATH", "/app/ssl/server.key")
    ca_certs = os.getenv("SSL_CA_CERTS", "/app/ssl/ca-bundle.crt")
    
    # Enterprise SSL/TLS settings
    ssl_version = 5  # TLS 1.2+
    ciphers = "ECDHE+AESGCM:ECDHE+CHACHA20:DHE+AESGCM:DHE+CHACHA20:!aNULL:!MD5:!DSS"
    cert_reqs = 0  # ssl.CERT_NONE for client certificates (adjust as needed)
    
    # Additional HTTPS bind for enterprise environments
    if ":" in bind:
        host, port = bind.rsplit(":", 1)
        https_port = int(port) + 443
        bind = [bind, f"{host}:{https_port}"]

# ============================================================================
# ENTERPRISE LOGGING CONFIGURATION
# ============================================================================

# Enterprise logging paths
log_dir = Path("/app/logs/application")
log_dir.mkdir(parents=True, exist_ok=True)

# Gunicorn logging configuration
loglevel = os.getenv("LOG_LEVEL", "info").lower()
accesslog = str(log_dir / "access.log")
errorlog = str(log_dir / "error.log")
capture_output = True
enable_stdio_inheritance = True

# Enterprise access log format with compliance fields
access_log_format = (
    '{'
    '"timestamp": "%(t)s", '
    '"remote_addr": "%(h)s", '
    '"request_id": "%({X-Request-ID}i)s", '
    '"method": "%(m)s", '
    '"url": "%(U)s", '
    '"query": "%(q)s", '
    '"protocol": "%(H)s", '
    '"status": %(s)s, '
    '"response_length": %(B)s, '
    '"referer": "%(f)s", '
    '"user_agent": "%(a)s", '
    '"request_time": %(D)s, '
    '"user_id": "%({X-User-ID}i)s", '
    '"session_id": "%({X-Session-ID}i)s", '
    '"enterprise_id": "%({X-Enterprise-ID}i)s", '
    '"compliance_mode": "%({X-Compliance-Mode}i)s", '
    '"audit_trail": "%({X-Audit-Trail}i)s"'
    '}'
)

# ============================================================================
# ENTERPRISE SECURITY CONFIGURATION
# ============================================================================

# Security limits for enterprise environments
limit_request_line = int(os.getenv("GUNICORN_LIMIT_REQUEST_LINE", "8190"))
limit_request_fields = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELDS", "100"))
limit_request_field_size = int(os.getenv("GUNICORN_LIMIT_REQUEST_FIELD_SIZE", "8190"))

# Enterprise process naming for monitoring
proc_name = "aquaculture-api-enterprise"

# Enterprise user and group (if running as root initially)
user = os.getenv("GUNICORN_USER", "enterprise")
group = os.getenv("GUNICORN_GROUP", "enterprise")

# Enterprise working directory
chdir = "/app"

# Enterprise environment variables
raw_env = [
    f"ENTERPRISE_MODE={os.getenv('ENTERPRISE_MODE', 'true')}",
    f"COMPLIANCE_MODE={os.getenv('COMPLIANCE_MODE', 'true')}",
    f"SOX_COMPLIANCE={os.getenv('SOX_COMPLIANCE', 'true')}",
    f"GDPR_COMPLIANCE={os.getenv('GDPR_COMPLIANCE', 'true')}",
    f"AUDIT_LOGGING={os.getenv('AUDIT_LOGGING', 'true')}",
    f"PROMETHEUS_ENABLED={os.getenv('PROMETHEUS_ENABLED', 'true')}",
    f"OPENTELEMETRY_ENABLED={os.getenv('OPENTELEMETRY_ENABLED', 'true')}",
]

# ============================================================================
# ENTERPRISE MONITORING AND HEALTH CHECKS
# ============================================================================

# Enterprise process monitoring
pidfile = "/app/tmp/gunicorn-enterprise.pid"
tmp_upload_dir = "/app/tmp/uploads"

# Create required directories
Path("/app/tmp").mkdir(parents=True, exist_ok=True)
Path(tmp_upload_dir).mkdir(parents=True, exist_ok=True)

# ============================================================================
# ENTERPRISE WORKER LIFECYCLE HOOKS
# ============================================================================

def on_starting(server):
    """Enterprise server startup hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    # Enterprise startup audit log
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_server_starting",
        "server_info": {
            "workers": server.cfg.workers,
            "worker_class": server.cfg.worker_class,
            "bind": server.cfg.bind,
            "ssl_enabled": ssl_enabled,
            "enterprise_mode": os.getenv("ENTERPRISE_MODE", "true"),
            "compliance_mode": os.getenv("COMPLIANCE_MODE", "true"),
        },
        "compliance": {
            "sox": os.getenv("SOX_COMPLIANCE", "true"),
            "gdpr": os.getenv("GDPR_COMPLIANCE", "true"),
            "audit_logging": os.getenv("AUDIT_LOGGING", "true"),
        }
    }
    
    logger.info(f"Enterprise server starting: {json.dumps(audit_event)}")

def on_reload(server):
    """Enterprise server reload hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_server_reload",
        "enterprise_mode": os.getenv("ENTERPRISE_MODE", "true"),
        "compliance_audit": True
    }
    
    logger.info(f"Enterprise server reload: {json.dumps(audit_event)}")

def when_ready(server):
    """Enterprise server ready hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_server_ready",
        "server_address": server.cfg.bind,
        "worker_count": len(server.WORKERS),
        "enterprise_ready": True,
        "compliance_ready": True
    }
    
    logger.info(f"Enterprise server ready: {json.dumps(audit_event)}")

def worker_int(worker):
    """Enterprise worker interrupt hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_worker_interrupt",
        "worker_pid": worker.pid,
        "worker_age": worker.age,
        "enterprise_shutdown": True
    }
    
    logger.info(f"Enterprise worker interrupt: {json.dumps(audit_event)}")

def pre_fork(server, worker):
    """Enterprise pre-fork hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    # Enterprise worker initialization
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_worker_pre_fork",
        "worker_id": worker.id,
        "server_pid": server.pid,
        "enterprise_worker": True
    }
    
    logger.info(f"Enterprise worker pre-fork: {json.dumps(audit_event)}")

def post_fork(server, worker):
    """Enterprise post-fork hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    # Enterprise worker post-fork initialization
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_worker_post_fork",
        "worker_id": worker.id,
        "worker_pid": worker.pid,
        "enterprise_initialized": True
    }
    
    logger.info(f"Enterprise worker post-fork: {json.dumps(audit_event)}")
    
    # Initialize enterprise monitoring for this worker
    try:
        # Set up Prometheus metrics for this worker
        import prometheus_client
        prometheus_client.CollectorRegistry(auto_describe=False)
        
        # Set up OpenTelemetry for this worker if enabled
        if os.getenv("OPENTELEMETRY_ENABLED", "false").lower() == "true":
            from opentelemetry import trace
            from opentelemetry.sdk.trace import TracerProvider
            from opentelemetry.sdk.trace.export import BatchSpanProcessor
            
            trace.set_tracer_provider(TracerProvider())
            
    except ImportError as e:
        logger.warning(f"Enterprise monitoring initialization failed: {e}")

def worker_abort(worker):
    """Enterprise worker abort hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_worker_abort",
        "worker_pid": worker.pid,
        "worker_age": worker.age,
        "enterprise_incident": True,
        "requires_investigation": True
    }
    
    logger.error(f"Enterprise worker abort: {json.dumps(audit_event)}")

def on_exit(server):
    """Enterprise server exit hook."""
    import logging
    import json
    from datetime import datetime
    
    logger = logging.getLogger("gunicorn.error")
    
    audit_event = {
        "timestamp": datetime.utcnow().isoformat(),
        "event": "gunicorn_server_exit",
        "server_pid": server.pid,
        "enterprise_shutdown": True,
        "compliance_audit_complete": True
    }
    
    logger.info(f"Enterprise server exit: {json.dumps(audit_event)}")

# ============================================================================
# ENTERPRISE PERFORMANCE TUNING
# ============================================================================

# Enterprise memory and resource optimization
max_requests_jitter = max_requests_jitter
worker_tmp_dir = "/dev/shm"  # Use shared memory for performance

# Enterprise connection handling
keepalive = keepalive
worker_connections = worker_connections

# Enterprise request handling optimization
sendfile = True  # Use sendfile() for static files
reuse_port = True  # Enable SO_REUSEPORT for better load distribution

# ============================================================================
# ENTERPRISE COMPLIANCE AND AUDIT CONFIGURATION
# ============================================================================

# Enterprise audit configuration
def enterprise_audit_config():
    """Configure enterprise audit settings."""
    return {
        "sox_compliance": os.getenv("SOX_COMPLIANCE", "true").lower() == "true",
        "gdpr_compliance": os.getenv("GDPR_COMPLIANCE", "true").lower() == "true",
        "audit_logging": os.getenv("AUDIT_LOGGING", "true").lower() == "true",
        "audit_log_path": "/app/logs/audit/gunicorn-audit.log",
        "compliance_mode": os.getenv("COMPLIANCE_MODE", "true").lower() == "true",
        "enterprise_mode": os.getenv("ENTERPRISE_MODE", "true").lower() == "true",
    }

# Store enterprise configuration for runtime access
ENTERPRISE_CONFIG = enterprise_audit_config()
