"""Lambda environment utilities for AWS Lambda deployment."""

import asyncio
import os

# Centralized Lambda detection - single source of truth
IS_LAMBDA = bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))


async def safe_await_in_lambda(coro, operation_name: str = "operation"):
    """Safely await a coroutine in Lambda, handling event loop closure.
    
    This function consolidates the duplicate _safe_await_in_lambda implementations
    from mongodb.py and repository files into a single, reusable utility.
    
    Args:
        coro: Coroutine to await
        operation_name: Name of operation for logging (optional)
        
    Returns:
        Result of the coroutine, or None if event loop is closed
        
    Note:
        In non-Lambda environments, this simply awaits the coroutine normally.
        In Lambda, it checks for event loop closure and handles it gracefully.
    """
    if not IS_LAMBDA:
        return await coro
    
    # Check if event loop is closed before attempting operation
    try:
        loop = asyncio.get_event_loop()
        if loop.is_closed():
            return None
    except RuntimeError:
        # No event loop or loop is closed
        return None
    
    try:
        return await coro
    except RuntimeError as e:
        error_msg = str(e)
        if "Event loop is closed" in error_msg or "event loop is closed" in error_msg.lower():
            # Event loop closed - return None silently
            return None
        else:
            # Re-raise other RuntimeErrors
            raise
    except Exception as e:
        # Catch all other exceptions and check for event loop closure
        error_msg = str(e)
        if "Event loop is closed" in error_msg or "event loop is closed" in error_msg.lower():
            return None
        else:
            # Re-raise other errors
            raise

