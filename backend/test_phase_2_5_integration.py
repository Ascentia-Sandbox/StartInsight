"""Test Phase 2.5: Integration Tests & Validation."""

import asyncio
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_phase_2_1_passed():
    """Verify Phase 2.1 (Database) tests passed."""
    logger.info("Verifying Phase 2.1 tests...")

    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "test_phase_2_1.py"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Phase 2.1 tests failed"
    assert "ALL PHASE 2.1 TESTS PASSED" in result.stdout or "ALL PHASE 2.1 TESTS PASSED" in result.stderr

    logger.info("✓ Phase 2.1 tests passed")


async def test_phase_2_2_passed():
    """Verify Phase 2.2 (AI Agent) tests passed."""
    logger.info("Verifying Phase 2.2 tests...")

    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "test_phase_2_2.py"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Phase 2.2 tests failed"
    assert "ALL PHASE 2.2 TESTS PASSED" in result.stdout or "ALL PHASE 2.2 TESTS PASSED" in result.stderr

    logger.info("✓ Phase 2.2 tests passed")


async def test_phase_2_3_passed():
    """Verify Phase 2.3 (Task Queue) tests passed."""
    logger.info("Verifying Phase 2.3 tests...")

    import subprocess

    result = subprocess.run(
        ["uv", "run", "python", "test_phase_2_3.py"],
        capture_output=True,
        text=True,
    )

    assert result.returncode == 0, "Phase 2.3 tests failed"
    assert "ALL PHASE 2.3 TESTS PASSED" in result.stdout or "ALL PHASE 2.3 TESTS PASSED" in result.stderr

    logger.info("✓ Phase 2.3 tests passed")


async def test_full_pipeline_components():
    """Test that all pipeline components exist."""
    logger.info("Testing pipeline components...")

    # Test Insight model exists
    from app.models.insight import Insight

    assert Insight is not None

    # Test analyzer exists
    from app.agents.analyzer import analyze_signal, analyze_signal_with_retry

    assert analyze_signal is not None
    assert analyze_signal_with_retry is not None

    # Test worker task exists
    from app.worker import analyze_signals_task

    assert analyze_signals_task is not None

    # Test API endpoints exist
    from app.api.routes import insights

    assert insights.router is not None

    logger.info("✓ All pipeline components exist")


async def test_database_schema_complete():
    """Test that database schema includes all required tables."""
    logger.info("Testing database schema...")

    from sqlalchemy import inspect

    from app.db.session import engine

    def get_tables(conn):
        inspector = inspect(conn)
        return inspector.get_table_names()

    async with engine.connect() as conn:
        tables = await conn.run_sync(get_tables)

        # Verify required tables exist
        required_tables = ["raw_signals", "insights", "alembic_version"]

        for table in required_tables:
            assert table in tables, f"Missing table: {table}"

    logger.info(f"✓ All {len(required_tables)} required tables exist")


async def test_models_relationship():
    """Test Insight ↔ RawSignal relationship."""
    logger.info("Testing model relationships...")

    from app.db.session import AsyncSessionLocal
    from app.models.insight import Insight
    from app.models.raw_signal import RawSignal

    async with AsyncSessionLocal() as session:
        # Create test raw signal
        signal = RawSignal(
            source="integration_test",
            url="https://test.com",
            content="Integration test content",
            extra_metadata={},
        )
        session.add(signal)
        await session.commit()
        await session.refresh(signal)

        # Create test insight
        insight = Insight(
            raw_signal_id=signal.id,
            problem_statement="Integration test problem",
            proposed_solution="Integration test solution",
            market_size_estimate="Small",
            relevance_score=0.5,
            competitor_analysis=[],
        )
        session.add(insight)
        await session.commit()

        # Test forward relationship
        await session.refresh(insight, ["raw_signal"])
        assert insight.raw_signal.id == signal.id

        # Test reverse relationship
        await session.refresh(signal, ["insights"])
        assert len(signal.insights) == 1
        assert signal.insights[0].id == insight.id

        # Cleanup
        await session.delete(insight)
        await session.delete(signal)
        await session.commit()

    logger.info("✓ Model relationships work correctly")


async def run_all_tests():
    """Run all Phase 2.5 integration tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.5 Test Suite: Integration Tests & Validation")
    logger.info("=" * 60 + "\n")

    try:
        # Verify all phase tests passed
        await test_phase_2_1_passed()
        await test_phase_2_2_passed()
        await test_phase_2_3_passed()

        # Component tests
        await test_full_pipeline_components()
        await test_database_schema_complete()
        await test_models_relationship()

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.5 INTEGRATION TESTS PASSED")
        logger.info("=" * 60)
        logger.info("\n🎉 PHASE 2 COMPLETE - Analysis Loop Fully Operational!")
        logger.info(
            "\nPipeline: Raw Signals → AI Analysis → Structured Insights → API Endpoints"
        )
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.5 INTEGRATION TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    exit(0 if success else 1)
