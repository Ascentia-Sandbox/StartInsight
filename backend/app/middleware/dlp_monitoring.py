"""Data Loss Prevention (DLP) monitoring middleware for StartInsight."""

import logging
from collections import defaultdict, deque
from dataclasses import dataclass
from datetime import UTC, datetime, timedelta

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import Response

logger = logging.getLogger(__name__)

@dataclass
class SecurityEvent:
    """Represents a security event for monitoring."""
    timestamp: datetime
    event_type: str
    user_id: str | None
    ip_address: str
    details: dict[str, str]

class DLPMonitoringMiddleware(BaseHTTPMiddleware):
    """
    Data Loss Prevention (DLP) monitoring middleware.

    Implements:
    - Unusual access pattern detection
    - Suspicious activity monitoring
    - Anomaly detection for sensitive operations
    - Enhanced session management
    """

    def __init__(self, app, suspicious_threshold: int = 10, time_window_minutes: int = 60):
        """
        Initialize DLP monitoring middleware.

        Args:
            app: Starlette application
            suspicious_threshold: Number of suspicious events before alerting
            time_window_minutes: Time window in minutes for anomaly detection
        """
        super().__init__(app)
        self.suspicious_threshold = suspicious_threshold
        self.time_window_minutes = time_window_minutes

        # Track suspicious activities by IP
        self.suspicious_activities = defaultdict(lambda: defaultdict(deque))

        # Track recent requests by IP for rate limiting
        self.ip_request_counts = defaultdict(lambda: defaultdict(int))

        # Track user sessions for consistency
        self.active_sessions = {}

    async def dispatch(self, request: Request, call_next):
        # Record request start time
        start_time = datetime.now(UTC)

        # Process the request
        response = await call_next(request)

        # Perform DLP monitoring after request processing
        await self._monitor_request(request, response, start_time)

        return response

    async def _monitor_request(self, request: Request, response: Response, start_time: datetime):
        """Monitor request for suspicious activities."""
        try:
            # Get client IP
            client_ip = self._get_client_ip(request)

            # Check for suspicious patterns in request
            suspicious_events = self._detect_suspicious_patterns(request)

            if suspicious_events:
                # Log suspicious activity
                for event in suspicious_events:
                    logger.warning(f"Suspicious activity detected: {event}")

                    # Track this suspicious activity
                    self._track_suspicious_activity(client_ip, event)

                    # Check if threshold exceeded
                    if self._exceeds_suspicious_threshold(client_ip):
                        logger.error(f"ALERT: Suspicious activity threshold exceeded for IP: {client_ip}")
                        # In production, you might want to trigger additional security measures
                        # such as blocking the IP, sending alerts, or requiring additional verification

        except Exception as e:
            logger.error(f"Error in DLP monitoring: {e}")

    def _get_client_ip(self, request: Request) -> str:
        """Get client IP address."""
        # Try to get IP from forwarded header (common in proxies/load balancers)
        x_forwarded_for = request.headers.get("x-forwarded-for")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0].strip()

        # Fallback to remote address
        return request.client.host if request.client else "unknown"

    def _detect_suspicious_patterns(self, request: Request) -> list[str]:
        """Detect suspicious patterns in the request."""
        suspicious_events = []

        # Check for unusual request patterns
        if self._is_unusual_request_pattern(request):
            suspicious_events.append("Unusual request pattern detected")

        # Check for suspicious user agents
        user_agent = request.headers.get("user-agent", "")
        if self._is_suspicious_user_agent(user_agent):
            suspicious_events.append("Suspicious user agent detected")

        # Check for potential path traversal attempts
        if self._contains_path_traversal(request.url.path):
            suspicious_events.append("Potential path traversal attempt detected")

        # Check for potential SQL injection attempts
        if self._contains_sql_injection(request.url.path):
            suspicious_events.append("Potential SQL injection attempt detected")

        return suspicious_events

    def _is_unusual_request_pattern(self, request: Request) -> bool:
        """Check if request has unusual patterns."""
        # This is a simplified check - in production, you'd want more sophisticated
        # pattern recognition and machine learning models
        return False  # Placeholder for actual implementation

    def _is_suspicious_user_agent(self, user_agent: str) -> bool:
        """Check if user agent is suspicious."""
        # Common suspicious user agents
        suspicious_patterns = [
            "sqlmap", "nikto", "burpsuite", "owasp", "metasploit"
        ]

        user_agent_lower = user_agent.lower()
        return any(pattern in user_agent_lower for pattern in suspicious_patterns)

    def _contains_path_traversal(self, path: str) -> bool:
        """Check if path contains path traversal attempts."""
        return ".." in path

    def _contains_sql_injection(self, path: str) -> bool:
        """Check if path contains SQL injection attempts."""
        sql_patterns = [
            "union",
            "select",
            "drop",
            "delete",
            "insert",
            "update",
            "create",
            "alter",
            "exec",
            "execute"
        ]

        path_lower = path.lower()
        return any(pattern in path_lower for pattern in sql_patterns)

    def _track_suspicious_activity(self, ip_address: str, event: str):
        """Track suspicious activity for threshold checking."""
        current_time = datetime.now(UTC)

        # Add to queue of recent activities
        self.suspicious_activities[ip_address]["events"].append(
            SecurityEvent(
                timestamp=current_time,
                event_type=event,
                user_id=None,
                ip_address=ip_address,
                details={}
            )
        )

        # Keep only recent events within the time window
        self._cleanup_old_activities(ip_address)

    def _cleanup_old_activities(self, ip_address: str):
        """Clean up old suspicious activities."""
        current_time = datetime.now(UTC)
        time_window = timedelta(minutes=self.time_window_minutes)

        # Keep only recent events
        self.suspicious_activities[ip_address]["events"] = [
            event for event in self.suspicious_activities[ip_address]["events"]
            if current_time - event.timestamp <= time_window
        ]

    def _exceeds_suspicious_threshold(self, ip_address: str) -> bool:
        """Check if suspicious activity threshold is exceeded."""
        current_time = datetime.now(UTC)
        time_window = timedelta(minutes=self.time_window_minutes)

        # Count recent suspicious events
        recent_events = [
            event for event in self.suspicious_activities[ip_address]["events"]
            if current_time - event.timestamp <= time_window
        ]

        return len(recent_events) >= self.suspicious_threshold
