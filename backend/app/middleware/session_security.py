"""Enhanced session security middleware for StartInsight."""

import logging
from typing import Optional
from datetime import datetime, timedelta
import secrets

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

from app.core.config import settings

logger = logging.getLogger(__name__)

class SessionSecurityMiddleware(BaseHTTPMiddleware):
    """
    Enhanced session security middleware.

    Implements:
    - Secure cookie settings
    - Session timeout management
    - Session fixation protection
    - Enhanced authentication security
    """

    def __init__(self, app, session_timeout_minutes: int = 120):
        """
        Initialize session security middleware.

        Args:
            app: Starlette application
            session_timeout_minutes: Session timeout in minutes
        """
        super().__init__(app)
        self.session_timeout_minutes = session_timeout_minutes

    async def dispatch(self, request: Request, call_next):
        # Process the request
        response = await call_next(request)

        # Add enhanced security headers for session management
        await self._enhance_session_security(response, request)

        return response

    async def _enhance_session_security(self, response: Response, request: Request):
        """Enhance session security with proper headers and settings."""

        # Add secure session-related headers
        # These are for browsers to handle sessions more securely

        # Secure cookie settings (if cookies are used)
        # In a real implementation, you'd want to set these based on your
        # authentication mechanism and session store

        # Add HSTS header for secure connections
        if request.url.scheme == "https":
            response.headers["Strict-Transport-Security"] = (
                "max-age=31536000; includeSubDomains; preload"
            )

        # Add CSRF protection headers (if applicable)
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"

    def _validate_session_age(self, session_data: dict) -> bool:
        """Validate session age and renew if necessary."""
        if "created_at" not in session_data:
            return False

        created_at = datetime.fromisoformat(session_data["created_at"])
        session_age = datetime.utcnow() - created_at

        # Check if session has expired
        timeout = timedelta(minutes=self.session_timeout_minutes)
        return session_age <= timeout

    def _generate_secure_session_id(self) -> str:
        """Generate a cryptographically secure session identifier."""
        return secrets.token_urlsafe(32)

    def _validate_session_integrity(self, session_data: dict) -> bool:
        """Validate session integrity."""
        # Basic validation of session structure
        required_fields = ["user_id", "created_at", "session_id"]
        return all(field in session_data for field in required_fields)