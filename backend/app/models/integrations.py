"""Integration models for Phase 10: Integration Ecosystem.

Provides:
- ExternalIntegration: Connected services (Notion, Airtable, Slack)
- IntegrationWebhook: Webhook endpoints for external services
- IntegrationSync: Sync status tracking
- BrowserExtensionToken: Chrome extension authentication
- BotSubscription: Slack/Discord bot subscriptions
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


class ExternalIntegration(Base):
    """External service integration (Notion, Airtable, Slack, etc.)."""

    __tablename__ = "external_integrations"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Service info
    service_type: Mapped[str] = mapped_column(String(50), nullable=False)
    service_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # OAuth tokens (encrypted in practice)
    access_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    refresh_token: Mapped[str | None] = mapped_column(Text, nullable=True)
    token_expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Workspace info
    workspace_id: Mapped[str | None] = mapped_column(String(255), nullable=True)
    workspace_name: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Service-specific config
    config: Mapped[dict[str, Any] | None] = mapped_column(JSONB, nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_sync_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    sync_error: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")
    webhooks: Mapped[list["IntegrationWebhook"]] = relationship("IntegrationWebhook", back_populates="integration", cascade="all, delete-orphan", lazy="selectin")
    syncs: Mapped[list["IntegrationSync"]] = relationship("IntegrationSync", back_populates="integration", cascade="all, delete-orphan", lazy="selectin")
    subscriptions: Mapped[list["BotSubscription"]] = relationship("BotSubscription", back_populates="integration", cascade="all, delete-orphan", lazy="selectin")

    # Service type constants
    SERVICE_NOTION = "notion"
    SERVICE_AIRTABLE = "airtable"
    SERVICE_SLACK = "slack"
    SERVICE_DISCORD = "discord"
    SERVICE_LINEAR = "linear"
    SERVICE_JIRA = "jira"

    def __repr__(self) -> str:
        return f"<ExternalIntegration(service={self.service_type}, user={self.user_id})>"


class IntegrationWebhook(Base):
    """Webhook endpoint for external service notifications."""

    __tablename__ = "integration_webhooks"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    integration_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False)

    # Webhook config
    webhook_type: Mapped[str] = mapped_column(String(50), nullable=False)
    webhook_url: Mapped[str] = mapped_column(String(500), nullable=False)
    secret: Mapped[str | None] = mapped_column(String(255), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_triggered_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    failure_count: Mapped[int] = mapped_column(Integer, default=0, nullable=False)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    integration: Mapped["ExternalIntegration"] = relationship("ExternalIntegration", back_populates="webhooks")

    # Webhook type constants
    TYPE_NEW_INSIGHT = "new_insight"
    TYPE_INSIGHT_UPDATE = "insight_update"
    TYPE_RESEARCH_COMPLETE = "research_complete"
    TYPE_TRENDING_ALERT = "trending_alert"

    def __repr__(self) -> str:
        return f"<IntegrationWebhook(type={self.webhook_type}, integration={self.integration_id})>"


class IntegrationSync(Base):
    """Sync operation log for integrations."""

    __tablename__ = "integration_syncs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    integration_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False)

    # Sync details
    sync_type: Mapped[str] = mapped_column(String(50), nullable=False)
    status: Mapped[str] = mapped_column(String(20), nullable=False)
    items_synced: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    items_failed: Mapped[int] = mapped_column(Integer, default=0, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)

    # Timestamps
    started_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    integration: Mapped["ExternalIntegration"] = relationship("ExternalIntegration", back_populates="syncs")

    # Sync type constants
    TYPE_FULL = "full"
    TYPE_INCREMENTAL = "incremental"
    TYPE_WEBHOOK = "webhook"

    # Status constants
    STATUS_STARTED = "started"
    STATUS_COMPLETED = "completed"
    STATUS_FAILED = "failed"

    def __repr__(self) -> str:
        return f"<IntegrationSync(type={self.sync_type}, status={self.status})>"


class BrowserExtensionToken(Base):
    """Authentication token for browser extension."""

    __tablename__ = "browser_extension_tokens"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    user_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    # Token info
    token_hash: Mapped[str] = mapped_column(String(64), unique=True, nullable=False)
    device_name: Mapped[str | None] = mapped_column(String(100), nullable=True)
    browser: Mapped[str | None] = mapped_column(String(50), nullable=True)

    # Usage tracking
    last_used_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    last_ip: Mapped[str | None] = mapped_column(String(45), nullable=True)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    expires_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Relationships
    user: Mapped["User"] = relationship("User", foreign_keys=[user_id], lazy="selectin")

    # Browser constants
    BROWSER_CHROME = "chrome"
    BROWSER_FIREFOX = "firefox"
    BROWSER_EDGE = "edge"
    BROWSER_SAFARI = "safari"

    def __repr__(self) -> str:
        return f"<BrowserExtensionToken(user={self.user_id}, browser={self.browser})>"


class BotSubscription(Base):
    """Slack/Discord bot subscription for notifications."""

    __tablename__ = "bot_subscriptions"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True, default=uuid4)
    integration_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("external_integrations.id", ondelete="CASCADE"), nullable=False)

    # Channel info
    channel_id: Mapped[str] = mapped_column(String(100), nullable=False)
    channel_name: Mapped[str | None] = mapped_column(String(100), nullable=True)

    # Subscription config
    subscription_type: Mapped[str] = mapped_column(String(50), nullable=False)
    keywords: Mapped[list[str] | None] = mapped_column(JSONB, nullable=True)
    min_score: Mapped[Decimal | None] = mapped_column(Numeric(3, 2), nullable=True)
    frequency: Mapped[str] = mapped_column(String(20), default="instant", nullable=False)

    # Status
    is_active: Mapped[bool] = mapped_column(Boolean, default=True, nullable=False)
    last_notified_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)

    # Timestamp
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now(), nullable=False)

    # Relationships
    integration: Mapped["ExternalIntegration"] = relationship("ExternalIntegration", back_populates="subscriptions")

    # Subscription type constants
    TYPE_KEYWORD = "keyword"
    TYPE_TRENDING = "trending"
    TYPE_NEW_INSIGHTS = "new_insights"
    TYPE_HIGH_SCORE = "high_score"

    # Frequency constants
    FREQ_INSTANT = "instant"
    FREQ_DAILY = "daily"
    FREQ_WEEKLY = "weekly"

    def __repr__(self) -> str:
        return f"<BotSubscription(type={self.subscription_type}, channel={self.channel_id})>"
