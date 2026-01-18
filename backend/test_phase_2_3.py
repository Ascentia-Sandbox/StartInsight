"""Test Phase 2.3: Analysis Task Queue."""

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from app.agents.analyzer import InsightSchema
from app.core.config import settings
from app.db.session import AsyncSessionLocal
from app.models.raw_signal import RawSignal
from app.worker import analyze_signals_task

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_analyze_signals_task_empty():
    """Test analyze_signals_task with no unprocessed signals."""
    logger.info("Testing analyze_signals_task with no unprocessed signals...")

    # Mock context
    ctx = {}

    # Run the task
    result = await analyze_signals_task(ctx)

    assert result["status"] == "success"
    assert result["analyzed"] == 0
    assert result["total"] == 0

    logger.info("✓ Task handles empty queue correctly")


async def test_analyze_signals_task_with_signals():
    """Test analyze_signals_task with unprocessed signals."""
    logger.info("Testing analyze_signals_task with signals...")

    # Create unprocessed raw signals
    async with AsyncSessionLocal() as session:
        signal1 = RawSignal(
            source="test",
            url="https://test.com/1",
            content="Test content 1",
            extra_metadata={},
            processed=False,
        )
        signal2 = RawSignal(
            source="test",
            url="https://test.com/2",
            content="Test content 2",
            extra_metadata={},
            processed=False,
        )
        session.add_all([signal1, signal2])
        await session.commit()
        signal_ids = [signal1.id, signal2.id]

    # Mock the analyzer
    mock_insight_data = InsightSchema(
        problem_statement="Test problem",
        proposed_solution="Test solution",
        market_size_estimate="Medium",
        relevance_score=0.75,
        competitor_analysis=[],
        title="Test Insight",
    )

    mock_result = Mock()
    mock_result.data = mock_insight_data

    mock_agent = Mock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("app.agents.analyzer.get_agent") as mock_get_agent:
        mock_get_agent.return_value = mock_agent

        # Run the task
        ctx = {}
        result = await analyze_signals_task(ctx)

        # Verify results
        assert result["status"] == "success"
        assert result["analyzed"] >= 1  # At least 1 signal analyzed
        assert result["failed"] == 0
        assert result["total"] >= 1

    # Verify signals were marked as processed
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        from app.models.insight import Insight

        # Check if signals were processed
        for signal_id in signal_ids:
            result = await session.execute(
                select(RawSignal).where(RawSignal.id == signal_id)
            )
            signal = result.scalar_one_or_none()
            if signal:
                assert signal.processed == True  # noqa: E712

                # Check if insight was created
                result = await session.execute(
                    select(Insight).where(Insight.raw_signal_id == signal_id)
                )
                insight = result.scalar_one_or_none()
                assert insight is not None

        # Cleanup
        for signal_id in signal_ids:
            result = await session.execute(
                select(Insight).where(Insight.raw_signal_id == signal_id)
            )
            insight = result.scalar_one_or_none()
            if insight:
                await session.delete(insight)

            result = await session.execute(
                select(RawSignal).where(RawSignal.id == signal_id)
            )
            signal = result.scalar_one_or_none()
            if signal:
                await session.delete(signal)

        await session.commit()

    logger.info("✓ Task processes signals correctly")


async def test_batch_size_respected():
    """Test that batch size is respected."""
    logger.info("Testing batch size limit...")

    # Get configured batch size
    batch_size = settings.analysis_batch_size

    # Create more signals than batch size
    async with AsyncSessionLocal() as session:
        signals = []
        for i in range(batch_size + 5):  # Create more than batch size
            signal = RawSignal(
                source="test",
                url=f"https://test.com/{i}",
                content=f"Test content {i}",
                extra_metadata={},
                processed=False,
            )
            signals.append(signal)
        session.add_all(signals)
        await session.commit()
        signal_ids = [s.id for s in signals]

    # Mock the analyzer
    mock_insight_data = InsightSchema(
        problem_statement="Test problem",
        proposed_solution="Test solution",
        market_size_estimate="Small",
        relevance_score=0.5,
        competitor_analysis=[],
        title="Test",
    )

    mock_result = Mock()
    mock_result.data = mock_insight_data

    mock_agent = Mock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("app.agents.analyzer.get_agent") as mock_get_agent:
        mock_get_agent.return_value = mock_agent

        # Run the task
        ctx = {}
        result = await analyze_signals_task(ctx)

        # Verify batch size was respected
        assert result["total"] <= batch_size

    # Cleanup
    async with AsyncSessionLocal() as session:
        from sqlalchemy import select

        from app.models.insight import Insight

        for signal_id in signal_ids:
            result = await session.execute(
                select(Insight).where(Insight.raw_signal_id == signal_id)
            )
            insight = result.scalar_one_or_none()
            if insight:
                await session.delete(insight)

            result = await session.execute(
                select(RawSignal).where(RawSignal.id == signal_id)
            )
            signal = result.scalar_one_or_none()
            if signal:
                await session.delete(signal)

        await session.commit()

    logger.info(f"✓ Batch size respected (max {batch_size} signals)")


async def test_scheduler_configuration():
    """Test that scheduler is configured correctly."""
    logger.info("Testing scheduler configuration...")

    from app.tasks.scheduler import scheduler

    # Verify scheduler exists
    assert scheduler is not None

    # Verify it's an AsyncIOScheduler
    from apscheduler.schedulers.asyncio import AsyncIOScheduler

    assert isinstance(scheduler, AsyncIOScheduler)

    logger.info("✓ Scheduler configured correctly")


def test_worker_settings():
    """Test that WorkerSettings includes analyze_signals_task."""
    logger.info("Testing WorkerSettings configuration...")

    from app.worker import WorkerSettings, analyze_signals_task

    # Verify task is registered
    assert analyze_signals_task in WorkerSettings.functions

    # Verify all expected tasks are registered
    expected_tasks = [
        "scrape_reddit_task",
        "scrape_product_hunt_task",
        "scrape_trends_task",
        "scrape_all_sources_task",
        "analyze_signals_task",
    ]

    task_names = [f.__name__ for f in WorkerSettings.functions]

    for expected in expected_tasks:
        assert expected in task_names, f"Missing task: {expected}"

    logger.info(f"✓ All {len(expected_tasks)} tasks registered in WorkerSettings")


async def run_all_tests():
    """Run all Phase 2.3 tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.3 Test Suite: Analysis Task Queue")
    logger.info("=" * 60 + "\n")

    try:
        # Sync tests
        test_worker_settings()

        # Async tests
        await test_analyze_signals_task_empty()
        await test_analyze_signals_task_with_signals()
        await test_batch_size_respected()
        await test_scheduler_configuration()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.3 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.3 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
