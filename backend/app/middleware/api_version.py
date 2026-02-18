"""API version header middleware.

Adds API-Version and Deprecation headers to all responses.
Prepares the codebase for future /api/v2 versioning.

Current version: v1 (all existing endpoints)
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request

API_VERSION = "1"
API_VERSION_FULL = "1.0.0"


class APIVersionMiddleware(BaseHTTPMiddleware):
    """
    Add API version information to all responses.

    Headers added:
    - API-Version: Current API version
    - X-API-Version: Full semantic version
    """

    async def dispatch(self, request: Request, call_next):
        response = await call_next(request)

        response.headers["API-Version"] = API_VERSION
        response.headers["X-API-Version"] = API_VERSION_FULL

        return response
