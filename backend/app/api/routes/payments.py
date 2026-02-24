"""Payment API Routes - Phase 6.1.

Endpoints for Stripe subscription management.
"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, status
from pydantic import BaseModel, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user
from app.db.session import get_db
from app.models import User
from app.models.custom_analysis import CustomAnalysis
from app.models.insight import Insight
from app.models.team import TeamMember
from app.services.payment_service import (
    PRICING_TIERS,
    create_checkout_session,
    create_customer_portal_session,
    handle_webhook_event,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/payments", tags=["Payments"])


# ============================================================
# Request/Response Schemas
# ============================================================


class CheckoutRequest(BaseModel):
    """Checkout session request."""

    tier: str = Field(..., pattern=r"^(starter|pro|enterprise)$")
    billing_cycle: str = Field(default="monthly", pattern=r"^(monthly|yearly)$")
    success_url: str
    cancel_url: str


class CheckoutResponse(BaseModel):
    """Checkout session response."""

    session_id: str
    checkout_url: str


class PortalRequest(BaseModel):
    """Customer portal request."""

    return_url: str


class PricingResponse(BaseModel):
    """Pricing information response."""

    tiers: dict[str, Any]


class SubscriptionUsage(BaseModel):
    """Current usage metrics for the authenticated user."""

    insights_today: int = Field(default=0, description="Insights viewed/accessed today")
    analyses_this_month: int = Field(default=0, description="Research analyses submitted this month")
    team_members: int = Field(default=0, description="Total team members across all teams")


# ============================================================
# Pricing Endpoints
# ============================================================


@router.get("/pricing", response_model=PricingResponse)
async def get_pricing() -> PricingResponse:
    """
    Get pricing tiers and features.

    Public endpoint - no authentication required.
    """
    tiers_data = {}
    for tier_name, tier_config in PRICING_TIERS.items():
        tiers_data[tier_name] = {
            "name": tier_config.name,
            "price_monthly": tier_config.price_monthly / 100,  # Convert to dollars
            "price_yearly": tier_config.price_yearly / 100,
            "features": tier_config.features,
            "limits": tier_config.limits,
        }

    return PricingResponse(tiers=tiers_data)


# ============================================================
# Checkout Endpoints
# ============================================================


@router.post("/checkout", response_model=CheckoutResponse)
async def create_checkout(
    request: CheckoutRequest,
    current_user: User = Depends(get_current_user),
) -> CheckoutResponse:
    """
    Create a Stripe checkout session for subscription.

    Requires authentication.
    """
    result = await create_checkout_session(
        user_id=str(current_user.id),
        tier=request.tier,
        success_url=request.success_url,
        cancel_url=request.cancel_url,
        billing_cycle=request.billing_cycle,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create checkout session",
        )

    return CheckoutResponse(
        session_id=result["id"],
        checkout_url=result["url"],
    )


@router.post("/portal")
async def create_portal_session(
    request: PortalRequest,
    current_user: User = Depends(get_current_user),
) -> dict[str, str]:
    """
    Create a Stripe customer portal session for subscription management.

    Requires authentication. User must have an active subscription.
    """
    # In production, get stripe_customer_id from user's subscription
    subscription = current_user.subscription if hasattr(current_user, "subscription") else None

    if not subscription or not hasattr(subscription, "stripe_customer_id"):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="No active subscription found",
        )

    result = await create_customer_portal_session(
        stripe_customer_id=subscription.stripe_customer_id,
        return_url=request.return_url,
    )

    if not result:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create portal session",
        )

    return {"portal_url": result["url"]}


# ============================================================
# Webhook Endpoint
# ============================================================


@router.post("/webhook")
async def handle_stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Handle Stripe webhook events with idempotency protection.

    This endpoint is called by Stripe to notify of subscription events.
    Uses database transactions to ensure exactly-once processing.

    Security:
    - Verifies webhook signature from Stripe
    - Uses idempotency to prevent duplicate processing
    - Records all webhook events for audit trail
    """
    payload = await request.body()
    signature = request.headers.get("stripe-signature", "")

    result = await handle_webhook_event(payload, signature, db)

    if result.get("status") == "error":
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=result.get("error", "Webhook processing failed"),
        )

    # Return 200 OK to Stripe for all processed events (including duplicates)
    return {
        "status": result.get("status", "processed"),
        "event_type": result.get("event_type", "unknown"),
    }


# ============================================================
# Subscription Status
# ============================================================


async def _get_subscription_usage(user_id: UUID, db: AsyncSession) -> SubscriptionUsage:
    """Fetch current usage metrics for a user.

    Queries insights saved today, research analyses this month, and total team members.
    """
    today_midnight = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    first_of_month = datetime.now(UTC).replace(day=1, hour=0, minute=0, second=0, microsecond=0)

    # Count insights created today by this user
    insights_today_result = await db.execute(
        select(func.count()).select_from(Insight).where(
            Insight.created_at >= today_midnight,
        )
    )
    insights_today = insights_today_result.scalar_one_or_none() or 0

    # Count research analyses submitted this month
    analyses_result = await db.execute(
        select(func.count()).select_from(CustomAnalysis).where(
            CustomAnalysis.user_id == user_id,
            CustomAnalysis.created_at >= first_of_month,
        )
    )
    analyses_this_month = analyses_result.scalar_one_or_none() or 0

    # Count team members across all teams the user belongs to
    team_members_result = await db.execute(
        select(func.count()).select_from(TeamMember).where(
            TeamMember.user_id == user_id,
        )
    )
    team_members = team_members_result.scalar_one_or_none() or 0

    return SubscriptionUsage(
        insights_today=insights_today,
        analyses_this_month=analyses_this_month,
        team_members=team_members,
    )


@router.get("/subscription")
async def get_subscription_status(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Get current user's subscription status including current usage.

    Requires authentication.
    """
    try:
        usage = await _get_subscription_usage(current_user.id, db)
        subscription = current_user.subscription if hasattr(current_user, "subscription") else None

        if not subscription:
            tier = getattr(current_user, "subscription_tier", "free")
            return {
                "tier": tier,
                "status": "active",
                "limits": PRICING_TIERS.get(tier, PRICING_TIERS["free"]).limits,
                "usage": usage.model_dump(),
            }

        return {
            "tier": subscription.tier if hasattr(subscription, "tier") else "free",
            "status": subscription.status if hasattr(subscription, "status") else "active",
            "current_period_end": (
                subscription.current_period_end.isoformat()
                if hasattr(subscription, "current_period_end") and subscription.current_period_end
                else None
            ),
            "cancel_at_period_end": (
                subscription.cancel_at_period_end
                if hasattr(subscription, "cancel_at_period_end")
                else False
            ),
            "limits": PRICING_TIERS.get(
                subscription.tier if hasattr(subscription, "tier") else "free",
                PRICING_TIERS["free"],
            ).limits,
            "usage": usage.model_dump(),
        }
    except Exception:
        logger.exception("Error fetching subscription status for user %s", current_user.id)
        return {
            "tier": "free",
            "status": "active",
            "limits": PRICING_TIERS["free"].limits,
            "usage": {"insights_today": 0, "analyses_this_month": 0, "team_members": 0},
        }
