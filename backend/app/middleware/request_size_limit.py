"""Request size limit middleware for DoS protection."""

from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

from app.core.config import settings

MAX_REQUEST_SIZE = settings.max_request_size


class RequestSizeLimitMiddleware(BaseHTTPMiddleware):
    """
    Enforce maximum request body size to prevent DoS attacks.

    Limits:
    - Maximum request size: 1MB
    - Returns 413 Payload Too Large if exceeded
    """

    async def dispatch(self, request: Request, call_next):
        # Check Content-Length header if present
        content_length = request.headers.get("content-length")

        if content_length:
            if int(content_length) > MAX_REQUEST_SIZE:
                return JSONResponse(
                    status_code=413,
                    content={
                        "detail": f"Request body too large. Maximum size: {MAX_REQUEST_SIZE / 1_000_000}MB"
                    },
                )

        return await call_next(request)
