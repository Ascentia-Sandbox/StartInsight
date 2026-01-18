"""Test Phase 2.1: Database Schema Extension (Insight model)."""

import asyncio
import logging
from datetime import datetime
from uuid import uuid4

from sqlalchemy import inspect, select

from app.db.session import AsyncSessionLocal
from app.models.insight import Insight
from app.models.raw_signal import RawSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_insight_model_creation():
    """Test that Insight model can be created and saved."""
    logger.info("Testing Insight model creation...")

    async with AsyncSessionLocal() as session:
        # Create a raw signal first
        raw_signal = RawSignal(
            source="test",
            url="https://test.com/signal",
            content="# Test Signal\n\nThis is a test signal for Phase 2.1.",
            extra_metadata={"test": True},
            processed=False,
        )
        session.add(raw_signal)
        await session.commit()
        await session.refresh(raw_signal)

        # Create an insight
        insight = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Test problem statement",
            proposed_solution="Test proposed solution",
            market_size_estimate="Medium",
            relevance_score=0.85,
            competitor_analysis=[
                {
                    "name": "Competitor A",
                    "url": "https://competitor-a.com",
                    "description": "A test competitor",
                    "market_position": "Large",
                }
            ],
        )
        session.add(insight)
        await session.commit()
        await session.refresh(insight)

        assert insight.id is not None
        assert insight.raw_signal_id == raw_signal.id
        assert insight.problem_statement == "Test problem statement"
        assert insight.relevance_score == 0.85
        assert isinstance(insight.created_at, datetime)

        logger.info(f"✓ Insight created: {insight.id}")

        # Cleanup
        await session.delete(insight)
        await session.delete(raw_signal)
        await session.commit()


async def test_foreign_key_relationship():
    """Test foreign key relationship to RawSignal."""
    logger.info("Testing foreign key relationship...")

    async with AsyncSessionLocal() as session:
        # Create raw signal
        raw_signal = RawSignal(
            source="test",
            url="https://test.com/signal",
            content="Test content",
            extra_metadata={},
        )
        session.add(raw_signal)
        await session.commit()
        await session.refresh(raw_signal)

        # Create insight with valid foreign key
        insight = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Small",
            relevance_score=0.5,
        )
        session.add(insight)
        await session.commit()

        # Verify relationship
        result = await session.execute(
            select(Insight).where(Insight.raw_signal_id == raw_signal.id)
        )
        found_insight = result.scalar_one()
        assert found_insight.id == insight.id

        logger.info("✓ Foreign key relationship works")

        # Cleanup
        await session.delete(insight)
        await session.delete(raw_signal)
        await session.commit()


async def test_jsonb_competitor_analysis():
    """Test JSONB competitor_analysis field."""
    logger.info("Testing JSONB competitor_analysis field...")

    async with AsyncSessionLocal() as session:
        # Create raw signal
        raw_signal = RawSignal(
            source="test",
            url="https://test.com/signal",
            content="Test content",
            extra_metadata={},
        )
        session.add(raw_signal)
        await session.commit()
        await session.refresh(raw_signal)

        # Create insight with complex competitor data
        competitors = [
            {
                "name": "Competitor 1",
                "url": "https://comp1.com",
                "description": "First competitor",
                "market_position": "Large",
            },
            {
                "name": "Competitor 2",
                "url": "https://comp2.com",
                "description": "Second competitor",
                "market_position": "Medium",
            },
            {
                "name": "Competitor 3",
                "url": "https://comp3.com",
                "description": "Third competitor",
                "market_position": "Small",
            },
        ]

        insight = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Large",
            relevance_score=0.9,
            competitor_analysis=competitors,
        )
        session.add(insight)
        await session.commit()
        await session.refresh(insight)

        # Verify JSONB data
        assert isinstance(insight.competitor_analysis, list)
        assert len(insight.competitor_analysis) == 3
        assert insight.competitor_analysis[0]["name"] == "Competitor 1"
        assert insight.competitor_analysis[1]["market_position"] == "Medium"

        logger.info("✓ JSONB competitor_analysis field works")

        # Cleanup
        await session.delete(insight)
        await session.delete(raw_signal)
        await session.commit()


