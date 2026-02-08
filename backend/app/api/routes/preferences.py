"""User Preferences API routes - Phase 9.1: User Attraction Features.

Provides endpoints for:
- User preferences (idea matching quiz)
- Email preferences (digest and alert settings)
- Unauthenticated email unsubscribe (CAN-SPAM compliance)
"""

import logging
from datetime import UTC, datetime
from decimal import Decimal
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import HTMLResponse
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.core.config import settings
from app.models.user import User
from app.models.user_preferences import UserPreferences, EmailPreferences

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/preferences", tags=["User Preferences"])


# ============================================
# Schemas
# ============================================

class UserPreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    background: str | None
    budget_range: str | None
    time_commitment: str | None
    market_preference: str | None
    risk_tolerance: str | None
    skills: list[str] | None
    interests: list[str] | None
    completed_quiz: bool
    updated_at: datetime

    class Config:
        from_attributes = True


class UserPreferencesUpdate(BaseModel):
    background: str | None = Field(None, pattern="^(tech|business|creative|other)$")
    budget_range: str | None = Field(None, pattern="^(0-1k|1k-10k|10k\\+)$")
    time_commitment: str | None = Field(None, pattern="^(nights_weekends|part_time|full_time)$")
    market_preference: str | None = Field(None, pattern="^(b2b|b2c|both)$")
    risk_tolerance: str | None = Field(None, pattern="^(low|medium|high)$")
    skills: list[str] | None = Field(None, max_length=20)
    interests: list[str] | None = Field(None, max_length=20)


class QuizSubmission(BaseModel):
    """One-click idea match quiz submission."""
    background: str = Field(..., pattern="^(tech|business|creative|other)$")
    budget_range: str = Field(..., pattern="^(0-1k|1k-10k|10k\\+)$")
    time_commitment: str = Field(..., pattern="^(nights_weekends|part_time|full_time)$")
    market_preference: str = Field(..., pattern="^(b2b|b2c|both)$")
    risk_tolerance: str = Field(..., pattern="^(low|medium|high)$")


class EmailPreferencesResponse(BaseModel):
    id: UUID
    user_id: UUID
    daily_digest: bool
    weekly_digest: bool
    instant_alerts: bool
    tracked_keywords: list[str] | None
    min_score_alert: float
    digest_time_utc: str
    timezone: str
    unsubscribed_at: datetime | None
    updated_at: datetime

    class Config:
        from_attributes = True


class EmailPreferencesUpdate(BaseModel):
    daily_digest: bool | None = None
    weekly_digest: bool | None = None
    instant_alerts: bool | None = None
    tracked_keywords: list[str] | None = Field(None, max_length=10)
    min_score_alert: float | None = Field(None, ge=0.0, le=1.0)
    digest_time_utc: str | None = Field(None, pattern="^([01]\\d|2[0-3]):[0-5]\\d$")
    timezone: str | None = Field(None, max_length=50)


# ============================================
# User Preferences Endpoints
# ============================================

