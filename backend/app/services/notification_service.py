"""Notification service for Slack/Discord webhook delivery.

Sends notifications to bot subscriptions when new insights match criteria.
Called by the pipeline orchestrator after content is published.
"""

import logging
from datetime import UTC, datetime

import httpx
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.models.insight import Insight
from app.models.integrations import BotSubscription

logger = logging.getLogger(__name__)


async def notify_subscribers(db: AsyncSession, insight: Insight) -> int:
    """Send notifications for a newly published insight.

    Checks all active bot subscriptions and sends webhook to matching ones.
    Returns the number of notifications sent.
    """
    result = await db.execute(
        select(BotSubscription)
        .options(selectinload(BotSubscription.integration))
        .where(BotSubscription.is_active.is_(True))
    )
    subscriptions = result.scalars().all()

    sent = 0
    for sub in subscriptions:
        if not _matches_subscription(insight, sub):
            continue

        integration = sub.integration
        if not integration or not integration.is_active:
            continue

        # Build webhook URL from integration config
        webhook_url = (integration.config or {}).get("webhook_url")
        if not webhook_url:
            continue

        payload = _build_payload(insight, integration.service_type)

        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.post(webhook_url, json=payload)
                resp.raise_for_status()
            sub.last_notified_at = datetime.now(UTC)
            sent += 1
            logger.info(
                "Sent %s notification for insight %s to channel %s",
                integration.service_type,
                insight.id,
                sub.channel_name or sub.channel_id,
            )
        except Exception as e:
            logger.warning(
                "Failed to send %s notification: %s",
                integration.service_type,
                e,
            )

    if sent:
        await db.commit()
    return sent


def _matches_subscription(insight: Insight, sub: BotSubscription) -> bool:
    """Check if an insight matches a subscription's filters."""
    # Score filter
    if sub.min_score is not None:
        if (insight.relevance_score or 0) < float(sub.min_score):
            return False

    # Keyword filter
    if sub.keywords:
        text = " ".join(
            filter(
                None,
                [
                    insight.title,
                    insight.problem_statement,
                    insight.proposed_solution,
                ],
            )
        ).lower()
        if not any(kw.lower() in text for kw in sub.keywords):
            return False

    # Subscription type filter
    if sub.subscription_type == BotSubscription.TYPE_HIGH_SCORE:
        if (insight.relevance_score or 0) < 0.8:
            return False

    return True


def _build_payload(insight: Insight, service_type: str) -> dict:
    """Build webhook payload for Slack or Discord."""
    title = insight.title or "New Insight"
    score_pct = int((insight.relevance_score or 0) * 100)
    market = insight.market_size_estimate or "Unknown"

    if service_type == "discord":
        return {
            "embeds": [
                {
                    "title": f"New Insight: {title}",
                    "description": (insight.problem_statement or "")[:300],
                    "color": 0x6366F1,
                    "fields": [
                        {"name": "Viability", "value": f"{score_pct}%", "inline": True},
                        {"name": "Market Size", "value": market, "inline": True},
                        {"name": "Revenue", "value": insight.revenue_potential or "N/A", "inline": True},
                    ],
                }
            ]
        }

    # Default: Slack format
    return {
        "blocks": [
            {
                "type": "header",
                "text": {"type": "plain_text", "text": f"New Insight: {title}"},
            },
            {
                "type": "section",
                "text": {
                    "type": "mrkdwn",
                    "text": (insight.problem_statement or "")[:300],
                },
                "fields": [
                    {"type": "mrkdwn", "text": f"*Viability:* {score_pct}%"},
                    {"type": "mrkdwn", "text": f"*Market:* {market}"},
                    {"type": "mrkdwn", "text": f"*Revenue:* {insight.revenue_potential or 'N/A'}"},
                ],
            },
        ]
    }
