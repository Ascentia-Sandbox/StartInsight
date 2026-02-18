"""Content Automation Pipeline Orchestrator (Phase 17).

After signal analysis, automatically triggers:
1. Market insight article generation for top insights
2. Success story generation for top 3 insights
3. Quality review 30 min later
4. Auto-publish if quality_score >= 7

Each run is tracked in the pipeline_runs table.
"""

import logging
from datetime import UTC, datetime

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.agents.market_insight_publisher import generate_market_insight_article
from app.agents.quality_reviewer import review_draft_articles
from app.db.session import AsyncSessionLocal
from app.models.agent_control import AgentConfiguration
from app.models.agent_execution_log import AgentExecutionLog
from app.models.insight import Insight
from app.models.pipeline_run import PipelineRun
from app.services.notification_service import notify_subscribers

logger = logging.getLogger(__name__)


async def _is_pipeline_enabled(session: AsyncSession) -> bool:
    """Check if the pipeline orchestrator agent is enabled."""
    result = await session.execute(
        select(AgentConfiguration).where(
            AgentConfiguration.agent_name == "pipeline_orchestrator"
        )
    )
    config = result.scalar_one_or_none()
    if config is None:
        return True  # Default to enabled
    return config.is_enabled


async def run_content_pipeline() -> dict:
    """
    Main content pipeline orchestrator.

    Finds new high-scoring insights and triggers content generation + quality review.
    """
    async with AsyncSessionLocal() as session:
        if not await _is_pipeline_enabled(session):
            logger.info("Pipeline orchestrator is disabled, skipping")
            return {"status": "skipped", "reason": "disabled"}

        # Create pipeline run record
        pipeline_run = PipelineRun(
            status="running",
            total_stages=4,
            details={"stages": []},
        )
        session.add(pipeline_run)
        await session.commit()
        await session.refresh(pipeline_run)

        started_at = datetime.now(UTC)
        stages_completed = 0
        stage_details = []

        try:
            # Stage 1: Find high-scoring unprocessed insights
            result = await session.execute(
                select(Insight)
                .where(Insight.relevance_score >= 0.8)
                .where(Insight.admin_status.in_(["approved", None]))
                .order_by(Insight.created_at.desc())
                .limit(5)
            )
            top_insights = result.scalars().all()

            if not top_insights:
                pipeline_run.status = "completed"
                pipeline_run.stages_completed = 0
                pipeline_run.completed_at = datetime.now(UTC)
                pipeline_run.details = {"reason": "no_qualifying_insights"}
                await session.commit()
                logger.info("Pipeline: no qualifying insights (score >= 0.8)")
                return {"status": "completed", "insights_found": 0}

            stage_details.append({
                "stage": "find_insights",
                "count": len(top_insights),
                "insight_ids": [str(i.id) for i in top_insights],
            })
            stages_completed += 1

            # Stage 2: Generate market insight article
            article = None
            try:
                article = await generate_market_insight_article(session)
                if article:
                    stage_details.append({
                        "stage": "generate_article",
                        "article_id": str(article.id),
                        "title": article.title,
                    })
                else:
                    stage_details.append({
                        "stage": "generate_article",
                        "skipped": True,
                        "reason": "agent_disabled",
                    })
                stages_completed += 1
            except Exception as e:
                logger.error(f"Pipeline stage 2 (article generation) failed: {e}")
                stage_details.append({
                    "stage": "generate_article",
                    "error": str(e),
                })

            # Stage 3: Quality review of draft articles
            try:
                review_results = await review_draft_articles(session)
                published_count = sum(1 for r in review_results if r.get("published"))
                stage_details.append({
                    "stage": "quality_review",
                    "reviewed": len(review_results),
                    "published": published_count,
                })
                stages_completed += 1
            except Exception as e:
                logger.error(f"Pipeline stage 3 (quality review) failed: {e}")
                stage_details.append({
                    "stage": "quality_review",
                    "error": str(e),
                })

            # Stage 4: Notify Slack/Discord subscribers
            try:
                notified = 0
                for insight in top_insights:
                    notified += await notify_subscribers(session, insight)
                stage_details.append({
                    "stage": "notify_subscribers",
                    "notifications_sent": notified,
                })
                stages_completed += 1
            except Exception as e:
                logger.error(f"Pipeline stage 4 (notifications) failed: {e}")
                stage_details.append({
                    "stage": "notify_subscribers",
                    "error": str(e),
                })

            # Update pipeline run
            pipeline_run.status = "completed" if stages_completed == 4 else "partial"
            pipeline_run.stages_completed = stages_completed
            pipeline_run.completed_at = datetime.now(UTC)
            pipeline_run.details = {"stages": stage_details}

            # Log execution
            duration_ms = int((datetime.now(UTC) - started_at).total_seconds() * 1000)
            session.add(AgentExecutionLog(
                agent_type="pipeline_orchestrator",
                source="pipeline",
                status="completed",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                duration_ms=duration_ms,
                items_processed=len(top_insights),
                extra_metadata={
                    "pipeline_run_id": str(pipeline_run.id),
                    "stages_completed": stages_completed,
                },
            ))

            await session.commit()

            logger.info(
                f"Pipeline completed: {stages_completed}/3 stages, "
                f"{len(top_insights)} insights processed"
            )

            return {
                "status": pipeline_run.status,
                "pipeline_run_id": str(pipeline_run.id),
                "stages_completed": stages_completed,
                "insights_found": len(top_insights),
                "details": stage_details,
            }

        except Exception as e:
            # Mark pipeline as failed
            pipeline_run.status = "failed"
            pipeline_run.error_message = str(e)[:500]
            pipeline_run.completed_at = datetime.now(UTC)
            pipeline_run.stages_completed = stages_completed
            pipeline_run.details = {"stages": stage_details, "error": str(e)}

            session.add(AgentExecutionLog(
                agent_type="pipeline_orchestrator",
                source="pipeline",
                status="failed",
                started_at=started_at,
                completed_at=datetime.now(UTC),
                error_message=str(e),
            ))

            await session.commit()
            logger.exception(f"Pipeline failed: {e}")
            return {"status": "error", "error": str(e)}
