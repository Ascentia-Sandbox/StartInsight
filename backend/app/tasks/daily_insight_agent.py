"""Daily Insight Agent - Curates the best insight every day at 8:00 UTC.

This agent:
1. Checks if it's enabled via AgentConfiguration
2. Queries insights from the last 24 hours
3. Selects the highest-scored insight as "Idea of the Day"
4. Logs execution to AgentExecutionLog for admin monitoring
"""

import logging
from datetime import UTC, datetime, timedelta

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration
from app.models.agent_execution_log import AgentExecutionLog
from app.models.insight import Insight

logger = logging.getLogger(__name__)

AGENT_NAME = "daily_insight_agent"


async def _is_agent_enabled(db: AsyncSession) -> bool:
    """Check if the daily insight agent is enabled in AgentConfiguration."""
    result = await db.execute(
        select(AgentConfiguration).where(AgentConfiguration.agent_name == AGENT_NAME)
    )
    config = result.scalar_one_or_none()

    if not config:
        # Auto-create config on first run
        config = AgentConfiguration(
            agent_name=AGENT_NAME,
            is_enabled=True,
            model_name="gemini-1.5-flash",
            rate_limit_per_hour=10,
        )
        db.add(config)
        await db.commit()
        return True

    return config.is_enabled


async def fetch_daily_insight_task(ctx: dict) -> dict:
    """Fetch and curate the top insight for today.

    Called by the scheduler at 08:00 UTC daily. Respects the
    AgentConfiguration is_enabled flag so admins can pause/stop it.
    """
    started_at = datetime.now(UTC)

    async with AsyncSessionLocal() as db:
        # Check if agent is enabled
        if not await _is_agent_enabled(db):
            logger.info(f"Agent {AGENT_NAME} is disabled, skipping execution")
            # Log skipped execution
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="insights",
                status="skipped",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                items_processed=0,
                extra_metadata={"reason": "agent_disabled"},
            ))
            await db.commit()
            return {"status": "skipped", "reason": "agent_disabled"}

        try:
            # Fetch top insights from last 24 hours
            cutoff = datetime.now(UTC) - timedelta(hours=24)
            result = await db.execute(
                select(Insight)
                .where(Insight.created_at >= cutoff)
                .order_by(Insight.relevance_score.desc())
                .limit(5)
            )
            insights = result.scalars().all()

            if not insights:
                # No new insights - log and return
                completed_at = datetime.now(UTC)
                db.add(AgentExecutionLog(
                    agent_type=AGENT_NAME,
                    source="insights",
                    status="completed",
                    started_at=started_at,
                    completed_at=completed_at,
                    duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                    items_processed=0,
                    extra_metadata={"reason": "no_new_insights"},
                ))
                await db.commit()
                logger.info("Daily insight agent: no new insights in last 24h")
                return {"status": "completed", "items": 0, "reason": "no_new_insights"}

            # Select the top insight as "Idea of the Day"
            top_insight = insights[0]

            # Log successful execution
            completed_at = datetime.now(UTC)
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="insights",
                status="completed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                items_processed=len(insights),
                extra_metadata={
                    "top_insight_id": str(top_insight.id),
                    "top_score": top_insight.relevance_score,
                    "candidates_evaluated": len(insights),
                },
            ))
            await db.commit()

            logger.info(
                f"Daily insight agent: selected insight {top_insight.id} "
                f"(score={top_insight.relevance_score}) from {len(insights)} candidates"
            )

            return {
                "status": "completed",
                "items": len(insights),
                "top_insight_id": str(top_insight.id),
                "top_score": top_insight.relevance_score,
            }

        except Exception as e:
            # Log failed execution
            completed_at = datetime.now(UTC)
            db.add(AgentExecutionLog(
                agent_type=AGENT_NAME,
                source="insights",
                status="failed",
                started_at=started_at,
                completed_at=completed_at,
                duration_ms=int((completed_at - started_at).total_seconds() * 1000),
                items_processed=0,
                error_message=str(e),
            ))
            await db.commit()

            logger.exception(f"Daily insight agent failed: {e}")
            return {"status": "failed", "error": str(e)}
