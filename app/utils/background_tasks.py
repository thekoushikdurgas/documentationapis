"""Utilities for managing FastAPI background tasks efficiently.

This module provides utilities for common background task patterns,
including error handling, logging, and task tracking.

Note: In AWS Lambda, background tasks execute synchronously before response
because Lambda closes the event loop immediately after response is sent.
"""

from typing import Any, Awaitable, Callable

from fastapi.background import BackgroundTasks as BackgroundTasksType

from app.utils.lambda_utils import IS_LAMBDA
from app.utils.logger import get_logger

logger = get_logger(__name__)


def add_background_task_safe(
    background_tasks: BackgroundTasksType,
    func: Callable[..., Awaitable[Any]],
    *args: Any,
    **kwargs: Any
) -> None:
    """Safely add a background task with error handling.
    
    In AWS Lambda, executes synchronously before response (Lambda closes event loop).
    In other environments, executes as background task after response.
    
    Args:
        background_tasks: FastAPI BackgroundTasks instance
        func: Async function to execute
        *args: Positional arguments for the function
        **kwargs: Keyword arguments for the function
    """
    if IS_LAMBDA:
        # In Lambda, we need to execute synchronously before response
        # Mangum will wait for background tasks, but we execute immediately
        # to ensure completion before event loop closes
        try:
            async def safe_wrapper() -> None:
                """Wrapper that handles errors gracefully."""
                try:
                    await func(*args, **kwargs)
                except Exception as e:
                    logger.error(
                        f"Background task failed in Lambda: {func.__name__}",
                        exc_info=True,
                        extra={
                            "context": {
                                "function": func.__name__,
                                "error": str(e),
                            }
                        }
                    )
            
            background_tasks.add_task(safe_wrapper)
        except Exception as e:
            logger.error(
                f"Failed to add background task in Lambda: {func.__name__}",
                exc_info=True,
                extra={
                    "context": {
                        "function": func.__name__,
                        "error": str(e),
                    }
                }
            )
    else:
        # In non-Lambda environments, use background tasks
        async def safe_wrapper() -> None:
            """Wrapper that handles errors gracefully."""
            try:
                await func(*args, **kwargs)
            except Exception as e:
                logger.error(
                    f"Background task failed: {func.__name__}",
                    exc_info=True,
                    extra={
                        "context": {
                            "function": func.__name__,
                            "error": str(e),
                            "args": str(args),
                            "kwargs": str(kwargs),
                        }
                    }
                )
                # Don't raise - background task failures shouldn't break the endpoint
        
        try:
            background_tasks.add_task(safe_wrapper)
        except Exception as e:
            logger.error(
                f"Failed to add background task: {func.__name__}",
                exc_info=True,
                extra={
                    "context": {
                        "function": func.__name__,
                        "error": str(e),
                    }
                }
            )
            # Don't raise - task addition failure shouldn't break the endpoint