async def test_indexes_exist():
    """Test that all required indexes exist."""
    logger.info("Testing database indexes...")

    from app.db.session import engine

    # Get database inspector using run_sync for async engine
    def get_indexes(conn):
        inspector = inspect(conn)
        return inspector.get_indexes("insights")

    async with engine.connect() as conn:
        indexes = await conn.run_sync(get_indexes)
        index_names = {idx["name"] for idx in indexes}

        # Expected indexes
        expected_indexes = {
            "ix_insights_created_at",
            "ix_insights_raw_signal_id",
            "ix_insights_relevance_score",
        }

        # Verify all indexes exist
        for expected in expected_indexes:
            assert expected in index_names, f"Missing index: {expected}"
            logger.info(f"✓ Index exists: {expected}")

        logger.info(f"✓ All {len(expected_indexes)} indexes exist")


async def test_bidirectional_relationship():
    """Test bidirectional relationship between Insight and RawSignal."""
    logger.info("Testing bidirectional relationship...")

    async with AsyncSessionLocal() as session:
        # Create raw signal
        raw_signal = RawSignal(
            source="test",
            url="https://test.com/signal",
            content="Test content",
            extra_metadata={},
        )
        session.add(raw_signal)
        await session.commit()
        await session.refresh(raw_signal)

        # Create multiple insights for the same signal
        insight1 = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Problem 1",
            proposed_solution="Solution 1",
            market_size_estimate="Small",
            relevance_score=0.6,
        )
        insight2 = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Problem 2",
            proposed_solution="Solution 2",
            market_size_estimate="Medium",
            relevance_score=0.8,
        )
        session.add_all([insight1, insight2])
        await session.commit()

        # Test forward relationship (Insight → RawSignal)
        await session.refresh(insight1, ["raw_signal"])
        assert insight1.raw_signal.id == raw_signal.id
        assert insight1.raw_signal.source == "test"
        logger.info("✓ Forward relationship works (Insight → RawSignal)")

        # Test reverse relationship (RawSignal → Insights)
        await session.refresh(raw_signal, ["insights"])
        assert len(raw_signal.insights) == 2
        insight_ids = {i.id for i in raw_signal.insights}
        assert insight1.id in insight_ids
        assert insight2.id in insight_ids
        logger.info("✓ Reverse relationship works (RawSignal → Insights)")

        # Cleanup
        await session.delete(insight1)
        await session.delete(insight2)
        await session.delete(raw_signal)
        await session.commit()


async def test_cascade_delete():
    """Test CASCADE delete behavior."""
    logger.info("Testing CASCADE delete...")

    async with AsyncSessionLocal() as session:
        # Create raw signal with insight
        raw_signal = RawSignal(
            source="test",
            url="https://test.com/signal",
            content="Test content",
            extra_metadata={},
        )
        session.add(raw_signal)
        await session.commit()
        await session.refresh(raw_signal)

        insight = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Small",
            relevance_score=0.7,
        )
        session.add(insight)
        await session.commit()

        insight_id = insight.id

        # Delete raw signal (should cascade delete insight)
        await session.delete(raw_signal)
        await session.commit()

        # Verify insight was deleted
        result = await session.execute(select(Insight).where(Insight.id == insight_id))
        found_insight = result.scalar_one_or_none()
        assert found_insight is None

        logger.info("✓ CASCADE delete works")


async def run_all_tests():
    """Run all Phase 2.1 tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.1 Test Suite: Database Schema Extension")
    logger.info("=" * 60 + "\n")

    try:
        await test_insight_model_creation()
        await test_foreign_key_relationship()
        await test_jsonb_competitor_analysis()
        await test_indexes_exist()
        await test_bidirectional_relationship()
        await test_cascade_delete()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.1 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.1 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