@router.get("/user", response_model=UserPreferencesResponse)
async def get_user_preferences(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's preferences. Creates default if not exists."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        # Create default preferences
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return UserPreferencesResponse.model_validate(prefs)


@router.patch("/user", response_model=UserPreferencesResponse)
async def update_user_preferences(
    updates: UserPreferencesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update user preferences."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    update_dict = updates.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(prefs, key, value)

    prefs.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(prefs)

    logger.info(f"User {current_user.id} updated preferences")
    return UserPreferencesResponse.model_validate(prefs)


@router.post("/quiz", response_model=UserPreferencesResponse)
async def submit_quiz(
    quiz: QuizSubmission,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Submit the idea match quiz and get personalized results."""
    result = await db.execute(
        select(UserPreferences).where(UserPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = UserPreferences(user_id=current_user.id)
        db.add(prefs)

    # Apply quiz answers
    prefs.background = quiz.background
    prefs.budget_range = quiz.budget_range
    prefs.time_commitment = quiz.time_commitment
    prefs.market_preference = quiz.market_preference
    prefs.risk_tolerance = quiz.risk_tolerance
    prefs.completed_quiz = True
    prefs.updated_at = datetime.now(UTC)

    await db.commit()
    await db.refresh(prefs)

    logger.info(f"User {current_user.id} completed idea match quiz")
    return UserPreferencesResponse.model_validate(prefs)


# ============================================
# Email Preferences Endpoints
# ============================================

@router.get("/email", response_model=EmailPreferencesResponse)
async def get_email_preferences(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get current user's email preferences. Creates default if not exists."""
    result = await db.execute(
        select(EmailPreferences).where(EmailPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = EmailPreferences(user_id=current_user.id)
        db.add(prefs)
        await db.commit()
        await db.refresh(prefs)

    return EmailPreferencesResponse.model_validate(prefs)


@router.patch("/email", response_model=EmailPreferencesResponse)
async def update_email_preferences(
    updates: EmailPreferencesUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update email preferences."""
    result = await db.execute(
        select(EmailPreferences).where(EmailPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = EmailPreferences(user_id=current_user.id)
        db.add(prefs)

    update_dict = updates.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        if key == "min_score_alert" and value is not None:
            value = Decimal(str(value))
        setattr(prefs, key, value)

    prefs.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(prefs)

    logger.info(f"User {current_user.id} updated email preferences")
    return EmailPreferencesResponse.model_validate(prefs)


@router.post("/email/unsubscribe")
async def unsubscribe_from_emails(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Unsubscribe from all email communications."""
    result = await db.execute(
        select(EmailPreferences).where(EmailPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = EmailPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.daily_digest = False
    prefs.weekly_digest = False
    prefs.instant_alerts = False
    prefs.unsubscribed_at = datetime.now(UTC)
    prefs.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(f"User {current_user.id} unsubscribed from emails")
    return {"status": "unsubscribed", "message": "You have been unsubscribed from all email communications"}


@router.post("/email/resubscribe")
async def resubscribe_to_emails(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Resubscribe to email communications with default settings."""
    result = await db.execute(
        select(EmailPreferences).where(EmailPreferences.user_id == current_user.id)
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = EmailPreferences(user_id=current_user.id)
        db.add(prefs)

    prefs.daily_digest = True
    prefs.weekly_digest = True
    prefs.unsubscribed_at = None
    prefs.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(f"User {current_user.id} resubscribed to emails")
    return {"status": "resubscribed", "message": "You have been resubscribed to email communications"}


# ============================================
# Token-based Unsubscribe (CAN-SPAM)
# ============================================


def _generate_unsubscribe_token(user_id: str) -> str:
    """Generate a signed token for one-click email unsubscribe."""
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
    return serializer.dumps(str(user_id), salt="email-unsubscribe")


def _verify_unsubscribe_token(token: str, max_age_days: int = 30) -> str | None:
    """Verify an unsubscribe token. Returns user_id or None."""
    from itsdangerous import BadSignature, SignatureExpired, URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
    try:
        return serializer.loads(token, salt="email-unsubscribe", max_age=max_age_days * 86400)
    except (BadSignature, SignatureExpired):
        return None


# Separate router for unauthenticated unsubscribe (no /preferences prefix)
email_router = APIRouter(tags=["Email"])


@email_router.get("/api/email/unsubscribe", response_class=HTMLResponse)
async def unsubscribe_via_token(
    token: str = Query(..., description="Signed unsubscribe token from email"),
    db: AsyncSession = Depends(get_db),
):
    """One-click email unsubscribe (no login required, CAN-SPAM compliant)."""
    user_id = _verify_unsubscribe_token(token)
    if not user_id:
        return HTMLResponse(
            content="""
            <html><body style="font-family: sans-serif; text-align: center; padding: 60px;">
                <h2>Invalid or Expired Link</h2>
                <p>This unsubscribe link has expired or is invalid.</p>
                <p>Please log in to manage your email preferences.</p>
            </body></html>
            """,
            status_code=400,
        )

    result = await db.execute(
        select(EmailPreferences).where(EmailPreferences.user_id == UUID(user_id))
    )
    prefs = result.scalar_one_or_none()

    if not prefs:
        prefs = EmailPreferences(user_id=UUID(user_id))
        db.add(prefs)

    prefs.daily_digest = False
    prefs.weekly_digest = False
    prefs.instant_alerts = False
    prefs.unsubscribed_at = datetime.now(UTC)
    prefs.updated_at = datetime.now(UTC)

    await db.commit()

    logger.info(f"User {user_id} unsubscribed via email token")

    return HTMLResponse(
        content="""
        <html><body style="font-family: sans-serif; text-align: center; padding: 60px;">
            <h2 style="color: #10B981;">Unsubscribed Successfully</h2>
            <p>You have been unsubscribed from all StartInsight emails.</p>
            <p>You can re-enable notifications anytime from your
               <a href="/settings">account settings</a>.</p>
        </body></html>
        """
    )
