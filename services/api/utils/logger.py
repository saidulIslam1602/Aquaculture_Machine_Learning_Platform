"""
Logging Utilities Module

Structured logging configuration and utilities.

Industry Standards:
    - Structured logging (JSON)
    - Log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    - Context injection
    - Log rotation
    - Performance logging
"""

import logging
import sys
from typing import Dict, Any
from pythonjsonlogger import jsonlogger
from ..core.config import settings


class CustomJsonFormatter(jsonlogger.JsonFormatter):
    """
    Custom JSON Log Formatter

    Formats log records as JSON with additional context.

    Features:
        - ISO timestamp format
        - Request ID tracking
        - User context
        - Performance metrics
        - Exception details
    """

    def add_fields(
        self, log_record: Dict[str, Any], record: logging.LogRecord, message_dict: Dict[str, Any]
    ) -> None:
        """
        Add Custom Fields to Log Record

        Args:
            log_record: Dictionary to populate
            record: Original log record
            message_dict: Message dictionary
        """
        super().add_fields(log_record, record, message_dict)

        # Add timestamp in ISO format
        log_record["timestamp"] = self.formatTime(record, "%Y-%m-%dT%H:%M:%S.%fZ")

        # Add service information
        log_record["service"] = "aquaculture-api"
        log_record["environment"] = settings.ENVIRONMENT

        # Add request context if available
        if hasattr(record, "request_id"):
            log_record["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_record["user_id"] = record.user_id


def setup_logging() -> None:
    """
    Setup Application Logging

    Configures logging with appropriate handlers and formatters.

    Configuration:
        - Console handler with JSON formatting
        - Log level from settings
        - Structured logging for production
        - Human-readable for development

    Example:
        ```python
        from services.api.utils.logger import setup_logging
        setup_logging()
        logger = logging.getLogger(__name__)
        logger.info("Application started")
        ```
    """
    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(settings.LOG_LEVEL)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)

    # Use JSON formatter in production, human-readable in development
    if settings.ENVIRONMENT == "production":
        formatter = CustomJsonFormatter("%(timestamp)s %(level)s %(name)s %(message)s")
    else:
        formatter = logging.Formatter(
            "%(asctime)s - %(name)s - %(levelname)s - %(message)s", datefmt="%Y-%m-%d %H:%M:%S"
        )

    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Set specific log levels for libraries
    logging.getLogger("uvicorn").setLevel(logging.INFO)
    logging.getLogger("sqlalchemy.engine").setLevel(logging.WARNING)
    logging.getLogger("celery").setLevel(logging.INFO)

    logging.info(
        f"Logging configured: level={settings.LOG_LEVEL}, " f"environment={settings.ENVIRONMENT}"
    )


def get_logger(name: str) -> logging.Logger:
    """
    Get Logger Instance

    Returns configured logger for a module.

    Args:
        name: Logger name (usually __name__)

    Returns:
        logging.Logger: Configured logger

    Example:
        ```python
        from services.api.utils.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Processing started")
        ```
    """
    return logging.getLogger(name)
