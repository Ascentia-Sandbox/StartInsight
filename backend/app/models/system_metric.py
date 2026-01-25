"""SystemMetric database model - Admin monitoring for system metrics.

Phase 4.2: Track LLM costs, API latencies, and other system metrics.
See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from datetime import datetime
from decimal import Decimal
from uuid import UUID, uuid4

from sqlalchemy import DateTime, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB, UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column

from app.db.base import Base


class SystemMetric(Base):
    """
    SystemMetric model - Tracks operational metrics for admin dashboard.

    Metric Types:
    - llm_cost: LLM API costs ($)
    - api_latency: API response time (ms)
    - error_rate: Error percentage (%)
    - scrape_rate: Items scraped per hour
    - analysis_rate: Items analyzed per hour

    Dimensions allow filtering/grouping:
    - model: "claude-3.5-sonnet", "gpt-4o"
    - task: "analysis", "scraping"
    - source: "reddit", "product_hunt"

    RLS Policy: Only admins can view system metrics.
    """

    __tablename__ = "system_metrics"

    # Primary key
    id: Mapped[UUID] = mapped_column(
        PGUUID(as_uuid=True),
        primary_key=True,
        default=uuid4,
        doc="Unique identifier for this metric",
    )

    # Metric identification
    metric_type: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        index=True,
        doc="Type: llm_cost, api_latency, error_rate, scrape_rate, analysis_rate",
    )

    # Metric value
    metric_value: Mapped[Decimal] = mapped_column(
        Numeric(10, 4),
        nullable=False,
        doc="Metric value (units depend on metric_type)",
    )

    # Dimensions for filtering/grouping
    dimensions: Mapped[dict] = mapped_column(
        JSONB,
        default=dict,
        nullable=False,
        doc="Dimensions: {model, task, source, endpoint, etc.}",
    )

    # Timestamp
    recorded_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        index=True,
        doc="When this metric was recorded",
    )

    def __repr__(self) -> str:
        """String representation of SystemMetric."""
        return (
            f"<SystemMetric(type={self.metric_type}, "
            f"value={self.metric_value}, "
            f"recorded_at={self.recorded_at})>"
        )

    def to_dict(self) -> dict:
        """Convert to dictionary for API responses."""
        return {
            "id": str(self.id),
            "metric_type": self.metric_type,
            "metric_value": float(self.metric_value),
            "dimensions": self.dimensions,
            "recorded_at": self.recorded_at.isoformat() if self.recorded_at else None,
        }

    @classmethod
    def record_llm_cost(
        cls,
        cost: float,
        model: str,
        task: str = "analysis",
        input_tokens: int = 0,
        output_tokens: int = 0,
    ) -> "SystemMetric":
        """Factory method to create LLM cost metric."""
        return cls(
            metric_type="llm_cost",
            metric_value=Decimal(str(cost)),
            dimensions={
                "model": model,
                "task": task,
                "input_tokens": input_tokens,
                "output_tokens": output_tokens,
            },
        )

    @classmethod
    def record_api_latency(
        cls,
        latency_ms: float,
        endpoint: str,
        method: str = "GET",
    ) -> "SystemMetric":
        """Factory method to create API latency metric."""
        return cls(
            metric_type="api_latency",
            metric_value=Decimal(str(latency_ms)),
            dimensions={
                "endpoint": endpoint,
                "method": method,
            },
        )

    @classmethod
    def record_error(
        cls,
        error_type: str,
        source: str | None = None,
        message: str | None = None,
    ) -> "SystemMetric":
        """Factory method to record an error event."""
        return cls(
            metric_type="error_rate",
            metric_value=Decimal("1"),  # Count = 1
            dimensions={
                "error_type": error_type,
                "source": source,
                "message": message[:200] if message else None,
            },
        )
