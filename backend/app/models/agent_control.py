"""Agent Control models for Phase 8.4-8.5: AI Agent Control & Security.

Provides:
- AgentConfiguration: AI agent settings and limits
- AuditLog: Security audit trail
"""

from datetime import datetime
from decimal import Decimal
from typing import TYPE_CHECKING, Any
from uuid import UUID, uuid4

from sqlalchemy import Boolean, DateTime, ForeignKey, Integer, Numeric, String, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.dialects.postgresql import UUID as PGUUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.base import Base

if TYPE_CHECKING:
    from app.models.user import User


class AgentConfiguration(Base):
    """Configuration settings for AI agents."""

    __tablename__ = "agent_configurations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    agent_name: Mapped[str] = mapped_column(String(50), unique=True, nullable=False)
    is_enabled: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    model_name: Mapped[str] = mapped_column(String(100), default="gemini-1.5-flash", nullable=False)
    temperature: Mapped[Decimal] = mapped_column(Numeric(3, 2), default=Decimal("0.7"), nullable=False)
    max_tokens: Mapped[int] = mapped_column(Integer, default=4096, nullable=False)
    rate_limit_per_hour: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    cost_limit_daily_usd: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("50.00"), nullable=False)
    custom_prompts: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    updated_by: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    updater: Mapped["User | None"] = relationship("User", foreign_keys=[updated_by], lazy="selectin")

    def __repr__(self) -> str:
        return f"<AgentConfiguration(agent={self.agent_name}, enabled={self.is_enabled})>"


class AuditLog(Base):
    """Security audit trail for administrative actions."""

    __tablename__ = "audit_logs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL"), nullable=True)
    action: Mapped[str] = mapped_column(String(100), nullable=False, index=True)
    resource_type: Mapped[str] = mapped_column(String(50), nullable=False)
    resource_id: Mapped[UUID | None] = mapped_column(PGUUID(as_uuid=True), nullable=True)
    details: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)
    ip_address: Mapped[str | None] = mapped_column(String(45), nullable=True)
    user_agent: Mapped[str | None] = mapped_column(String(500), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User | None"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Action constants
    ACTION_LOGIN = "user.login"
    ACTION_LOGOUT = "user.logout"
    ACTION_CREATE = "resource.create"
    ACTION_UPDATE = "resource.update"
    ACTION_DELETE = "resource.delete"
    ACTION_EXPORT = "data.export"
    ACTION_IMPERSONATE = "admin.impersonate"
    ACTION_CONFIG_CHANGE = "config.change"

    def __repr__(self) -> str:
        return f"<AuditLog(action={self.action}, user={self.user_id})>"
