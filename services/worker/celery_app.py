"""
Celery Application Configuration

Configures Celery for distributed task processing with production-grade settings.

Industry Standards:
    - Task routing for workload distribution
    - Result backend for task state tracking
    - Task serialization with JSON
    - Automatic retry with exponential backoff
    - Task time limits and soft timeouts
    - Worker prefetch optimization
    - Task result expiration

Architecture:
    - Broker: Redis (message queue)
    - Backend: Redis (result storage)
    - Serializer: JSON (security and compatibility)
    - Workers: Multiple processes for parallelism
"""

from celery import Celery
from celery.signals import task_prerun, task_postrun, task_failure
from kombu import Queue, Exchange
import logging
from typing import Dict, Any
import time

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Celery application instance
# Uses Redis as both broker and result backend for simplicity
celery_app = Celery(
    "aquaculture_worker",
    broker="redis://redis:6379/1",  # Separate DB from cache
    backend="redis://redis:6379/2",  # Separate DB for results
    include=[
        "services.worker.tasks.ml_tasks",
        "services.worker.tasks.data_tasks",
        "services.worker.tasks.batch_tasks",
    ],
)

# Celery Configuration
# Following best practices for production deployments
celery_app.conf.update(
    # Task Execution Settings
    task_serializer="json",  # JSON for security (no pickle)
    accept_content=["json"],  # Only accept JSON
    result_serializer="json",
    timezone="UTC",  # Always use UTC for consistency
    enable_utc=True,
    # Task Result Settings
    result_expires=3600,  # Results expire after 1 hour
    result_backend_transport_options={
        "master_name": "mymaster",  # For Redis Sentinel
        "visibility_timeout": 3600,
    },
    # Task Routing Configuration
    # Route different task types to different queues
    task_routes={
        "services.worker.tasks.ml_tasks.*": {
            "queue": "ml_inference",
            "routing_key": "ml.inference",
        },
        "services.worker.tasks.data_tasks.*": {
            "queue": "data_processing",
            "routing_key": "data.processing",
        },
        "services.worker.tasks.batch_tasks.*": {"queue": "batch_jobs", "routing_key": "batch.jobs"},
    },
    # Task Queue Definitions
    # Define queues with specific priorities and settings
    task_queues=(
        Queue(
            "ml_inference",
            Exchange("ml_inference", type="topic"),
            routing_key="ml.inference",
            queue_arguments={"x-max-priority": 10},  # Enable priority
        ),
        Queue(
            "data_processing",
            Exchange("data_processing", type="topic"),
            routing_key="data.processing",
            queue_arguments={"x-max-priority": 5},
        ),
        Queue(
            "batch_jobs",
            Exchange("batch_jobs", type="topic"),
            routing_key="batch.jobs",
            queue_arguments={"x-max-priority": 1},
        ),
    ),
    # Worker Settings
    worker_prefetch_multiplier=4,  # Number of tasks to prefetch per worker
    worker_max_tasks_per_child=1000,  # Restart worker after N tasks (prevent memory leaks)
    worker_disable_rate_limits=False,  # Enable rate limiting
    # Task Execution Limits
    task_time_limit=3600,  # Hard time limit: 1 hour
    task_soft_time_limit=3300,  # Soft time limit: 55 minutes
    task_acks_late=True,  # Acknowledge task after completion (safer)
    task_reject_on_worker_lost=True,  # Reject task if worker dies
    # Task Retry Settings
    task_autoretry_for=(Exception,),  # Auto-retry on any exception
    task_retry_backoff=True,  # Exponential backoff
    task_retry_backoff_max=600,  # Max retry delay: 10 minutes
    task_retry_jitter=True,  # Add random jitter to prevent thundering herd
    task_max_retries=3,  # Maximum retry attempts
    # Monitoring and Logging
    worker_send_task_events=True,  # Send task events for monitoring
    task_send_sent_event=True,  # Track task sent events
    task_track_started=True,  # Track when tasks start
    task_ignore_result=False,  # Store all results
    # Performance Optimization
    broker_pool_limit=10,  # Connection pool size
    broker_connection_retry=True,  # Retry broker connection
    broker_connection_retry_on_startup=True,
    broker_connection_max_retries=10,
    # Result Backend Optimization
    result_backend_max_retries=10,
    result_backend_retry_on_timeout=True,
    # Beat Scheduler Settings (for periodic tasks)
    beat_schedule={
        "cleanup-expired-results": {
            "task": "services.worker.tasks.data_tasks.cleanup_expired_results",
            "schedule": 3600.0,  # Run every hour
        },
        "health-check": {
            "task": "services.worker.tasks.data_tasks.worker_health_check",
            "schedule": 300.0,  # Run every 5 minutes
        },
    },
)


