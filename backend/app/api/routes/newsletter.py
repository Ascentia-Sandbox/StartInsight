"""Newsletter subscription API — double opt-in with Resend emails."""

import logging
import secrets
from datetime import UTC, datetime, timedelta

from fastapi import APIRouter, Depends, HTTPException, Request
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.rate_limits import limiter
from app.db.session import get_db
from app.models.newsletter import NewsletterSubscriber
from app.services.email_service import send_email

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/newsletter", tags=["newsletter"])

TOKEN_EXPIRY_HOURS = 24


class SubscribeRequest(BaseModel):
    email: EmailStr
    source: str = Field(default="footer", pattern=r"^(footer|homepage)$")


class SubscribeResponse(BaseModel):
    message: str


@router.post("/subscribe", response_model=SubscribeResponse)
@limiter.limit("5/minute")
async def subscribe(
    request: Request,
    body: SubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> SubscribeResponse:
    """
    Subscribe to the newsletter (step 1 of double opt-in).

    Generates a confirmation token and sends a confirmation email.
    Duplicate emails get a friendly message (no enumeration).
    """
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == body.email.lower())
    )
    existing = result.scalar_one_or_none()

    if existing:
        if existing.confirmed and not existing.unsubscribed_at:
            # Already confirmed — don't reveal this to prevent enumeration
            return SubscribeResponse(message="Check your email to confirm your subscription.")

        if existing.unsubscribed_at:
            # Re-subscribing after unsubscribe — reset and send new confirmation
            existing.unsubscribed_at = None
            existing.confirmed = False

        # Refresh token (new or expired)
        existing.confirmation_token = secrets.token_urlsafe(48)
        existing.token_expires_at = datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS)
        existing.source = body.source
        await db.commit()

        await _send_confirmation_email(body.email.lower(), existing.confirmation_token)
        return SubscribeResponse(message="Check your email to confirm your subscription.")

    # New subscriber
    token = secrets.token_urlsafe(48)
    subscriber = NewsletterSubscriber(
        email=body.email.lower(),
        confirmation_token=token,
        token_expires_at=datetime.now(UTC) + timedelta(hours=TOKEN_EXPIRY_HOURS),
        source=body.source,
    )
    db.add(subscriber)
    await db.commit()

    await _send_confirmation_email(body.email.lower(), token)
    return SubscribeResponse(message="Check your email to confirm your subscription.")


@router.get("/confirm/{token}")
async def confirm(
    token: str,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Confirm newsletter subscription (step 2 of double opt-in).

    Validates the token and expiry, marks subscriber as confirmed.
    """
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.confirmation_token == token)
    )
    subscriber = result.scalar_one_or_none()

    if not subscriber:
        raise HTTPException(status_code=404, detail="Invalid confirmation link.")

    if subscriber.confirmed:
        return {"message": "Your subscription is already confirmed."}

    if subscriber.token_expires_at and subscriber.token_expires_at < datetime.now(UTC):
        raise HTTPException(
            status_code=410,
            detail="This confirmation link has expired. Please subscribe again.",
        )

    subscriber.confirmed = True
    subscriber.confirmed_at = datetime.now(UTC)
    subscriber.confirmation_token = None
    subscriber.token_expires_at = None
    await db.commit()

    # Send welcome email (non-blocking — don't fail the confirmation)
    try:
        await send_email(
            to=subscriber.email,
            template="newsletter_welcome",
            variables={
                "app_url": settings.frontend_url,
                "unsubscribe_url": f"{settings.app_url}/api/newsletter/unsubscribe?email={subscriber.email}",
            },
        )
    except Exception as e:
        logger.warning(f"Failed to send welcome email: {e}")

    return {"message": "Your subscription is confirmed! Welcome aboard."}


class UnsubscribeRequest(BaseModel):
    email: EmailStr


@router.post("/unsubscribe")
async def unsubscribe(
    body: UnsubscribeRequest,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    Unsubscribe from the newsletter. Idempotent.
    """
    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == body.email.lower())
    )
    subscriber = result.scalar_one_or_none()

    if subscriber and not subscriber.unsubscribed_at:
        subscriber.unsubscribed_at = datetime.now(UTC)
        await db.commit()

    # Always return success (don't reveal whether email exists)
    return {"message": "You have been unsubscribed."}


@router.get("/unsubscribe")
async def unsubscribe_via_link(
    email: str | None = None,
    token: str | None = None,
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    GET-based unsubscribe for email links. Accepts ?email= or ?token= query param.
    """
    target_email: str | None = email

    # If token provided, decode it to get the email
    if token and not target_email:
        try:
            from itsdangerous import URLSafeTimedSerializer

            serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
            target_email = serializer.loads(token, salt="unsubscribe", max_age=86400 * 30)
        except Exception:
            pass

    if not target_email:
        return {"message": "You have been unsubscribed."}

    result = await db.execute(
        select(NewsletterSubscriber).where(NewsletterSubscriber.email == target_email.lower())
    )
    subscriber = result.scalar_one_or_none()

    if subscriber and not subscriber.unsubscribed_at:
        subscriber.unsubscribed_at = datetime.now(UTC)
        await db.commit()

    return {"message": "You have been unsubscribed."}


async def _send_confirmation_email(email: str, token: str) -> None:
    """Send the double opt-in confirmation email."""
    confirm_url = f"{settings.app_url}/api/newsletter/confirm/{token}"
    try:
        await send_email(
            to=email,
            template="newsletter_confirm",
            variables={"confirm_url": confirm_url},
        )
    except Exception as e:
        logger.warning(f"Failed to send confirmation email to {email}: {e}")
