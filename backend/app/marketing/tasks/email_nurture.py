"""Email nurture drip sequence for newsletter subscribers.

Sends timed emails based on days since confirmation:
  Day 1  → Top 5 insights this week
  Day 3  → How StartInsight works (platform tour)
  Day 7  → Category report preview (fintech-malaysia)
  Day 14 → Founder success stories + referral CTA

Runs daily at 10:00 UTC via scheduler.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.insight import Insight
from app.models.newsletter import NewsletterSubscriber
from app.services.email_service import send_email

logger = logging.getLogger(__name__)

# Maps nurture_stage → (min_days_since_confirmed, template_name, next_stage)
NURTURE_STEPS = [
    (1, "nurture_day1", 1),
    (3, "nurture_day3", 3),
    (7, "nurture_day7", 7),
    (14, "nurture_day14", 14),
]


async def _build_insights_html(session: AsyncSession, limit: int = 5) -> str:
    """Build HTML snippet of top insights for the Day 1 email."""
    result = await session.execute(
        select(Insight)
        .where(Insight.relevance_score >= 0.7)
        .order_by(Insight.created_at.desc())
        .limit(limit)
    )
    insights = result.scalars().all()

    if not insights:
        return "<p>Check out the latest ideas on our platform.</p>"

    items = []
    for i in insights:
        title = i.title or i.proposed_solution or "Untitled"
        score = f"{i.relevance_score:.1f}" if i.relevance_score else "—"
        items.append(
            f'<li style="margin-bottom: 8px;"><strong>{title}</strong> — Score: {score}</li>'
        )
    return f'<ol style="font-size: 14px; line-height: 1.8;">{"".join(items)}</ol>'


async def _get_unsubscribe_url(email: str) -> str:
    """Build unsubscribe URL. Uses itsdangerous token if available."""
    try:
        from itsdangerous import URLSafeTimedSerializer

        serializer = URLSafeTimedSerializer(settings.jwt_secret or "dev-secret")
        token = serializer.dumps(email, salt="unsubscribe")
        return f"{settings.app_url}/api/newsletter/unsubscribe?token={token}"
    except Exception:
        return f"{settings.app_url}/api/newsletter/unsubscribe?email={email}"


async def run_email_nurture(session: AsyncSession) -> dict:
    """Send nurture emails to subscribers based on days since confirmation.

    Returns summary dict with counts.
    """
    now = datetime.now(UTC)

    # Get all confirmed, non-unsubscribed subscribers
    result = await session.execute(
        select(NewsletterSubscriber).where(
            NewsletterSubscriber.confirmed.is_(True),
            NewsletterSubscriber.unsubscribed_at.is_(None),
            NewsletterSubscriber.confirmed_at.is_not(None),
        )
    )
    subscribers = result.scalars().all()

    if not subscribers:
        return {"status": "completed", "sent": 0, "reason": "no_subscribers"}

    sent = 0
    skipped = 0
    errors = 0
    insights_html: str | None = None

    for sub in subscribers:
        days_since = (now - sub.confirmed_at).days

        # Find the next nurture step this subscriber should receive
        next_step = None
        for min_days, template, stage in NURTURE_STEPS:
            if sub.nurture_stage < stage and days_since >= min_days:
                next_step = (min_days, template, stage)
                break

        if next_step is None:
            skipped += 1
            continue

        _, template, stage = next_step

        try:
            # Build template variables
            unsubscribe_url = await _get_unsubscribe_url(sub.email)
            variables: dict = {
                "app_url": settings.frontend_url,
                "unsubscribe_url": unsubscribe_url,
                "referral_code": "",
            }

            # Day 1 needs the insights HTML
            if template == "nurture_day1":
                if insights_html is None:
                    insights_html = await _build_insights_html(session)
                variables["insights_html"] = insights_html

            result = await send_email(
                to=sub.email,
                template=template,
                variables=variables,
            )

            if result.get("status") == "error":
                errors += 1
                logger.warning(f"Nurture {template} skipped for {sub.email}: {result.get('error')}")
                continue

            sub.nurture_stage = stage
            sent += 1
            logger.info(f"Nurture {template} sent to {sub.email}")

        except Exception as e:
            errors += 1
            logger.error(f"Nurture email failed for {sub.email}: {e}")

    await session.commit()

    summary = {"status": "completed", "sent": sent, "skipped": skipped, "errors": errors}
    logger.info(f"Email nurture: {summary}")
    return summary
