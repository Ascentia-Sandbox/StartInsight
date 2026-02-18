"""Core decorators for standardized functionality - Code simplification Phase 4.

Provides reusable decorators for common patterns like background task error handling.
"""

import functools
import logging
from collections.abc import Callable
from typing import Any

logger = logging.getLogger(__name__)


def background_task_with_error_handling(func: Callable) -> Callable:
    """
    Decorator for background tasks with standardized error handling.

    Catches exceptions, logs them, and prevents background tasks from crashing silently.
    Useful for async background tasks that run outside request context.

    Args:
        func: Async function to wrap with error handling

    Returns:
        Wrapped async function with error handling

    Example:
        @background_task_with_error_handling
        async def process_analysis(analysis_id: UUID):
            # ... processing logic
            pass
    """
    @functools.wraps(func)
    async def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            logger.exception(
                f"Background task {func.__name__} failed with error: {str(e)}",
                exc_info=True,
            )
            # Re-raise to allow caller to handle if needed
            raise

    return wrapper
