"""Payment Service - Phase 6.1 Stripe Integration.

Handles subscription management, checkout sessions, and webhooks.
"""

import logging
from datetime import datetime
from typing import Any
from urllib.parse import urlparse

from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Pricing Configuration
# ============================================================


class PricingTier(BaseModel):
    """Pricing tier definition."""

    name: str
    price_monthly: int  # In cents
    price_yearly: int  # In cents (with discount)
    features: list[str]
    limits: dict[str, int]  # analyses_per_month, api_calls_per_hour, etc.


PRICING_TIERS: dict[str, PricingTier] = {
    "free": PricingTier(
        name="Free",
        price_monthly=0,
        price_yearly=0,
        features=[
            "5 insights per day",
            "1 research analysis per month",
            "Basic export (CSV)",
            "Community support",
        ],
        limits={
            "insights_per_day": 5,
            "analyses_per_month": 1,
            "api_calls_per_hour": 10,
            "team_members": 0,
        },
    ),
    "starter": PricingTier(
        name="Starter",
        price_monthly=1900,  # $19/mo
        price_yearly=15900,  # $159/yr (save 30%)
        features=[
            "Unlimited insights",
            "3 research analyses per month",
            "Full export (PDF, CSV, JSON)",
            "Email notifications",
            "Email support",
        ],
        limits={
            "insights_per_day": -1,  # Unlimited
            "analyses_per_month": 3,
            "api_calls_per_hour": 100,
            "team_members": 3,
        },
    ),
    "pro": PricingTier(
        name="Pro",
        price_monthly=4900,  # $49/mo
        price_yearly=39900,  # $399/yr (save 30%)
        features=[
            "Everything in Starter",
            "10 research analyses per month",
            "Brand package generator",
            "Landing page generator",
            "Real-time feed access",
            "API access",
            "Priority support",
        ],
        limits={
            "insights_per_day": -1,
            "analyses_per_month": 10,
            "api_calls_per_hour": 500,
            "team_members": 10,
        },
    ),
    "enterprise": PricingTier(
        name="Enterprise",
        price_monthly=19900,  # $199/mo
        price_yearly=159900,  # $1599/yr
        features=[
            "Everything in Pro",
            "Unlimited research analyses",
            "White-label branding",
            "Custom domain",
            "Dedicated account manager",
            "SLA guarantee",
        ],
        limits={
            "insights_per_day": -1,
            "analyses_per_month": -1,
            "api_calls_per_hour": 2000,
            "team_members": -1,
        },
    ),
}


# ============================================================
# Payment Service Functions
# ============================================================


def get_stripe_client():
    """Get Stripe client instance."""
    try:
        import stripe
        stripe.api_key = settings.stripe_secret_key
        return stripe
    except ImportError:
        logger.warning("Stripe not installed")
        return None


async def create_checkout_session(
    user_id: str,
    tier: str,
    success_url: str,
    cancel_url: str,
    billing_cycle: str = "monthly",
) -> dict[str, Any] | None:
    """
    Create a Stripe checkout session for subscription.

    Args:
        user_id: User's UUID
        tier: Pricing tier (starter, pro, enterprise)
        success_url: Redirect URL on successful payment (must be HTTPS in production)
        cancel_url: Redirect URL on cancelled payment (must be HTTPS in production)
        billing_cycle: monthly or yearly

    Returns:
        Checkout session data with URL, or None if failed

    Raises:
        ValueError: If URLs are invalid or Stripe not configured in production
    """
    # ✅ URL VALIDATION - Prevent phishing attacks
    if settings.environment == "production":
        if not success_url.startswith("https://"):
            raise ValueError("success_url must use HTTPS in production")
        if not cancel_url.startswith("https://"):
            raise ValueError("cancel_url must use HTTPS in production")

        # Validate URLs belong to allowed domains (prevent open redirect attacks)
        allowed_origins = settings.cors_origins_list
        allowed_hosts = {urlparse(origin).hostname for origin in allowed_origins if urlparse(origin).hostname}
        success_host = urlparse(success_url).hostname
        cancel_host = urlparse(cancel_url).hostname

        if success_host not in allowed_hosts:
            raise ValueError(f"success_url domain not in allowed CORS origins: {success_host}")
        if cancel_host not in allowed_hosts:
            raise ValueError(f"cancel_url domain not in allowed CORS origins: {cancel_host}")

    stripe = get_stripe_client()
    if not stripe or not settings.stripe_secret_key:
        if settings.environment == "production":
            raise ValueError("Stripe not configured - cannot process payments in production")

        logger.warning("Stripe not configured, returning mock checkout (development only)")
        return {
            "id": "mock_session_id",
            "url": success_url,
            "status": "mock",
        }

    try:
        # Get price ID based on tier and billing cycle
        price_id = _get_price_id(tier, billing_cycle)
        if not price_id:
            logger.error(f"No price ID configured for tier: {tier}")
            return None

        session = stripe.checkout.Session.create(
            mode="subscription",
            payment_method_types=["card"],
            line_items=[{"price": price_id, "quantity": 1}],
            success_url=success_url,
            cancel_url=cancel_url,
            client_reference_id=user_id,
            metadata={"user_id": user_id, "tier": tier},
            allow_promotion_codes=True,
        )

        logger.info(f"Created checkout session for user {user_id}, tier {tier}")
        return {
            "id": session.id,
            "url": session.url,
            "status": session.status,
        }

    except Exception as e:
        logger.error(f"Failed to create checkout session: {e}")
        return None


