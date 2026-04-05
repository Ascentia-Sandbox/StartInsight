"""Newsletter subscriber model — double opt-in email collection."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, String, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class NewsletterSubscriber(Base):
    """Newsletter subscriber with double opt-in confirmation flow."""

    __tablename__ = "newsletter_subscribers"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)

    email: Mapped[str] = mapped_column(String(255), unique=True, nullable=False, index=True)

    confirmed: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)

    confirmation_token: Mapped[str | None] = mapped_column(
        String(128), unique=True, nullable=True, index=True
    )

    token_expires_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True), nullable=True
    )

    confirmed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    unsubscribed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Linked user account (set when a subscriber later creates an account)
    user_id: Mapped[UUID | None] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
        index=True,
    )

    source: Mapped[str] = mapped_column(String(50), default="footer", nullable=False)

    # Email nurture drip sequence: 0=welcome sent, 1=day1, 3=day3, 7=day7, 14=day14
    nurture_stage: Mapped[int] = mapped_column(
        Integer, default=0, server_default="0", nullable=False
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False
    )
