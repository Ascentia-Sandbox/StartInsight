"""Webhook event tracking for idempotency - Phase 6.1.

Prevents duplicate processing of Stripe webhook events.
"""

from datetime import datetime
from uuid import uuid4

from sqlalchemy import DateTime, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class WebhookEvent(Base):
    """Track processed webhook events for idempotency.

    Prevents duplicate processing of Stripe webhook events during retries.
    Stripe guarantees at-least-once delivery, so we must ensure exactly-once processing.
    """

    __tablename__ = "webhook_events"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Stripe event ID (unique identifier from Stripe)
    stripe_event_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,  # Ensures each event processed only once
        index=True,
    )

    # Event details
    event_type: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
        index=True,
    )  # checkout.session.completed, invoice.paid, etc.

    # Processing status
    status: Mapped[str] = mapped_column(
        String(50),
        default="processed",
        nullable=False,
    )  # processed, failed, skipped

    # Event payload (for debugging)
    payload: Mapped[dict] = mapped_column(
        JSONB,
        nullable=False,
    )

    # Processing result
    result: Mapped[dict | None] = mapped_column(
        JSONB,
        nullable=True,
    )

    # Error details (if processing failed)
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    processed_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
