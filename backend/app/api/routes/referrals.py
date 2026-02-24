"""Referral program API endpoints.

Endpoints:
- GET /api/referrals/stats - Current user referral stats and link

Referral codes are 8-character uppercase alphanumeric strings,
auto-generated on first access via GET /api/users/me or this endpoint.
"""

import logging
import secrets
import string
from datetime import UTC, datetime

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.db.session import get_db
from app.models.user import User
from app.schemas.user import ReferralStatsResponse

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/referrals", tags=["Referrals"])

_REFERRAL_ALPHABET = string.ascii_uppercase + string.digits
_SITE_URL = "https://startinsight.co"


def generate_referral_code() -> str:
    """Generate an 8-char alphanumeric referral code (uppercase)."""
    return "".join(secrets.choice(_REFERRAL_ALPHABET) for _ in range(8))


async def _ensure_referral_code(user: User, db: AsyncSession) -> str:
    """Return the user's referral code, generating one if absent.

    Writes back to DB only when a new code is generated.
    """
    if user.referral_code:
        return user.referral_code

    # Generate a unique code with retry in case of collision
    for _ in range(5):
        candidate = generate_referral_code()
        existing = await db.scalar(
            select(User).where(User.referral_code == candidate).limit(1)
        )
        if not existing:
            user.referral_code = candidate
            user.updated_at = datetime.now(UTC)
            await db.commit()
            await db.refresh(user)
            logger.info(f"Generated referral code {candidate} for user {user.email}")
            return candidate

    # Extremely unlikely — log and fall back to uuid fragment
    fallback = secrets.token_hex(4).upper()
    user.referral_code = fallback
    user.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(user)
    logger.warning(
        f"Used fallback referral code {fallback} for user {user.email} "
        "after collision loop exhausted"
    )
    return fallback


@router.get("/stats", response_model=ReferralStatsResponse)
async def get_referral_stats(
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> ReferralStatsResponse:
    """Get current user's referral program statistics.

    Automatically generates a referral code if the user doesn't have one yet.

    Returns:
        referral_code: The user's unique 8-char code
        referral_link: Full URL to share (https://startinsight.co/?ref=XXXXXXXX)
        referrals_count: Number of users who signed up via this code
        reward_status: "pending" (< 1 referral converts) | "earned" (>= 1)
    """
    code = await _ensure_referral_code(current_user, db)

    # Count how many users were referred by this code
    referrals_count: int = await db.scalar(
        select(func.count()).select_from(User).where(
            User.referred_by == code
        )
    ) or 0

    reward_status = "earned" if referrals_count >= 1 else "pending"

    logger.info(
        f"Referral stats fetched for {current_user.email}: "
        f"code={code}, referrals={referrals_count}"
    )

    return ReferralStatsResponse(
        referral_code=code,
        referral_link=f"{_SITE_URL}/?ref={code}",
        referrals_count=referrals_count,
        reward_status=reward_status,
    )
