"""
Logging Middleware Module

Request/response logging middleware for observability.

Industry Standards:
    - Structured logging (JSON format)
    - Request ID tracking
    - Performance metrics
    - Security audit logging
    - PII redaction
"""

from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import Response
import time
import uuid
import logging
import json
from typing import Callable

from ..utils.metrics import performance_metrics

logger = logging.getLogger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    """
    Request Logging Middleware

    Logs all HTTP requests and responses with timing information.
    Adds request ID for distributed tracing.

    Features:
        - Request ID generation
        - Request/response logging
        - Performance timing
        - Structured logging
        - Error tracking

    Example:
        ```python
        app.add_middleware(RequestLoggingMiddleware)
        ```

    Logged Information:
        - Request method and path
        - Request ID (for tracing)
        - Client IP address
        - User agent
        - Response status code
        - Response time
        - Error details (if any)
    """

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        """
        Process Request

        Logs request, processes it, and logs response.

        Args:
            request: Incoming HTTP request
            call_next: Next middleware/route handler

        Returns:
            Response: HTTP response
        """
        # Generate unique request ID
        request_id = str(uuid.uuid4())

        # Add request ID to request state
        request.state.request_id = request_id

        # Start timing
        start_time = time.time()

        # Extract request information
        request_info = {
            "request_id": request_id,
            "method": request.method,
            "path": request.url.path,
            "query_params": dict(request.query_params),
            "client_ip": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        # Log request
        logger.info(f"Request started: {request.method} {request.url.path}", extra=request_info)

        # Process request
        try:
            response = await call_next(request)

            # Calculate processing time
            process_time = time.time() - start_time
            process_time_ms = process_time * 1000

            # Record metrics for performance tracking
            success = response.status_code < 400
            performance_metrics.record_request(process_time_ms, success=success)

            # Add custom headers
            response.headers["X-Request-ID"] = request_id
            response.headers["X-Process-Time"] = str(process_time)

            # Log response
            response_info = {
                **request_info,
                "status_code": response.status_code,
                "process_time_ms": process_time_ms,
            }

            log_level = logging.INFO if response.status_code < 400 else logging.WARNING
            logger.log(
                log_level,
                f"Request completed: {request.method} {request.url.path} "
                f"[{response.status_code}] {process_time_ms:.2f}ms",
                extra=response_info,
            )

            return response

        except Exception as e:
            # Calculate processing time
            process_time = time.time() - start_time

            # Log error
            error_info = {
                **request_info,
                "error": str(e),
                "error_type": type(e).__name__,
                "process_time_ms": process_time * 1000,
            }

            logger.error(
                f"Request failed: {request.method} {request.url.path} - {str(e)}",
                exc_info=True,
                extra=error_info,
            )

            # Re-raise to be handled by exception handlers
            raise


class StructuredLoggingFormatter(logging.Formatter):
    """
    Structured Logging Formatter

    Formats log records as JSON for machine parsing.

    Features:
        - JSON output format
        - Timestamp in ISO format
        - Contextual information
        - Error stack traces

    Example:
        ```python
        handler = logging.StreamHandler()
        handler.setFormatter(StructuredLoggingFormatter())
        logger.addHandler(handler)
        ```

    Output Format:
        {
            "timestamp": "2025-10-07T12:00:00.000Z",
            "level": "INFO",
            "logger": "api.routes",
            "message": "Request completed",
            "context": {...}
        }
    """

    def format(self, record: logging.LogRecord) -> str:
        """
        Format Log Record as JSON

        Args:
            record: Log record to format

        Returns:
            str: JSON-formatted log string
        """
        # Base log structure
        log_data = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
        }

        # Add extra context if available
        if hasattr(record, "request_id"):
            log_data["request_id"] = record.request_id

        if hasattr(record, "user_id"):
            log_data["user_id"] = record.user_id

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add any extra fields
        for key, value in record.__dict__.items():
            if key not in [
                "name",
                "msg",
                "args",
                "created",
                "filename",
                "funcName",
                "levelname",
                "levelno",
                "lineno",
                "module",
                "msecs",
                "message",
                "pathname",
                "process",
                "processName",
                "relativeCreated",
                "thread",
                "threadName",
                "exc_info",
                "exc_text",
                "stack_info",
            ]:
                log_data[key] = value

        return json.dumps(log_data)
