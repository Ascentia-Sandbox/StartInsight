"""
Backfill Enhanced Scoring for Existing Insights

Re-analyzes insights that have NULL revenue_potential (created before
enhanced analyzer was fully wired) using upgrade_insight_scoring().

Preserves proposed_solution (cleaned titles) and existing basic fields.
Updates: revenue_potential, market_gap_analysis, why_now_analysis,
competitor_analysis, community_signals_chart, market_sizing, proof_signals,
execution_plan, value_ladder, trend_keywords, and all 8 dimension scores.

Usage:
    cd backend && uv run python scripts/backfill_enhanced.py

Cost: ~$0.54 total (54 x Gemini Flash at ~$0.01/call)
"""

import asyncio
import logging
import sys
from pathlib import Path

# Setup Python path
sys.path.insert(0, str(Path(__file__).parent.parent))

from sqlalchemy import select
from sqlalchemy.orm import selectinload

from app.agents.enhanced_analyzer import upgrade_insight_scoring
from app.db.session import AsyncSessionLocal
from app.models.insight import Insight

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
logger = logging.getLogger(__name__)

BATCH_SIZE = 5
DELAY_BETWEEN_BATCHES = 2.0  # seconds


async def backfill() -> None:
    """Backfill enhanced scoring for all insights with NULL revenue_potential."""
    async with AsyncSessionLocal() as session:
        # Find insights missing enhanced scoring
        stmt = (
            select(Insight)
            .where(Insight.revenue_potential.is_(None))
            .options(selectinload(Insight.raw_signal))
            .order_by(Insight.created_at)
        )
        result = await session.execute(stmt)
        insights = list(result.scalars().all())

        total = len(insights)
        logger.info(f"Found {total} insights to backfill")

        if total == 0:
            logger.info("Nothing to backfill - all insights already have enhanced scoring")
            return

        success = 0
        failed = 0

        for i in range(0, total, BATCH_SIZE):
            batch = insights[i : i + BATCH_SIZE]
            batch_num = (i // BATCH_SIZE) + 1
            total_batches = (total + BATCH_SIZE - 1) // BATCH_SIZE
            logger.info(f"Processing batch {batch_num}/{total_batches} ({len(batch)} insights)")

            for insight in batch:
                if not insight.raw_signal:
                    logger.warning(f"Skipping insight {insight.id} - no raw_signal loaded")
                    failed += 1
                    continue

                # Save original proposed_solution to preserve it
                original_solution = insight.proposed_solution

                try:
                    await upgrade_insight_scoring(insight.raw_signal, insight)

                    # Restore proposed_solution (preserve cleaned titles)
                    insight.proposed_solution = original_solution

                    await session.commit()
                    success += 1
                    logger.info(
                        f"  [{success + failed}/{total}] Upgraded: {original_solution[:60]}"
                    )
                except Exception as e:
                    await session.rollback()
                    failed += 1
                    logger.error(
                        f"  [{success + failed}/{total}] Failed insight {insight.id}: {e}"
                    )

            # Rate limit between batches
            if i + BATCH_SIZE < total:
                logger.info(f"  Waiting {DELAY_BETWEEN_BATCHES}s before next batch...")
                await asyncio.sleep(DELAY_BETWEEN_BATCHES)

        logger.info(
            f"Backfill complete: {success} upgraded, {failed} failed out of {total}"
        )


if __name__ == "__main__":
    asyncio.run(backfill())
