"""Daily digest email task - sends top insights to opted-in users."""

import hashlib
import logging
from datetime import UTC, date, datetime, timedelta

from sqlalchemy import select

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.insight import Insight
from app.models.user import User
from app.models.user_preferences import EmailPreferences, EmailSend
from app.services.email_service import send_daily_digest

logger = logging.getLogger(__name__)


def _generate_unsubscribe_token(user_id: str) -> str:
    """Generate a signed unsubscribe token for email links."""
    from itsdangerous import URLSafeTimedSerializer

    serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
    return serializer.dumps(str(user_id), salt="email-unsubscribe")


async def send_daily_digests_task(ctx: dict) -> dict:
    """Send daily digest emails to opted-in users.

    This task:
    1. Queries users with daily_digest=True and not unsubscribed
    2. Fetches top 3 insights from the last 24 hours
    3. Sends a digest email to each user with dedup via content_hash
    """
    async with AsyncSessionLocal() as db:
        # Get opted-in users
        result = await db.execute(
            select(EmailPreferences, User)
            .join(User, EmailPreferences.user_id == User.id)
            .where(EmailPreferences.daily_digest.is_(True))
            .where(EmailPreferences.unsubscribed_at.is_(None))
            .where(User.deleted_at.is_(None))
        )
        subscribers = result.all()

        if not subscribers:
            logger.info("No subscribers for daily digest")
            return {"status": "skipped", "reason": "no_subscribers"}

        # Get top 3 insights from last 24h
        cutoff = datetime.now(UTC) - timedelta(hours=24)
        insights_result = await db.execute(
            select(Insight)
            .where(Insight.created_at >= cutoff)
            .order_by(Insight.relevance_score.desc())
            .limit(3)
        )
        insights = insights_result.scalars().all()

        if not insights:
            logger.info("No new insights in last 24h, skipping daily digest")
            return {"status": "skipped", "reason": "no_new_insights"}

        # Format insights for template
        insight_list = [
            {
                "title": (i.title or i.proposed_solution[:80]),
                "problem_statement": i.problem_statement[:150],
                "relevance_score": f"{(i.relevance_score or 0) * 100:.0f}%",
                "market_size": i.market_size_estimate or "Unknown",
            }
            for i in insights
        ]

        # Send to each user with content_hash dedup
        sent = 0
        skipped = 0
        for prefs, user in subscribers:
            content_hash = hashlib.sha256(
                f"{date.today()}{user.id}".encode()
            ).hexdigest()

            # Check if already sent today
            existing = await db.execute(
                select(EmailSend).where(
                    EmailSend.user_id == user.id,
                    EmailSend.content_hash == content_hash,
                )
            )
            if existing.scalar_one_or_none():
                skipped += 1
                continue

            try:
                await send_daily_digest(
                    email=user.email,
                    name=user.display_name or "there",
                    insights=insight_list,
                    dashboard_url=f"{settings.app_url}/insights",
                    unsubscribe_url=(
                        f"{settings.app_url}/api/email/unsubscribe"
                        f"?token={_generate_unsubscribe_token(str(user.id))}"
                    ),
                )

                # Track send
                db.add(
                    EmailSend(
                        user_id=user.id,
                        email_type="daily_digest",
                        content_hash=content_hash,
                    )
                )
                sent += 1
            except Exception:
                logger.exception(f"Failed to send digest to user {user.id}")

        await db.commit()

        logger.info(f"Daily digest: sent={sent}, skipped={skipped}")
        return {"status": "success", "sent": sent, "skipped": skipped}
