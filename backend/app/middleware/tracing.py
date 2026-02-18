"""Request tracing middleware with correlation IDs.

Sprint 2.3: Adds correlation IDs to all requests for distributed tracing.
- Extracts or generates correlation ID from X-Correlation-ID header
- Adds correlation ID to response headers
- Sets request context for structured logging
- Times request duration
"""

import time
from collections.abc import Callable

from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware

from app.core.logging import (
    clear_request_context,
    generate_correlation_id,
    get_logger,
    set_correlation_id,
    set_request_context,
)

logger = get_logger(__name__)


class TracingMiddleware(BaseHTTPMiddleware):
    """Middleware for request tracing and correlation IDs."""

    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Get or generate correlation ID
        correlation_id = request.headers.get("X-Correlation-ID")
        if not correlation_id:
            correlation_id = generate_correlation_id()

        # Set correlation ID in context
        set_correlation_id(correlation_id)

        # Extract client IP
        client_ip = request.client.host if request.client else None
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            client_ip = forwarded_for.split(",")[0].strip()

        # Extract user ID if authenticated
        user_id = None
        if hasattr(request.state, "user") and request.state.user:
            user_id = str(getattr(request.state.user, "id", None))

        # Set request context for logging
        set_request_context(
            method=request.method,
            path=request.url.path,
            user_id=user_id,
            client_ip=client_ip,
        )

        # Start timing
        start_time = time.perf_counter()

        try:
            # Process request
            response = await call_next(request)

            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Add correlation ID to response headers
            response.headers["X-Correlation-ID"] = correlation_id
            response.headers["X-Response-Time-Ms"] = str(round(duration_ms, 2))

            # Log request completion
            logger.info(
                f"{request.method} {request.url.path} -> {response.status_code}",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
                user_id=user_id,
            )

            return response

        except Exception as e:
            # Calculate duration
            duration_ms = (time.perf_counter() - start_time) * 1000

            # Log error
            logger.error(
                f"{request.method} {request.url.path} -> 500 ERROR",
                method=request.method,
                path=request.url.path,
                status_code=500,
                duration_ms=round(duration_ms, 2),
                client_ip=client_ip,
                user_id=user_id,
                error=str(e),
            )

            raise

        finally:
            # Clear context
            clear_request_context()
