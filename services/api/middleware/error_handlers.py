"""
Error Handlers Module

Custom exception handlers for FastAPI application.

Industry Standards:
    - Consistent error response format
    - Proper HTTP status codes
    - Error logging with context
    - User-friendly error messages
    - Security (no sensitive data in errors)
"""

import logging
from datetime import datetime

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from sqlalchemy.exc import SQLAlchemyError

logger = logging.getLogger(__name__)


class APIException(Exception):
    """
    Base API Exception

    Custom exception class for API-specific errors.

    Attributes:
        status_code: HTTP status code
        detail: Error detail message
        headers: Optional response headers
    """

    def __init__(self, status_code: int, detail: str, headers: dict = None):
        self.status_code = status_code
        self.detail = detail
        self.headers = headers
        super().__init__(detail)


async def api_exception_handler(request: Request, exc: APIException) -> JSONResponse:
    """
    API Exception Handler

    Handles custom API exceptions with consistent format.

    Args:
        request: FastAPI request object
        exc: API exception

    Returns:
        JSONResponse: Formatted error response
    """
    logger.warning(
        f"API Exception: {exc.detail}",
        extra={
            "status_code": exc.status_code,
            "path": request.url.path,
            "method": request.method,
        },
    )

    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "type": "APIException",
                "message": exc.detail,
                "status_code": exc.status_code,
                "path": request.url.path,
                "timestamp": str(
                    logging.Formatter().formatTime(
                        logging.LogRecord("", 0, "", 0, "", (), None)
                    )
                ),
            }
        },
        headers=exc.headers,
    )


async def validation_exception_handler(
    request: Request, exc: RequestValidationError
) -> JSONResponse:
    """
    Validation Exception Handler

    Handles Pydantic validation errors with detailed information.

    Args:
        request: FastAPI request object
        exc: Validation error

    Returns:
        JSONResponse: Formatted validation error response

    Note:
        Provides detailed field-level validation errors
        for better client-side error handling.
    """
    logger.warning(
        f"Validation Error: {exc.errors()}",
        extra={"path": request.url.path, "method": request.method, "body": exc.body},
    )

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "type": "ValidationError",
                "message": "Request validation failed",
                "details": exc.errors(),
                "path": request.url.path,
                "timestamp": str(datetime.utcnow().isoformat()),
            }
        },
    )


async def database_exception_handler(
    request: Request, exc: SQLAlchemyError
) -> JSONResponse:
    """
    Database Exception Handler

    Handles SQLAlchemy database errors.

    Args:
        request: FastAPI request object
        exc: Database error

    Returns:
        JSONResponse: Formatted error response

    Security Note:
        Does not expose database details to clients.
        Logs full error for debugging.
    """
    logger.error(
        f"Database Error: {exc}",
        exc_info=True,
        extra={"path": request.url.path, "method": request.method},
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "DatabaseError",
                "message": "Database operation failed. Please try again.",
                "path": request.url.path,
                "timestamp": str(datetime.utcnow().isoformat()),
            }
        },
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Generic Exception Handler

    Catches all unhandled exceptions.

    Args:
        request: FastAPI request object
        exc: Unhandled exception

    Returns:
        JSONResponse: Generic error response

    Security Note:
        Returns generic message to clients.
        Logs full exception for debugging.
    """
    logger.error(
        f"Unhandled Exception: {exc}",
        exc_info=True,
        extra={
            "path": request.url.path,
            "method": request.method,
            "exception_type": type(exc).__name__,
        },
    )

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "type": "InternalServerError",
                "message": "An unexpected error occurred. Please try again later.",
                "path": request.url.path,
                "timestamp": str(datetime.utcnow().isoformat()),
            }
        },
    )
