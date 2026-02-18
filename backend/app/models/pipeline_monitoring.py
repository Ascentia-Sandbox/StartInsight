"""Pipeline Monitoring models for Phase 8.2: Data Pipeline Command Center.

Provides:
- PipelineHealthCheck: Scraper health tracking
- APIQuotaUsage: API quota monitoring
- AdminAlert: Alert configurations
- AdminAlertIncident: Alert incidents
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, Text, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class PipelineHealthCheck(Base):
    """Tracks scraper health status over time."""

    __tablename__ = "pipeline_health_checks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    scraper_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    status: Mapped[str] = mapped_column(String(20), nullable=False, comment="healthy, degraded, down")
    response_time_ms: Mapped[int | None] = mapped_column(Integer, nullable=True)
    items_fetched: Mapped[int | None] = mapped_column(Integer, nullable=True)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)
    checked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<PipelineHealthCheck(scraper={self.scraper_name}, status={self.status})>"


class APIQuotaUsage(Base):
    """Tracks API quota usage for external services."""

    __tablename__ = "api_quota_usage"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    api_name: Mapped[str] = mapped_column(String(50), nullable=False, index=True)
    metric_name: Mapped[str] = mapped_column(String(50), nullable=False, comment="requests, tokens, cost_usd")
    value: Mapped[Decimal] = mapped_column(Numeric(12, 4), nullable=False)
    period_start: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    period_end: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    recorded_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    def __repr__(self) -> str:
        return f"<APIQuotaUsage(api={self.api_name}, metric={self.metric_name}, value={self.value})>"


class AdminAlert(Base):
    """Alert configuration for monitoring thresholds."""

    __tablename__ = "admin_alerts"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_name: Mapped[str] = mapped_column(String(100), nullable=False)
    alert_type: Mapped[str] = mapped_column(String(50), nullable=False, comment="threshold, anomaly, failure")
    metric_name: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False)
    severity: Mapped[str] = mapped_column(String(20), default="warning", nullable=False)
    notification_channels: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False, index=True)
    created_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    creator: Mapped["User | None"] = relationship("User", foreign_keys=[created_by], lazy="selectin")
    incidents: Mapped[list["AdminAlertIncident"]] = relationship("AdminAlertIncident", back_populates="alert", cascade="all, delete-orphan")

    def __repr__(self) -> str:
        return f"<AdminAlert(name={self.alert_name}, severity={self.severity}, active={self.is_active})>"


class AdminAlertIncident(Base):
    """Individual alert incident when threshold is breached."""

    __tablename__ = "admin_alert_incidents"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    alert_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("admin_alerts.id", ondelete="CASCADE"), nullable=False)
    triggered_value: Mapped[Decimal | None] = mapped_column(Numeric(12, 4), nullable=True)
    status: Mapped[str] = mapped_column(String(20), default="open", nullable=False, comment="open, acknowledged, resolved")
    acknowledged_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    resolved_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    alert: Mapped["AdminAlert"] = relationship("AdminAlert", back_populates="incidents", lazy="selectin")
    acknowledger: Mapped["User | None"] = relationship("User", foreign_keys=[acknowledged_by], lazy="selectin")

    def __repr__(self) -> str:
        return f"<AdminAlertIncident(alert_id={self.alert_id}, status={self.status})>"
