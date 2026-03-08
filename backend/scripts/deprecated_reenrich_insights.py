"""Re-enrich all real insights with fresh AI analysis.

Re-runs the enhanced_analyzer agent on all non-seed insights to regenerate
titles, competitor analysis, proof signals, community signals, trend keywords,
value ladders, execution plans, and all 8 dimension scores.

Preserves the original raw_signal_id link (keeps real source URL).
Updates existing insight rows in-place (does not create new rows).

Usage:
    cd backend && uv run python -m scripts.reenrich_insights
"""

import asyncio
import logging
import time

from dotenv import load_dotenv

load_dotenv()  # Load .env before any app imports

from sqlalchemy import select, update
from sqlalchemy.orm import selectinload

from app.agents.enhanced_analyzer import analyze_signal_enhanced
from app.db.session import AsyncSessionLocal
from app.models.insight import Insight
from app.models.raw_signal import RawSignal
from app.utils.slug import generate_slug

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 5
BATCH_DELAY = 10.0  # seconds between batches to respect LLM rate limits


async def reenrich():
    """Main re-enrichment routine."""
    async with AsyncSessionLocal() as session:
        # Fetch all insights with raw_signals (exclude seed_data)
        query = (
            select(Insight)
            .join(RawSignal, Insight.raw_signal_id == RawSignal.id)
            .where(RawSignal.source != "seed_data")
            .options(selectinload(Insight.raw_signal))
            .order_by(Insight.created_at.asc())
        )
        result = await session.execute(query)
        insights = list(result.scalars().all())

        total = len(insights)
        logger.info(f"Found {total} real insights to re-enrich")

        if total == 0:
            logger.info("Nothing to do")
            return

        success = 0
        failed = 0

        for i, insight in enumerate(insights, 1):
            raw_signal = insight.raw_signal
            if not raw_signal or not raw_signal.content:
                logger.warning(f"[{i}/{total}] Skipping {insight.id}: no raw_signal content")
                failed += 1
                continue

            logger.info(
                f"[{i}/{total}] Re-enriching insight {insight.id} "
                f"(source={raw_signal.source}, url={raw_signal.url[:80]}...)"
            )

            try:
                start = time.time()
                new_insight = await analyze_signal_enhanced(raw_signal)
                elapsed = time.time() - start

                # Update existing row with fresh analysis
                new_slug = generate_slug(new_insight.title)

                # Check for slug collision
                existing = await session.execute(
                    select(Insight.id)
                    .where(Insight.slug == new_slug)
                    .where(Insight.id != insight.id)
                )
                if existing.scalar_one_or_none():
                    # Append short id suffix to avoid collision
                    new_slug = f"{new_slug}-{str(insight.id)[:6]}"

                await session.execute(
                    update(Insight)
                    .where(Insight.id == insight.id)
                    .values(
                        title=new_insight.title,
                        slug=new_slug,
                        problem_statement=new_insight.problem_statement,
                        proposed_solution=new_insight.proposed_solution,
                        market_size_estimate=new_insight.market_size_estimate,
                        relevance_score=new_insight.relevance_score,
                        competitor_analysis=new_insight.competitor_analysis,
                        opportunity_score=new_insight.opportunity_score,
                        problem_score=new_insight.problem_score,
                        feasibility_score=new_insight.feasibility_score,
                        why_now_score=new_insight.why_now_score,
                        revenue_potential=new_insight.revenue_potential,
                        execution_difficulty=new_insight.execution_difficulty,
                        go_to_market_score=new_insight.go_to_market_score,
                        founder_fit_score=new_insight.founder_fit_score,
                        value_ladder=new_insight.value_ladder,
                        market_gap_analysis=new_insight.market_gap_analysis,
                        why_now_analysis=new_insight.why_now_analysis,
                        proof_signals=new_insight.proof_signals,
                        execution_plan=new_insight.execution_plan,
                        community_signals_chart=new_insight.community_signals_chart,
                        trend_keywords=new_insight.trend_keywords,
                        market_sizing=new_insight.market_sizing,
                    )
                )

                success += 1
                logger.info(
                    f"[{i}/{total}] OK: '{new_insight.title}' "
                    f"(slug={new_slug}, {elapsed:.1f}s)"
                )

            except Exception as e:
                failed += 1
                logger.error(f"[{i}/{total}] FAILED for {insight.id}: {e}")

            # Commit and rate-limit after each batch
            if i % BATCH_SIZE == 0:
                await session.commit()
                logger.info(
                    f"Committed batch {i // BATCH_SIZE} "
                    f"({success} ok, {failed} failed). "
                    f"Sleeping {BATCH_DELAY}s for rate limits..."
                )
                await asyncio.sleep(BATCH_DELAY)

        # Final commit
        await session.commit()
        logger.info(
            f"Re-enrichment complete: {success} updated, {failed} failed "
            f"out of {total} total"
        )


if __name__ == "__main__":
    asyncio.run(reenrich())
