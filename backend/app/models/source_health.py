"""Phase 6.2A: Source health tracking model.

Tracks per-source scraper health: last run times, failure counts,
latency, signal yield, and circuit breaker state.
"""

import uuid
from datetime import datetime

from sqlalchemy import Float, Integer, String, Text
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import Mapped, mapped_column
from sqlalchemy.sql import func

from app.db.base import Base


class SourceHealth(Base):
    """Tracks scraper health per data source."""

    __tablename__ = "source_health"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), primary_key=True, default=uuid.uuid4
    )
    source_name: Mapped[str] = mapped_column(
        String(50), unique=True, nullable=False, index=True
    )
    status: Mapped[str] = mapped_column(
        String(20), nullable=False, default="unknown"
    )  # fresh/stale/error/disabled/unknown
    last_success_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_failure_at: Mapped[datetime | None] = mapped_column(nullable=True)
    last_error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    consecutive_failures: Mapped[int] = mapped_column(Integer, default=0)
    avg_latency_ms: Mapped[float] = mapped_column(Float, default=0)
    avg_signals_per_run: Mapped[float] = mapped_column(Float, default=0)
    total_runs: Mapped[int] = mapped_column(Integer, default=0)
    total_failures: Mapped[int] = mapped_column(Integer, default=0)
    circuit_state: Mapped[str] = mapped_column(
        String(20), default="closed"
    )  # closed/open/half_open
    # Phase 6.4A: Welford's algorithm baselines
    baseline_mean: Mapped[float] = mapped_column(Float, default=0)
    baseline_variance: Mapped[float] = mapped_column(Float, default=0)
    baseline_count: Mapped[int] = mapped_column(Integer, default=0)

    updated_at: Mapped[datetime] = mapped_column(
        server_default=func.now(), onupdate=func.now()
    )