async def create_customer_portal_session(
    stripe_customer_id: str,
    return_url: str,
) -> dict[str, Any] | None:
    """
    Create a Stripe customer portal session for managing subscriptions.

    Args:
        stripe_customer_id: Stripe customer ID
        return_url: URL to return to after portal session

    Returns:
        Portal session data with URL, or None if failed
    """
    stripe = get_stripe_client()
    if not stripe or not settings.stripe_secret_key:
        return {"url": return_url, "status": "mock"}

    try:
        session = stripe.billing_portal.Session.create(
            customer=stripe_customer_id,
            return_url=return_url,
        )

        return {
            "id": session.id,
            "url": session.url,
        }

    except Exception as e:
        logger.error(f"Failed to create portal session: {e}")
        return None


async def handle_webhook_event(
    payload: bytes,
    signature: str,
    db: AsyncSession,
) -> dict[str, Any]:
    """
    Process Stripe webhook event with idempotency protection.

    Uses webhook_events table to ensure exactly-once processing.
    Stripe guarantees at-least-once delivery, so we must prevent duplicate processing.

    Args:
        payload: Raw webhook payload
        signature: Stripe signature header
        db: Database session for transaction

    Returns:
        Processing result with event type and status
    """
    stripe = get_stripe_client()
    if not stripe or not settings.stripe_webhook_secret:
        # CRITICAL: Fail hard in production to prevent webhook forgery
        if settings.environment == "production":
            logger.error("Stripe webhook secret not configured in production!")
            raise ValueError("STRIPE_WEBHOOK_SECRET is required in production")

        # Development only: allow skip with warning
        logger.warning("Stripe webhooks not configured - development mode only")
        return {"status": "skipped", "reason": "not_configured"}

    try:
        # Verify webhook signature (prevents forgery)
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )

        event_id = event["id"]
        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing Stripe webhook: {event_type} (event_id: {event_id})")

        # ✅ IDEMPOTENCY CHECK - Prevent duplicate processing
        from app.models.webhook_event import WebhookEvent

        # Check if event already processed
        result = await db.execute(
            select(WebhookEvent).where(WebhookEvent.stripe_event_id == event_id)
        )
        existing_event = result.scalar_one_or_none()

        if existing_event:
            logger.info(f"Webhook event {event_id} already processed, skipping")
            return {
                "status": "duplicate",
                "event_id": event_id,
                "event_type": event_type,
                "processed_at": existing_event.processed_at.isoformat(),
            }

        # Process event based on type
        processing_result = {}
        try:
            if event_type == "checkout.session.completed":
                processing_result = await _handle_checkout_completed(event_data, db)
            elif event_type == "customer.subscription.updated":
                processing_result = await _handle_subscription_updated(event_data, db)
            elif event_type == "customer.subscription.deleted":
                processing_result = await _handle_subscription_deleted(event_data, db)
            elif event_type == "invoice.paid":
                processing_result = await _handle_invoice_paid(event_data, db)
            elif event_type == "invoice.payment_failed":
                processing_result = await _handle_payment_failed(event_data, db)
            else:
                logger.info(f"Unhandled webhook event: {event_type}")
                processing_result = {"status": "ignored", "event_type": event_type}

            # ✅ RECORD EVENT - Mark as processed
            webhook_event = WebhookEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                status="processed",
                payload=event,
                result=processing_result,
            )
            db.add(webhook_event)
            await db.commit()

            logger.info(f"Webhook event {event_id} processed successfully")
            return processing_result

        except Exception as handler_error:
            # Record failed processing attempt
            webhook_event = WebhookEvent(
                stripe_event_id=event_id,
                event_type=event_type,
                status="failed",
                payload=event,
                error_message=str(handler_error),
            )
            db.add(webhook_event)
            await db.commit()

            logger.error(f"Webhook handler failed: {handler_error}", exc_info=True)
            raise

    except stripe.error.SignatureVerificationError as e:
        logger.error(f"Invalid webhook signature: {e}")
        return {"status": "error", "error": "invalid_signature"}
    except Exception as e:
        logger.error(f"Webhook processing failed: {e}", exc_info=True)
        await db.rollback()
        return {"status": "error", "error": str(e)}


