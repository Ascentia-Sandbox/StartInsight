"""Report request model — tracks paid category report purchases.

Part of the conviction funnel: category landing page → Stripe Checkout → report generation.
See design doc: Full Two-Sided Conviction Funnel.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Index, String, Text, func
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class ReportRequest(Base):
    """
    Tracks the lifecycle of a paid category report purchase.

    State machine:
        pending → generating → rendered → delivered
                ↘ failed (any step) → retry → generating/rendered

    Source attribution via UTM: pdf (from weekly digest), seo, direct.
    """

    __tablename__ = "report_requests"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
    )

    # Stripe idempotency — prevents duplicate processing
    stripe_payment_intent_id: Mapped[str] = mapped_column(
        String(255),
        unique=True,
        nullable=False,
        index=True,
    )

    # Source attribution (utm_source: pdf / seo / direct)
    source: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="direct",
    )

    # Category (fintech-malaysia, fnb-malaysia, logistics-singapore)
    category: Mapped[str] = mapped_column(
        String(100),
        nullable=False,
    )

    # Buyer email (from Stripe Checkout)
    email: Mapped[str] = mapped_column(
        String(255),
        nullable=False,
    )

    # Funnel timestamps
    teaser_viewed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    checkout_started_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    paid_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )
    report_delivered_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
    )

    # Pipeline status: pending / generating / rendered / delivered / failed
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        default="pending",
    )

    # Step that failed (for admin retry): gemini / weasyprint / resend
    failed_step: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    # Generated report content (stored for re-delivery)
    report_html: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    # Metadata
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
    )
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
    )

    # Composite index for per-channel kill criteria queries
    __table_args__ = (Index("ix_report_requests_category_source", "category", "source"),)
