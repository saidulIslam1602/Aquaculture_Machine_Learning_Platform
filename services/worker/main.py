#!/usr/bin/env python3
"""
Worker Service Main Module - Aquaculture ML Platform

This module serves as the entry point for the Celery worker service that handles
background tasks, data processing, and asynchronous operations for the
Aquaculture Machine Learning Platform.

Key Responsibilities:
- Background task processing with Celery
- Data pipeline orchestration
- ML model training and inference tasks
- Kafka message consumption and processing
- Database maintenance and cleanup operations
- Scheduled task execution

Architecture:
The worker service operates as a distributed task queue using Celery with Redis
as the message broker. It processes tasks asynchronously to ensure the main API
service remains responsive while handling compute-intensive operations.

Author: Data Engineering Team
Version: 2.1.0
"""

import logging
import sys
import os
from typing import Dict, Any

# Add the project root to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from services.worker.celery_app import celery_app
from services.worker.tasks.data_tasks import process_sensor_data, cleanup_old_data
from services.worker.tasks.ml_tasks import train_model, batch_inference
from services.worker.consumers.kafka_consumer import start_kafka_consumer

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout),
        logging.FileHandler('/tmp/worker.log') if os.path.exists('/tmp') else logging.NullHandler()
    ]
)

logger = logging.getLogger(__name__)


def setup_worker_environment() -> Dict[str, Any]:
    """
    Set up the worker environment and validate configuration.
    
    Returns:
        Dict containing worker configuration and status
    """
    config = {
        'celery_broker': os.getenv('CELERY_BROKER_URL', 'redis://localhost:6379/0'),
        'database_url': os.getenv('DATABASE_URL', 'postgresql://localhost/agricultural_iot'),
        'kafka_servers': os.getenv('KAFKA_BOOTSTRAP_SERVERS', 'localhost:9092'),
        'worker_concurrency': int(os.getenv('WORKER_CONCURRENCY', '4')),
        'log_level': os.getenv('LOG_LEVEL', 'INFO'),
    }
    
    logger.info("Worker environment configuration:")
    for key, value in config.items():
        # Don't log sensitive information like database URLs
        if 'url' in key.lower() or 'password' in key.lower():
            logger.info(f"  {key}: [CONFIGURED]")
        else:
            logger.info(f"  {key}: {value}")
    
    return config


def start_worker():
    """
    Start the Celery worker with proper configuration.
    
    This function initializes the worker service and starts processing tasks
    from the configured message broker (Redis).
    """
    logger.info("Starting Aquaculture ML Platform Worker Service...")
    
    # Setup environment
    config = setup_worker_environment()
    
    # Configure Celery worker options
    worker_options = [
        'worker',
        '--app=services.worker.celery_app:celery_app',
        f'--concurrency={config["worker_concurrency"]}',
        f'--loglevel={config["log_level"]}',
        '--without-gossip',
        '--without-mingle',
        '--without-heartbeat',
    ]
    
    logger.info(f"Starting Celery worker with options: {' '.join(worker_options)}")
    
    try:
        # Start the Celery worker
        celery_app.start(worker_options)
    except KeyboardInterrupt:
        logger.info("Worker service interrupted by user")
    except Exception as e:
        logger.error(f"Worker service failed to start: {e}")
        sys.exit(1)


def health_check() -> bool:
    """
    Perform a health check of the worker service.
    
    Returns:
        True if the worker is healthy, False otherwise
    """
    try:
        # Check Celery connection
        inspect = celery_app.control.inspect()
        stats = inspect.stats()
        
        if stats:
            logger.info("Worker health check: HEALTHY")
            return True
        else:
            logger.warning("Worker health check: No active workers found")
            return False
            
    except Exception as e:
        logger.error(f"Worker health check failed: {e}")
        return False


if __name__ == "__main__":
    """
    Main entry point for the worker service.
    
    Supports different modes of operation:
    - Default: Start the Celery worker
    - health: Perform health check and exit
    - version: Display version information
    """
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        command = sys.argv[1].lower()
        
        if command == "health":
            # Health check mode
            if health_check():
                print("Worker service is healthy")
                sys.exit(0)
            else:
                print("Worker service is unhealthy")
                sys.exit(1)
                
        elif command == "version":
            # Version information mode
            from services.worker import __version__
            print(f"Aquaculture ML Platform Worker Service v{__version__}")
            sys.exit(0)
            
        elif command == "help":
            # Help information
            print("Aquaculture ML Platform Worker Service")
            print("Usage:")
            print("  python -m services.worker.main        # Start worker service")
            print("  python -m services.worker.main health  # Health check")
            print("  python -m services.worker.main version # Version info")
            print("  python -m services.worker.main help    # This help")
            sys.exit(0)
    
    # Default: Start the worker service
    start_worker()
