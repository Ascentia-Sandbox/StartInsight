"""AgentExecutionLog database model - Admin monitoring for agent tasks.

Phase 4.2: Track agent execution history for admin dashboard.
See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class AgentExecutionLog(Base):
    """
    AgentExecutionLog model - Tracks background task executions.

    Records:
    - Agent type (scraper, analyzer)
    - Source (reddit, product_hunt, google_trends)
    - Execution status and duration
    - Items processed/failed
    - Error messages

    Used by admin dashboard for:
    - Real-time execution monitoring
    - Performance analysis
    - Error tracking

    RLS Policy: Only admins can view execution logs.
    """

    __tablename__ = "agent_execution_logs"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this execution log",
    )

    # Agent identification
    agent_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Agent type: scraper, analyzer",
    )

    source: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
        index=True,
        doc="Data source: reddit, product_hunt, google_trends (for scrapers)",
    )

    # Execution status
    status: Mapped[str] = mapped_column(
        String(20),
        nullable=False,
        index=True,
        doc="Status: running, completed, failed, skipped",
    )

    # Timing
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        doc="When execution started",
    )

    completed_at: Mapped[datetime | None] = mapped_column(
        DateTime(timezone=True),
        nullable=True,
        doc="When execution completed",
    )

    duration_ms: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
        doc="Execution duration in milliseconds",
    )

    # Results
    items_processed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of items successfully processed",
    )

    items_failed: Mapped[int] = mapped_column(
        Integer,
        default=0,
        nullable=False,
        doc="Number of items that failed processing",
    )

    # Error information
    error_message: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
        doc="Error message if execution failed",
    )

    # Additional metadata
    extra_metadata: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Additional execution metadata (job_id, trigger_type, etc.)",
    )

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this log was created",
    )

    def __repr__(self) -> str:
        """String representation of AgentExecutionLog."""
        return (
            f"<AgentExecutionLog(agent={self.agent_type}, "
            f"source={self.source}, "
            f"status={self.status}, "
            f"items={self.items_processed})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "agent_type": self.agent_type,
            "source": self.source,
            "status": self.status,
            "started_at": self.started_at.isoformat() if self.started_at else None,
            "completed_at": self.completed_at.isoformat() if self.completed_at else None,
            "duration_ms": self.duration_ms,
            "items_processed": self.items_processed,
            "items_failed": self.items_failed,
            "error_message": self.error_message,
            "metadata": self.extra_metadata,
        }

    def calculate_duration(self) -> None:
        """Calculate duration from started_at and completed_at."""
        if self.started_at and self.completed_at:
            delta = self.completed_at - self.started_at
            self.duration_ms = int(delta.total_seconds() * 1000)
