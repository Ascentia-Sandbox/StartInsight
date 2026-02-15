"""Contact form API endpoint."""

import logging
from datetime import datetime

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, EmailStr, Field
from slowapi import Limiter
from slowapi.util import get_remote_address
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.rate_limits import limiter
from app.db.session import get_db

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/contact", tags=["contact"])


class ContactRequest(BaseModel):
    name: str = Field(..., min_length=1, max_length=100)
    email: EmailStr
    subject: str = Field(..., min_length=1, max_length=200)
    message: str = Field(..., min_length=10, max_length=5000)


class ContactResponse(BaseModel):
    success: bool
    message: str


@router.post("", response_model=ContactResponse)
@limiter.limit("5/hour")
async def submit_contact_form(
    request: Request,
    data: ContactRequest,
    db: AsyncSession = Depends(get_db),
) -> ContactResponse:
    """
    Submit a contact form message.

    Rate limited to 5 per hour per IP to prevent spam.
    Logs the message and optionally sends email notification.
    """
    logger.info(
        f"Contact form submission from {data.name} ({data.email}): {data.subject}"
    )

    # Store in database for tracking (optional - log for now)
    # In production, this would send via email_service
    try:
        from app.services.email_service import send_email

        await send_email(
            to="hello@startinsight.co",
            template="contact_form",
            variables={
                "name": data.name,
                "email": data.email,
                "subject": data.subject,
                "message": data.message,
                "timestamp": datetime.utcnow().isoformat(),
            },
        )
    except Exception as e:
        # Don't fail the request if email fails - just log
        logger.warning(f"Failed to send contact notification email: {e}")

    return ContactResponse(
        success=True,
        message="Thank you for your message. We'll get back to you within 24 hours.",
    )
