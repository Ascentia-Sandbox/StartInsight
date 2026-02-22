"""Email open tracking endpoint.

Returns a 1x1 transparent GIF when an email is opened.
Decodes the tracking token to log open events.
Token format: base64url-encoded JSON {"user_id": "...", "digest_date": "YYYY-MM-DD", "type": "weekly_digest"}
"""

import base64
import json
import logging
from datetime import UTC, datetime

from fastapi import APIRouter, Response

router = APIRouter(tags=["Email Tracking"])
logger = logging.getLogger(__name__)

# 1x1 transparent GIF (43 bytes)
_TRANSPARENT_GIF = bytes([
    0x47, 0x49, 0x46, 0x38, 0x39, 0x61, 0x01, 0x00, 0x01, 0x00,
    0x80, 0x00, 0x00, 0xFF, 0xFF, 0xFF, 0x00, 0x00, 0x00, 0x21,
    0xF9, 0x04, 0x00, 0x00, 0x00, 0x00, 0x00, 0x2C, 0x00, 0x00,
    0x00, 0x00, 0x01, 0x00, 0x01, 0x00, 0x00, 0x02, 0x02, 0x44,
    0x01, 0x00, 0x3B,
])

_NO_CACHE_HEADERS = {
    "Cache-Control": "no-store, no-cache, must-revalidate",
    "Pragma": "no-cache",
    "Expires": "0",
}


def _make_gif_response() -> Response:
    """Return the 1x1 GIF response with no-cache headers."""
    return Response(
        content=_TRANSPARENT_GIF,
        media_type="image/gif",
        headers=_NO_CACHE_HEADERS,
    )


@router.get("/api/email/track/open/{token}")
async def track_email_open(token: str) -> Response:
    """
    Track email open events via a 1x1 tracking pixel.

    The token is a base64url-encoded JSON object containing:
    - user_id: anonymised user identifier (UUID string)
    - digest_date: date the digest was sent (YYYY-MM-DD)
    - type: email type (e.g. "weekly_digest")

    Always returns the 1x1 GIF regardless of token validity so that
    broken tokens never cause a visible error in the email client.
    Raw email addresses are NEVER logged.
    """
    try:
        # Pad the token to a valid base64 length (urlsafe_b64decode requires correct padding)
        padded = token + "==" * ((-len(token)) % 4 if len(token) % 4 else 0)
        data: dict = json.loads(base64.urlsafe_b64decode(padded).decode("utf-8"))

        user_id = data.get("user_id", "unknown")
        email_type = data.get("type", "unknown")
        digest_date = data.get("digest_date", "unknown")

        logger.info(
            "Email opened: user_id=%s type=%s date=%s opened_at=%s",
            user_id,
            email_type,
            digest_date,
            datetime.now(UTC).isoformat(),
        )

        # Future: persist to email_sends.opened_at via DB write
        # Keeping the endpoint lightweight for now (no DB dependency = no latency risk)

    except Exception:
        # Never let tracking errors surface to the email client
        pass

    return _make_gif_response()


def build_tracking_token(user_id: str, digest_date: str, email_type: str = "weekly_digest") -> str:
    """
    Build a base64url tracking token for an email open pixel.

    Args:
        user_id: UUID string of the recipient user (not email address).
        digest_date: ISO date string (YYYY-MM-DD) the digest was sent.
        email_type: Type identifier for the email.

    Returns:
        URL-safe base64 token string (no padding) safe for use in URLs.
    """
    payload = json.dumps(
        {"user_id": user_id, "digest_date": digest_date, "type": email_type},
        separators=(",", ":"),
    ).encode("utf-8")
    return base64.urlsafe_b64encode(payload).rstrip(b"=").decode("ascii")
