"""Social posting agent — reads pending social_posts, posts to Twitter/LinkedIn.

Runs twice daily (10am/4pm UTC) via scheduler.
Rate limits: 3 tweets/day, 2 LinkedIn posts/day.
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.marketing.models.social_post import SocialPost

logger = logging.getLogger(__name__)


async def _count_posted_today(
    session: AsyncSession, platform: str
) -> int:
    """Count posts already sent today for a given platform."""
    today_start = datetime.now(UTC).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await session.execute(
        select(func.count(SocialPost.id)).where(
            SocialPost.platform == platform,
            SocialPost.status == "posted",
            SocialPost.posted_at >= today_start,
        )
    )
    return result.scalar() or 0


async def run_social_posting_pipeline(session: AsyncSession) -> dict:
    """Post pending social content to Twitter/X and LinkedIn.

    Returns summary dict with counts of posted/failed/skipped.
    """
    if not settings.enable_social_posting:
        logger.info("Social posting disabled (enable_social_posting=false)")
        return {"status": "disabled"}

    # Get pending posts, oldest first
    result = await session.execute(
        select(SocialPost)
        .where(SocialPost.status == "pending")
        .order_by(SocialPost.created_at.asc())
        .limit(10)
    )
    pending = result.scalars().all()

    if not pending:
        return {"status": "completed", "posted": 0, "reason": "no_pending_posts"}

    twitter_today = await _count_posted_today(session, "twitter")
    linkedin_today = await _count_posted_today(session, "linkedin")

    posted = 0
    failed = 0
    skipped = 0

    for post in pending:
        # Rate limit check
        if post.platform == "twitter" and twitter_today >= settings.twitter_daily_post_limit:
            skipped += 1
            continue
        if post.platform == "linkedin" and linkedin_today >= settings.linkedin_daily_post_limit:
            skipped += 1
            continue

        try:
            if post.platform == "twitter":
                from app.marketing.services.twitter_service import post_tweet

                result_data = await post_tweet(post.content)
                post.external_post_id = result_data["id"]
                twitter_today += 1

            elif post.platform == "linkedin":
                from app.marketing.services.linkedin_service import post_to_linkedin

                result_data = await post_to_linkedin(post.content)
                post.external_post_id = result_data.get("id")
                linkedin_today += 1

            else:
                logger.warning(f"Unknown platform: {post.platform}")
                skipped += 1
                continue

            post.status = "posted"
            post.posted_at = datetime.now(UTC)
            posted += 1
            logger.info(
                f"Posted to {post.platform}: {post.external_post_id} "
                f"(insight={post.insight_id})"
            )

        except Exception as e:
            post.status = "failed"
            post.error_message = str(e)[:500]
            failed += 1
            logger.error(f"Failed to post to {post.platform}: {e}")

    await session.commit()

    summary = {
        "status": "completed",
        "posted": posted,
        "failed": failed,
        "skipped": skipped,
    }
    logger.info(f"Social posting pipeline: {summary}")
    return summary
