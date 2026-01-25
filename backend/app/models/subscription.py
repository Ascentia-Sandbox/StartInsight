"""Subscription model for Phase 6.1 - Stripe Payment Integration.

Tracks user subscriptions, payment history, and billing information.
"""

from datetime import datetime
from typing import TYPE_CHECKING
from uuid import uuid4

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class Subscription(Base):
    """Subscription model for Stripe payment tracking.

    Stores subscription details including Stripe IDs, status, and billing cycle.
    """

    __tablename__ = "subscriptions"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # User relationship
    user_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe identifiers
    stripe_customer_id: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
        unique=True,
        index=True,
    )
    stripe_subscription_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
        index=True,
    )
    stripe_price_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Subscription details
    tier: Mapped[str] = mapped_column(
        String(50),
        default="free",
        nullable=False,
    )  # free, starter, pro, enterprise
    status: Mapped[str] = mapped_column(
        String(50),
        default="active",
        nullable=False,
    )  # active, past_due, canceled, trialing, incomplete

    # Billing cycle
    current_period_start: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    current_period_end: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    cancel_at_period_end: Mapped[bool] = mapped_column(
        default=False,
        nullable=False,
    )
    canceled_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Usage tracking
    analyses_used_this_month: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
    )
    last_usage_reset: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Extra data
    subscription_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )

    # Relationships
    user: Mapped["User"] = relationship(
        "User",
        back_populates="subscription",
    )
    payment_history: Mapped[list["PaymentHistory"]] = relationship(
        "PaymentHistory",
        back_populates="subscription",
        cascade="all, delete-orphan",
    )


class PaymentHistory(Base):
    """Payment history for tracking all transactions."""

    __tablename__ = "payment_history"

    id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    subscription_id: Mapped[UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("subscriptions.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
    )

    # Stripe identifiers
    stripe_payment_intent_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
        unique=True,
    )
    stripe_invoice_id: Mapped[str | None] = mapped_column(
        String(255),
        nullable=True,
    )

    # Payment details
    amount: Mapped[int] = mapped_column(
        Integer,
        nullable=False,
    )  # Amount in cents
    currency: Mapped[str] = mapped_column(
        String(3),
        default="usd",
        nullable=False,
    )
    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
    )  # succeeded, failed, pending, refunded

    # Description
    description: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    # Relationships
    subscription: Mapped["Subscription"] = relationship(
        "Subscription",
        back_populates="payment_history",
    )