# Task Event Handlers
# Monitor task lifecycle for metrics and debugging


@task_prerun.connect
def task_prerun_handler(
    sender=None, task_id=None, task=None, args=None, kwargs=None, **extra_kwargs
):
    """
    Task Pre-run Handler

    Called before task execution. Used for logging and metrics.

    Args:
        sender: Task class
        task_id: Unique task ID
        task: Task instance
        args: Task positional arguments
        kwargs: Task keyword arguments
    """
    logger.info(
        f"Task started: {task.name} [ID: {task_id}]",
        extra={"task_id": task_id, "task_name": task.name, "args": args, "kwargs": kwargs},
    )


@task_postrun.connect
def task_postrun_handler(
    sender=None,
    task_id=None,
    task=None,
    args=None,
    kwargs=None,
    retval=None,
    state=None,
    **extra_kwargs,
):
    """
    Task Post-run Handler

    Called after successful task execution. Used for cleanup and metrics.

    Args:
        sender: Task class
        task_id: Unique task ID
        task: Task instance
        args: Task positional arguments
        kwargs: Task keyword arguments
        retval: Task return value
        state: Task final state
    """
    logger.info(
        f"Task completed: {task.name} [ID: {task_id}] State: {state}",
        extra={"task_id": task_id, "task_name": task.name, "state": state},
    )


@task_failure.connect
def task_failure_handler(
    sender=None,
    task_id=None,
    exception=None,
    args=None,
    kwargs=None,
    traceback=None,
    einfo=None,
    **extra_kwargs,
):
    """
    Task Failure Handler

    Called when task fails. Used for error logging and alerting.

    Args:
        sender: Task class
        task_id: Unique task ID
        exception: Exception that caused failure
        args: Task positional arguments
        kwargs: Task keyword arguments
        traceback: Exception traceback
        einfo: Exception info object
    """
    logger.error(
        f"Task failed: {sender.name} [ID: {task_id}] Error: {exception}",
        extra={
            "task_id": task_id,
            "task_name": sender.name,
            "exception": str(exception),
            "traceback": str(traceback),
        },
        exc_info=einfo,
    )


def get_celery_app() -> Celery:
    """
    Get Celery Application Instance

    Returns configured Celery application for task execution.

    Returns:
        Celery: Configured Celery application

    Example:
        >>> from services.worker.celery_app import get_celery_app
        >>> app = get_celery_app()
        >>> result = app.send_task('my_task', args=[1, 2])
    """
    return celery_app


def get_worker_stats() -> Dict[str, Any]:
    """
    Get Worker Statistics

    Returns comprehensive worker statistics and health information.

    Returns:
        Dict: Worker statistics including active tasks, queues, etc.

    Example:
        >>> stats = get_worker_stats()
        >>> print(f"Active tasks: {stats['active_tasks']}")
    """
    inspect = celery_app.control.inspect()

    stats = {
        "active_tasks": inspect.active(),
        "scheduled_tasks": inspect.scheduled(),
        "reserved_tasks": inspect.reserved(),
        "registered_tasks": inspect.registered(),
        "stats": inspect.stats(),
        "active_queues": inspect.active_queues(),
    }

    return stats
