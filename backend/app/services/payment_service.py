"""Payment Service - Phase 6.1 Stripe Integration.

Handles subscription management, checkout sessions, and webhooks.
"""

import logging
from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field

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
        success_url: Redirect URL on successful payment
        cancel_url: Redirect URL on cancelled payment
        billing_cycle: monthly or yearly

    Returns:
        Checkout session data with URL, or None if failed
    """
    stripe = get_stripe_client()
    if not stripe or not settings.stripe_secret_key:
        logger.warning("Stripe not configured, returning mock checkout")
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
) -> dict[str, Any]:
    """
    Process Stripe webhook event.

    Args:
        payload: Raw webhook payload
        signature: Stripe signature header

    Returns:
        Processing result with event type and status
    """
    stripe = get_stripe_client()
    if not stripe or not settings.stripe_webhook_secret:
        logger.warning("Stripe webhooks not configured")
        return {"status": "skipped", "reason": "not_configured"}

    try:
        event = stripe.Webhook.construct_event(
            payload,
            signature,
            settings.stripe_webhook_secret,
        )

        event_type = event["type"]
        event_data = event["data"]["object"]

        logger.info(f"Processing Stripe webhook: {event_type}")

        # Handle different event types
        if event_type == "checkout.session.completed":
            return await _handle_checkout_completed(event_data)
        elif event_type == "customer.subscription.updated":
            return await _handle_subscription_updated(event_data)
        elif event_type == "customer.subscription.deleted":
            return await _handle_subscription_deleted(event_data)
        elif event_type == "invoice.paid":
            return await _handle_invoice_paid(event_data)
        elif event_type == "invoice.payment_failed":
            return await _handle_payment_failed(event_data)
        else:
            logger.info(f"Unhandled webhook event: {event_type}")
            return {"status": "ignored", "event_type": event_type}

    except Exception as e:
        logger.error(f"Webhook processing failed: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================
# Webhook Handlers
# ============================================================


async def _handle_checkout_completed(data: dict) -> dict:
    """Handle successful checkout completion."""
    user_id = data.get("client_reference_id")
    customer_id = data.get("customer")
    subscription_id = data.get("subscription")

    logger.info(f"Checkout completed for user {user_id}")

    # TODO: Update user subscription in database
    # This would be done by the route handler after validating webhook

    return {
        "status": "processed",
        "event_type": "checkout.session.completed",
        "user_id": user_id,
        "customer_id": customer_id,
        "subscription_id": subscription_id,
    }


async def _handle_subscription_updated(data: dict) -> dict:
    """Handle subscription update (upgrade/downgrade)."""
    subscription_id = data.get("id")
    status = data.get("status")
    customer_id = data.get("customer")

    logger.info(f"Subscription {subscription_id} updated to {status}")

    return {
        "status": "processed",
        "event_type": "customer.subscription.updated",
        "subscription_id": subscription_id,
        "subscription_status": status,
    }


async def _handle_subscription_deleted(data: dict) -> dict:
    """Handle subscription cancellation."""
    subscription_id = data.get("id")
    customer_id = data.get("customer")

    logger.info(f"Subscription {subscription_id} cancelled")

    return {
        "status": "processed",
        "event_type": "customer.subscription.deleted",
        "subscription_id": subscription_id,
    }


async def _handle_invoice_paid(data: dict) -> dict:
    """Handle successful invoice payment."""
    invoice_id = data.get("id")
    customer_id = data.get("customer")
    amount_paid = data.get("amount_paid")

    logger.info(f"Invoice {invoice_id} paid: ${amount_paid/100:.2f}")

    return {
        "status": "processed",
        "event_type": "invoice.paid",
        "invoice_id": invoice_id,
        "amount_cents": amount_paid,
    }


async def _handle_payment_failed(data: dict) -> dict:
    """Handle failed payment."""
    invoice_id = data.get("id")
    customer_id = data.get("customer")

    logger.warning(f"Payment failed for invoice {invoice_id}")

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
    """Get limits for a subscription tier."""
    if tier in PRICING_TIERS:
        return PRICING_TIERS[tier].limits
    return PRICING_TIERS["free"].limits


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
