"""Integration API routes - Phase 10: Integration Ecosystem.

Provides endpoints for:
- External integrations (Notion, Airtable, Slack, etc.)
- Browser extension support
- Webhook management
- Bot subscriptions
"""

import hashlib
import logging
import secrets
from datetime import UTC, datetime, timedelta
from typing import Annotated, Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request
from pydantic import BaseModel, ConfigDict, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models.integrations import (
    BotSubscription,
    BrowserExtensionToken,
    ExternalIntegration,
    IntegrationSync,
    IntegrationWebhook,
)
from app.models.user import User

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/integrations", tags=["Integrations"])


# ============================================
# Schemas
# ============================================

class IntegrationCreate(BaseModel):
    service_type: str = Field(..., pattern="^(notion|airtable|slack|discord|linear|jira)$")
    service_name: str | None = Field(None, max_length=100)
    access_token: str | None = None
    workspace_id: str | None = None
    workspace_name: str | None = None
    config: dict[str, Any] | None = None


class IntegrationResponse(BaseModel):
    id: UUID
    user_id: UUID
    service_type: str
    service_name: str | None
    workspace_id: str | None
    workspace_name: str | None
    is_active: bool
    last_sync_at: datetime | None
    sync_error: str | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class IntegrationUpdate(BaseModel):
    service_name: str | None = Field(None, max_length=100)
    is_active: bool | None = None
    config: dict[str, Any] | None = None


class WebhookCreate(BaseModel):
    webhook_type: str = Field(..., pattern="^(new_insight|insight_update|research_complete|trending_alert)$")
    webhook_url: str = Field(..., max_length=500)


class WebhookResponse(BaseModel):
    id: UUID
    integration_id: UUID
    webhook_type: str
    webhook_url: str
    is_active: bool
    last_triggered_at: datetime | None
    failure_count: int
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class ExtensionTokenResponse(BaseModel):
    id: UUID
    token: str  # Only returned on creation
    device_name: str | None
    browser: str | None
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime
    expires_at: datetime | None


class ExtensionTokenInfo(BaseModel):
    id: UUID
    device_name: str | None
    browser: str | None
    last_used_at: datetime | None
    is_active: bool
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class BotSubscriptionCreate(BaseModel):
    channel_id: str = Field(..., max_length=100)
    channel_name: str | None = Field(None, max_length=100)
    subscription_type: str = Field(..., pattern="^(keyword|trending|new_insights|high_score)$")
    keywords: list[str] | None = Field(None, max_length=10)
    min_score: float | None = Field(None, ge=0.0, le=1.0)
    frequency: str = Field(default="instant", pattern="^(instant|daily|weekly)$")


class BotSubscriptionResponse(BaseModel):
    id: UUID
    integration_id: UUID
    channel_id: str
    channel_name: str | None
    subscription_type: str
    keywords: list[str] | None
    min_score: float | None
    frequency: str
    is_active: bool
    last_notified_at: datetime | None
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SyncHistoryResponse(BaseModel):
    id: UUID
    sync_type: str
    status: str
    items_synced: int
    items_failed: int
    error_message: str | None
    started_at: datetime
    completed_at: datetime | None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Integration Endpoints
# ============================================

@router.get("", response_model=list[IntegrationResponse])
async def list_integrations(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    service_type: str | None = None,
):
    """List user's external integrations."""
    query = select(ExternalIntegration).where(ExternalIntegration.user_id == current_user.id)

    if service_type:
        query = query.where(ExternalIntegration.service_type == service_type)

    result = await db.execute(query.order_by(ExternalIntegration.created_at.desc()))
    return [IntegrationResponse.model_validate(i) for i in result.scalars().all()]


