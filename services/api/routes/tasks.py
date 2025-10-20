"""
Task Management API Routes

REST API endpoints for managing and monitoring Celery tasks.

Industry Standards:
    - RESTful resource design
    - Proper HTTP status codes
    - Comprehensive error handling
    - Task state management
    - Progress tracking
"""

import logging
from datetime import datetime
from typing import Any, Dict, List, Optional

from fastapi import APIRouter, Depends, HTTPException, status
from pydantic import BaseModel, Field

from ..core.security import get_current_active_user

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/tasks", tags=["Task Management"])


class TaskStatusResponse(BaseModel):
    """
    Task Status Response Schema

    Schema for task status information.

    Attributes:
        task_id: Unique task identifier
        status: Current task status
        result: Task result (if completed)
        progress: Task progress information
        created_at: Task creation timestamp
        completed_at: Task completion timestamp
    """

    task_id: str = Field(..., description="Unique task ID")
    status: str = Field(
        ..., description="Task status: PENDING, STARTED, SUCCESS, FAILURE, RETRY"
    )
    result: Optional[Dict[str, Any]] = Field(None, description="Task result")
    progress: Optional[Dict[str, Any]] = Field(None, description="Progress information")
    error: Optional[str] = Field(None, description="Error message if failed")
    created_at: Optional[datetime] = Field(None, description="Task creation time")
    completed_at: Optional[datetime] = Field(None, description="Task completion time")

    class Config:
        schema_extra = {
            "example": {
                "task_id": "a1b2c3d4-e5f6-7890-abcd-ef1234567890",
                "status": "SUCCESS",
                "result": {"species": "Tilapia", "confidence": 0.95},
                "progress": {"current": 100, "total": 100},
                "created_at": "2025-10-07T12:00:00Z",
                "completed_at": "2025-10-07T12:00:05Z",
            }
        }


class TaskListResponse(BaseModel):
    """Task List Response Schema"""

    tasks: List[TaskStatusResponse]
    total: int
    page: int
    page_size: int


@router.get(
    "/{task_id}",
    response_model=TaskStatusResponse,
    summary="Get Task Status",
    description="Retrieves status and result of a specific task.",
)
async def get_task_status(
    task_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> TaskStatusResponse:
    """
    Get Task Status

    Retrieves current status and result of a Celery task.

    Args:
        task_id: Unique task identifier
        current_user: Authenticated user

    Returns:
        TaskStatusResponse: Task status information

    Raises:
        HTTPException: 404 if task not found

    Example:
        ```python
        response = requests.get(
            f'http://localhost:8000/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        status = response.json()
        print(f"Status: {status['status']}")
        ```

    Task States:
        - PENDING: Task waiting to be executed
        - STARTED: Task execution started
        - SUCCESS: Task completed successfully
        - FAILURE: Task failed with error
        - RETRY: Task is being retried
        - REVOKED: Task was cancelled
    """
    try:
        # TODO: Get task status from Celery
        # from celery.result import AsyncResult
        # task = AsyncResult(task_id)

        # Mock response for now
        response = TaskStatusResponse(
            task_id=task_id,
            status="SUCCESS",
            result={"species": "Tilapia", "confidence": 0.95},
            progress={"current": 100, "total": 100},
            created_at=datetime.utcnow(),
            completed_at=datetime.utcnow(),
        )

        logger.info(f"Task status retrieved: {task_id}")

        return response

    except Exception as e:
        logger.error(f"Failed to get task status: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail=f"Task {task_id} not found"
        )


@router.delete(
    "/{task_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Cancel Task",
    description="Cancels a running or pending task.",
)
async def cancel_task(
    task_id: str, current_user: Dict[str, Any] = Depends(get_current_active_user)
) -> None:
    """
    Cancel Task

    Attempts to cancel a running or pending Celery task.

    Args:
        task_id: Task to cancel
        current_user: Authenticated user

    Raises:
        HTTPException: 404 if task not found
        HTTPException: 400 if task cannot be cancelled

    Example:
        ```python
        response = requests.delete(
            f'http://localhost:8000/api/v1/tasks/{task_id}',
            headers={'Authorization': f'Bearer {token}'}
        )
        ```

    Note:
        - Only PENDING and STARTED tasks can be cancelled
        - Completed tasks cannot be cancelled
        - Cancellation is best-effort (may not be immediate)
    """
    try:
        # TODO: Cancel task in Celery
        # from celery.result import AsyncResult
        # task = AsyncResult(task_id)
        # task.revoke(terminate=True)

        logger.info(
            f"Task cancelled: {task_id} by user: {current_user.get('username')}"
        )

    except Exception as e:
        logger.error(f"Failed to cancel task: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Failed to cancel task: {str(e)}",
        )


@router.get(
    "/",
    response_model=TaskListResponse,
    summary="List Tasks",
    description="Lists recent tasks with filtering and pagination.",
)
async def list_tasks(
    status_filter: Optional[str] = None,
    page: int = 1,
    page_size: int = 20,
    current_user: Dict[str, Any] = Depends(get_current_active_user),
) -> TaskListResponse:
    """
    List Tasks

    Retrieves list of tasks with filtering and pagination.

    Args:
        status_filter: Filter by task status
        page: Page number (1-indexed)
        page_size: Number of tasks per page
        current_user: Authenticated user

    Returns:
        TaskListResponse: Paginated list of tasks

    Example:
        ```python
        # Get all successful tasks
        response = requests.get(
            'http://localhost:8000/api/v1/tasks/?status_filter=SUCCESS&page=1',
            headers={'Authorization': f'Bearer {token}'}
        )
        ```
    """
    try:
        # TODO: Get tasks from Celery/Database

        # Mock response
        tasks = [
            TaskStatusResponse(
                task_id=f"task-{i}",
                status="SUCCESS",
                result={"species": "Tilapia"},
                created_at=datetime.utcnow(),
                completed_at=datetime.utcnow(),
            )
            for i in range(page_size)
        ]

        return TaskListResponse(tasks=tasks, total=100, page=page, page_size=page_size)

    except Exception as e:
        logger.error(f"Failed to list tasks: {e}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to retrieve tasks",
        )