# ============================================================
# Webhook Handlers
# ============================================================


async def _handle_checkout_completed(data: dict, db: AsyncSession) -> dict:
    """Handle successful checkout completion - create/update subscription."""
    from app.models.subscription import Subscription
    from app.models.user import User

    user_id = data.get("client_reference_id")
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")
    tier = data.get("metadata", {}).get("tier", "starter")

    if not user_id or not customer_id:
        raise ValueError("Missing user_id or customer_id in checkout session")

    logger.info(f"Checkout completed for user {user_id}, tier {tier}")

    # Get user
    result = await db.execute(select(User).where(User.id == user_id))
    user = result.scalar_one_or_none()

    if not user:
        raise ValueError(f"User {user_id} not found")

    # Create or update subscription (atomic upsert)
    stmt = insert(Subscription).values(
        user_id=user_id,
        stripe_customer_id=customer_id,
        stripe_subscription_id=subscription_id,
        tier=tier,
        status="active",
        subscription_metadata=data.get("metadata", {}),
    ).on_conflict_do_update(
        index_elements=["user_id"],
        set_={
            "stripe_customer_id": customer_id,
            "stripe_subscription_id": subscription_id,
            "tier": tier,
            "status": "active",
            "subscription_metadata": data.get("metadata", {}),
        }
    )

    await db.execute(stmt)
    await db.commit()

    logger.info(f"Subscription activated for user {user_id}: {tier}")

    return {
        "status": "processed",
        "event_type": "checkout.session.completed",
        "user_id": user_id,
        "customer_id": customer_id,
        "subscription_id": subscription_id,
        "tier": tier,
    }


async def _handle_subscription_updated(data: dict, db: AsyncSession) -> dict:
    """Handle subscription update (upgrade/downgrade/status change)."""
    from app.models.subscription import Subscription

    stripe_subscription_id = data.get("id")
    status = data.get("status")
    current_period_start = datetime.fromtimestamp(data.get("current_period_start", 0))
    current_period_end = datetime.fromtimestamp(data.get("current_period_end", 0))
    cancel_at_period_end = data.get("cancel_at_period_end", False)

    logger.info(f"Subscription {stripe_subscription_id} updated to {status}")

    # Find subscription by stripe_subscription_id
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription {stripe_subscription_id} not found in database")
        return {"status": "skipped", "reason": "subscription_not_found"}

    # Update subscription status and billing cycle
    subscription.status = status
    subscription.current_period_start = current_period_start
    subscription.current_period_end = current_period_end
    subscription.cancel_at_period_end = cancel_at_period_end

    await db.commit()

    logger.info(f"Subscription {stripe_subscription_id} updated in database")

    return {
        "status": "processed",
        "event_type": "customer.subscription.updated",
        "subscription_id": stripe_subscription_id,
        "subscription_status": status,
    }