@router.post("", response_model=IntegrationResponse)
async def create_integration(
    integration: IntegrationCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a new external integration."""
    new_integration = ExternalIntegration(
        user_id=current_user.id,
        service_type=integration.service_type,
        service_name=integration.service_name,
        access_token=integration.access_token,
        workspace_id=integration.workspace_id,
        workspace_name=integration.workspace_name,
        config=integration.config,
    )
    db.add(new_integration)
    await db.commit()
    await db.refresh(new_integration)

    logger.info(f"User {current_user.id} created {integration.service_type} integration")
    return IntegrationResponse.model_validate(new_integration)


@router.get("/{integration_id}", response_model=IntegrationResponse)
async def get_integration(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Get an integration by ID."""
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    return IntegrationResponse.model_validate(integration)


@router.patch("/{integration_id}", response_model=IntegrationResponse)
async def update_integration(
    integration_id: UUID,
    updates: IntegrationUpdate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Update an integration."""
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    update_dict = updates.model_dump(exclude_unset=True)
    for key, value in update_dict.items():
        setattr(integration, key, value)

    integration.updated_at = datetime.now(UTC)
    await db.commit()
    await db.refresh(integration)

    return IntegrationResponse.model_validate(integration)


@router.delete("/{integration_id}")
async def delete_integration(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete an integration and all associated data."""
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    await db.delete(integration)
    await db.commit()

    logger.info(f"User {current_user.id} deleted integration {integration_id}")
    return {"status": "deleted"}


# ============================================
# Webhook Endpoints
# ============================================

@router.post("/{integration_id}/webhooks", response_model=WebhookResponse)
async def create_webhook(
    integration_id: UUID,
    webhook: WebhookCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a webhook for an integration."""
    # Verify integration ownership
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")

    # Generate webhook secret
    secret = secrets.token_urlsafe(32)

    new_webhook = IntegrationWebhook(
        integration_id=integration_id,
        webhook_type=webhook.webhook_type,
        webhook_url=webhook.webhook_url,
        secret=secret,
    )
    db.add(new_webhook)
    await db.commit()
    await db.refresh(new_webhook)

    return WebhookResponse.model_validate(new_webhook)


@router.get("/{integration_id}/webhooks", response_model=list[WebhookResponse])
async def list_webhooks(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List webhooks for an integration."""
    # Verify integration ownership
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")

    result = await db.execute(
        select(IntegrationWebhook).where(IntegrationWebhook.integration_id == integration_id)
    )
    return [WebhookResponse.model_validate(w) for w in result.scalars().all()]


@router.delete("/webhooks/{webhook_id}")
async def delete_webhook(
    webhook_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a webhook."""
    result = await db.execute(
        select(IntegrationWebhook)
        .join(ExternalIntegration)
        .where(
            IntegrationWebhook.id == webhook_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    webhook = result.scalar_one_or_none()

    if not webhook:
        raise HTTPException(status_code=404, detail="Webhook not found")

    await db.delete(webhook)
    await db.commit()

    return {"status": "deleted"}


# ============================================
# Browser Extension Endpoints
# ============================================

@router.post("/extension/token", response_model=ExtensionTokenResponse)
async def create_extension_token(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    request: Request,
    device_name: str = None,
    browser: str = None,
):
    """Create a new browser extension token."""
    # Generate token
    token = secrets.token_urlsafe(32)
    token_hash = hashlib.sha256(token.encode()).hexdigest()

    new_token = BrowserExtensionToken(
        user_id=current_user.id,
        token_hash=token_hash,
        device_name=device_name,
        browser=browser,
        last_ip=request.client.host if request.client else None,
        expires_at=datetime.now(UTC) + timedelta(days=365),  # 1 year expiry
    )
    db.add(new_token)
    await db.commit()
    await db.refresh(new_token)

    logger.info(f"User {current_user.id} created extension token for {browser or 'unknown browser'}")

    return ExtensionTokenResponse(
        id=new_token.id,
        token=token,  # Only returned once
        device_name=new_token.device_name,
        browser=new_token.browser,
        last_used_at=new_token.last_used_at,
        is_active=new_token.is_active,
        created_at=new_token.created_at,
        expires_at=new_token.expires_at,
    )


@router.get("/extension/tokens", response_model=list[ExtensionTokenInfo])
async def list_extension_tokens(
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List user's extension tokens (without actual token values)."""
    result = await db.execute(
        select(BrowserExtensionToken)
        .where(BrowserExtensionToken.user_id == current_user.id)
        .order_by(BrowserExtensionToken.created_at.desc())
    )
    return [ExtensionTokenInfo.model_validate(t) for t in result.scalars().all()]


@router.delete("/extension/tokens/{token_id}")
async def revoke_extension_token(
    token_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Revoke an extension token."""
    result = await db.execute(
        select(BrowserExtensionToken).where(
            BrowserExtensionToken.id == token_id,
            BrowserExtensionToken.user_id == current_user.id,
        )
    )
    token = result.scalar_one_or_none()

    if not token:
        raise HTTPException(status_code=404, detail="Token not found")

    token.is_active = False
    await db.commit()

    logger.info(f"User {current_user.id} revoked extension token {token_id}")
    return {"status": "revoked"}


# ============================================
# Bot Subscription Endpoints
# ============================================

@router.post("/{integration_id}/subscriptions", response_model=BotSubscriptionResponse)
async def create_bot_subscription(
    integration_id: UUID,
    subscription: BotSubscriptionCreate,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Create a bot subscription for Slack/Discord."""
    # Verify integration ownership and is Slack/Discord
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")
    if integration.service_type not in ("slack", "discord"):
        raise HTTPException(status_code=400, detail="Subscriptions only supported for Slack/Discord")

    from decimal import Decimal
    new_subscription = BotSubscription(
        integration_id=integration_id,
        channel_id=subscription.channel_id,
        channel_name=subscription.channel_name,
        subscription_type=subscription.subscription_type,
        keywords=subscription.keywords,
        min_score=Decimal(str(subscription.min_score)) if subscription.min_score else None,
        frequency=subscription.frequency,
    )
    db.add(new_subscription)
    await db.commit()
    await db.refresh(new_subscription)

    return BotSubscriptionResponse.model_validate(new_subscription)


@router.get("/{integration_id}/subscriptions", response_model=list[BotSubscriptionResponse])
async def list_bot_subscriptions(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """List bot subscriptions for an integration."""
    # Verify integration ownership
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")

    result = await db.execute(
        select(BotSubscription).where(BotSubscription.integration_id == integration_id)
    )
    return [BotSubscriptionResponse.model_validate(s) for s in result.scalars().all()]


@router.delete("/subscriptions/{subscription_id}")
async def delete_bot_subscription(
    subscription_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
):
    """Delete a bot subscription."""
    result = await db.execute(
        select(BotSubscription)
        .join(ExternalIntegration)
        .where(
            BotSubscription.id == subscription_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        raise HTTPException(status_code=404, detail="Subscription not found")

    await db.delete(subscription)
    await db.commit()

    return {"status": "deleted"}


# ============================================
# Sync History Endpoints
# ============================================

@router.get("/{integration_id}/syncs", response_model=list[SyncHistoryResponse])
async def list_sync_history(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    limit: int = Query(20, le=100),
):
    """List sync history for an integration."""
    # Verify integration ownership
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    if not result.scalar_one_or_none():
        raise HTTPException(status_code=404, detail="Integration not found")

    result = await db.execute(
        select(IntegrationSync)
        .where(IntegrationSync.integration_id == integration_id)
        .order_by(IntegrationSync.started_at.desc())
        .limit(limit)
    )
    return [SyncHistoryResponse.model_validate(s) for s in result.scalars().all()]


@router.post("/{integration_id}/sync")
async def trigger_sync(
    integration_id: UUID,
    db: Annotated[AsyncSession, Depends(get_db)],
    current_user: Annotated[User, Depends(get_current_user)],
    sync_type: str = "incremental",
):
    """Trigger a manual sync for an integration."""
    # Verify integration ownership
    result = await db.execute(
        select(ExternalIntegration).where(
            ExternalIntegration.id == integration_id,
            ExternalIntegration.user_id == current_user.id,
        )
    )
    integration = result.scalar_one_or_none()

    if not integration:
        raise HTTPException(status_code=404, detail="Integration not found")

    # Create sync record
    sync = IntegrationSync(
        integration_id=integration_id,
        sync_type=sync_type,
        status=IntegrationSync.STATUS_STARTED,
    )
    db.add(sync)
    await db.commit()
    await db.refresh(sync)

    # TODO: Queue actual sync job via Arq
    logger.info(f"User {current_user.id} triggered {sync_type} sync for integration {integration_id}")

    return {"status": "started", "sync_id": str(sync.id)}
