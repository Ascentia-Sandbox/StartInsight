"""Rate limiting middleware for payment endpoints."""
import logging
from collections import defaultdict
from datetime import datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response
from starlette.status import HTTP_429_TOO_MANY_REQUESTS

logger = logging.getLogger(__name__)

# In-memory rate limiting for non-production environments
# For production, use Redis-based rate limiting
_rate_limits: defaultdict[str, list] = defaultdict(list)

class RateLimiterMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware for sensitive payment endpoints.

    Implements rate limiting for:
    - Checkout session creation
    - Subscription updates
    - Payment-related operations

    For production environments, consider using Redis-based rate limiting
    to support distributed rate limiting across multiple instances.
    """

    def __init__(self, app, max_requests: int = 100, window_seconds: int = 3600):
        """
        Initialize rate limiter.

        Args:
            app: Starlette application
            max_requests: Maximum number of requests per window
            window_seconds: Time window in seconds
        """
        super().__init__(app)
        self.max_requests = max_requests
        self.window_seconds = window_seconds

    async def dispatch(self, request: Request, call_next):
        # Skip rate limiting for health checks and public endpoints
        if request.url.path.startswith("/health") or request.url.path.startswith("/api/public"):
            return await call_next(request)

        # Apply rate limiting to sensitive payment endpoints
        if self._should_rate_limit(request):
            # Check if IP is rate limited
            client_ip = self._get_client_ip(request)
            if self._is_rate_limited(client_ip):
                logger.warning(f"Rate limit exceeded for IP: {client_ip}")
                return Response(
                    content="Too Many Requests",
                    status_code=HTTP_429_TOO_MANY_REQUESTS
                )

            # Record this request
            self._record_request(client_ip)

        return await call_next(request)

    def _should_rate_limit(self, request: Request) -> bool:
        """Determine if this endpoint should be rate limited."""
        payment_endpoints = [
            "/api/checkout",
            "/api/portal",
            "/api/webhook",
            "/api/payments"
        ]

        # Check if this is a payment-related endpoint
        for endpoint in payment_endpoints:
            if request.url.path.startswith(endpoint):
                return True

        # Also rate limit specific sensitive operations
        sensitive_operations = [
            "POST /api/checkout",
            "POST /api/portal",
            "POST /api/webhook"
        ]

        request_identifier = f"{request.method} {request.url.path}"
        for op in sensitive_operations:
            if request_identifier.startswith(op):
                return True

        return False

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Try to get IP from forwarded header (common in proxies/load balancers)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Fallback to remote address
        return request.client.host if request.client else "unknown"

    def _is_rate_limited(self, client_ip: str) -> bool:
        """Check if client is rate limited."""
        now = datetime.utcnow()
        window_start = now - timedelta(seconds=self.window_seconds)

        # Get requests in current window
        ip_requests = _rate_limits[client_ip]
        recent_requests = [
            req_time for req_time in ip_requests
            if req_time > window_start
        ]

        # Check if rate limit exceeded
        return len(recent_requests) >= self.max_requests

    def _record_request(self, client_ip: str):
        """Record a request for rate limiting."""
        now = datetime.utcnow()
        _rate_limits[client_ip].append(now)

        # Clean up old requests
        window_start = now - timedelta(seconds=self.window_seconds)
        _rate_limits[client_ip] = [
            req_time for req_time in _rate_limits[client_ip]
            if req_time > window_start
        ]
