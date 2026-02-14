"""Pipeline Run model - Tracks content automation pipeline executions.

Phase 17: Content Automation Pipeline
"""

from datetime import datetime
from decimal import Decimal
from typing import Any
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class PipelineRun(Base):
    """Tracks content automation pipeline executions."""

    __tablename__ = "pipeline_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    status: Mapped[str] = mapped_column(
        String(20), default="running", nullable=False,
        doc="running | completed | failed | partial",
    )
    stages_completed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    total_stages: Mapped[int] = mapped_column(Integer, default=4, nullable=False)
    cost_usd: Mapped[Decimal] = mapped_column(Numeric(10, 4), default=Decimal("0"), nullable=False)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String(500), nullable=True)
    started_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), nullable=False,
    )
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    def __repr__(self) -> str:
        return f"<PipelineRun(id={self.id}, status={self.status}, stages={self.stages_completed}/{self.total_stages})>"
