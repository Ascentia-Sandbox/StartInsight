"""Insight database model - AI-analyzed structured insights."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Float, ForeignKey, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base


class Insight(Base):
    """
    Insight model - Stores AI-analyzed, structured insights from raw signals.

    An Insight represents the structured analysis of a RawSignal, containing:
    - Identified market problem
    - Proposed solution
    - Market size estimate
    - Relevance score (0.0 - 1.0)
    - Competitor analysis (up to 3 competitors)
    """

    __tablename__ = "insights"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this insight",
    )

    # Foreign key to source raw signal
    raw_signal_id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        ForeignKey("raw_signals.id", ondelete="CASCADE"),
        nullable=False,
        index=True,
        doc="Reference to the source raw signal",
    )

    # Core insight data
    problem_statement: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Identified market problem from the signal",
    )

    proposed_solution: Mapped[str] = mapped_column(
        Text,
        nullable=False,
        doc="Suggested solution approach or opportunity",
    )

    market_size_estimate: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        doc="Market size: 'Small' (<$100M), 'Medium' ($100M-$1B), 'Large' (>$1B)",
    )

    relevance_score: Mapped[float] = mapped_column(
        Float,
        nullable=False,
        index=True,
        doc="Signal relevance (0.0=weak, 1.0=strong)",
    )

    # Competitor analysis (stored as JSON array of competitor objects)
    competitor_analysis: Mapped[dict] = mapped_column(
        JSONB,
        nullable=True,
        default=list,
        doc="List of up to 3 competitors with name, URL, description, market position",
    )

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this insight was created",
    )

    # Relationships
    raw_signal: Mapped["RawSignal"] = relationship(
        "RawSignal",
        back_populates="insights",
        lazy="selectin",
        doc="The source raw signal for this insight",
    )

    def __repr__(self) -> str:
        """String representation of Insight."""
        return (
            f"<Insight(id={self.id}, "
            f"problem='{self.problem_statement[:50]}...', "
            f"score={self.relevance_score})>"
        )

    def __str__(self) -> str:
        """Human-readable string representation."""
        return f"Insight: {self.problem_statement[:100]}"