async def _handle_subscription_deleted(data: dict, db: AsyncSession) -> dict:
    """Handle subscription cancellation."""
    from app.models.subscription import Subscription

    stripe_subscription_id = data.get("id")
    canceled_at = datetime.fromtimestamp(data.get("canceled_at", 0)) if data.get("canceled_at") else datetime.utcnow()

    logger.info(f"Subscription {stripe_subscription_id} cancelled")

    # Find and update subscription
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_subscription_id == stripe_subscription_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription {stripe_subscription_id} not found in database")
        return {"status": "skipped", "reason": "subscription_not_found"}

    # Mark as canceled and downgrade to free tier
    subscription.status = "canceled"
    subscription.tier = "free"
    subscription.canceled_at = canceled_at
    subscription.stripe_subscription_id = None  # Clear subscription ID

    await db.commit()

    logger.info(f"Subscription {stripe_subscription_id} canceled, user downgraded to free tier")

    return {
        "status": "processed",
        "event_type": "customer.subscription.deleted",
        "subscription_id": stripe_subscription_id,
    }


async def _handle_invoice_paid(data: dict, db: AsyncSession) -> dict:
    """Handle successful invoice payment - record in payment history."""
    from app.models.subscription import PaymentHistory, Subscription

    invoice_id = data.get("id")
    customer_id = data.get("customer")
    amount_paid = data.get("amount_paid", 0)
    currency = data.get("currency", "usd")
    subscription_id = data.get("subscription")

    logger.info(f"Invoice {invoice_id} paid: ${amount_paid/100:.2f} {currency.upper()}")

    # Find subscription by stripe_customer_id
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription for customer {customer_id} not found")
        return {"status": "skipped", "reason": "subscription_not_found"}

    # Record payment in history
    payment_record = PaymentHistory(
        subscription_id=subscription.id,
        stripe_invoice_id=invoice_id,
        amount=amount_paid,
        currency=currency,
        status="succeeded",
        description=f"Subscription payment for {subscription.tier} tier",
    )
    db.add(payment_record)
    await db.commit()

    logger.info(f"Payment recorded for subscription {subscription.id}: ${amount_paid/100:.2f}")

    return {
        "status": "processed",
        "event_type": "invoice.paid",
        "invoice_id": invoice_id,
        "amount_cents": amount_paid,
    }


async def _handle_payment_failed(data: dict, db: AsyncSession) -> dict:
    """Handle failed payment - update subscription status."""
    from app.models.subscription import PaymentHistory, Subscription

    invoice_id = data.get("id")
    customer_id = data.get("customer")
    amount_due = data.get("amount_due", 0)

    logger.warning(f"Payment failed for invoice {invoice_id}")

    # Find subscription by stripe_customer_id
    result = await db.execute(
        select(Subscription).where(Subscription.stripe_customer_id == customer_id)
    )
    subscription = result.scalar_one_or_none()

    if not subscription:
        logger.warning(f"Subscription for customer {customer_id} not found")
        return {"status": "skipped", "reason": "subscription_not_found"}

    # Update subscription status to past_due
    subscription.status = "past_due"

    # Record failed payment attempt
    payment_record = PaymentHistory(
        subscription_id=subscription.id,
        stripe_invoice_id=invoice_id,
        amount=amount_due,
        currency="usd",
        status="failed",
        description=f"Failed payment for {subscription.tier} tier",
    )
    db.add(payment_record)
    await db.commit()

    logger.warning(f"Subscription {subscription.id} marked as past_due due to failed payment")

    return {
        "status": "processed",
        "event_type": "invoice.payment_failed",
        "invoice_id": invoice_id,
    }


# ============================================================
# Helper Functions
# ============================================================


def _get_price_id(tier: str, billing_cycle: str) -> str | None:
    """Get Stripe price ID for tier and billing cycle."""
    price_map = {
        ("starter", "monthly"): settings.stripe_price_starter,
        ("pro", "monthly"): settings.stripe_price_pro,
        # Add yearly prices when configured
    }
    return price_map.get((tier, billing_cycle))


def get_tier_limits(tier: str) -> dict[str, int]:
    """Get limits for a subscription tier. Falls back to free tier if unknown."""
    return PRICING_TIERS.get(tier, PRICING_TIERS["free"]).limits


def check_tier_limit(tier: str, limit_name: str, current_usage: int) -> bool:
    """
    Check if usage is within tier limits.

    Returns True if within limits, False if exceeded.
    """
    limits = get_tier_limits(tier)
    limit = limits.get(limit_name, 0)

    # -1 means unlimited
    if limit == -1:
        return True

    return current_usage < limit
