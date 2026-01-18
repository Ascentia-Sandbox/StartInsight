"""Test Phase 2.6: Monitoring & Logging."""

import asyncio
import logging
from datetime import datetime
from unittest.mock import AsyncMock, Mock, patch

from app.agents.analyzer import InsightSchema, analyze_signal
from app.models.raw_signal import RawSignal
from app.monitoring.metrics import (
    LLMCallMetrics,
    MetricsTracker,
    get_metrics_tracker,
)

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_llm_call_metrics_cost_calculation():
    """Test LLM call metrics cost calculation."""
    logger.info("Testing LLM call metrics cost calculation...")

    # Test Claude 3.5 Sonnet cost calculation
    metrics = LLMCallMetrics(
        timestamp=datetime.utcnow(),
        model="claude-3-5-sonnet-20241022",
        prompt_length=1000,
        response_length=500,
        input_tokens=250,  # 1000 chars ≈ 250 tokens
        output_tokens=125,  # 500 chars ≈ 125 tokens
        latency_ms=1500.0,
        success=True,
    )

    # Claude pricing: $0.003/1K input, $0.015/1K output
    # Cost = (250 * 0.003/1000) + (125 * 0.015/1000)
    # Cost = 0.00075 + 0.001875 = 0.002625
    expected_cost = (250 * 0.003 / 1000) + (125 * 0.015 / 1000)

    assert abs(metrics.cost_usd - expected_cost) < 0.0001
    assert metrics.cost_usd > 0.0

    logger.info(f"✓ Cost calculation correct: ${metrics.cost_usd:.6f}")


def test_metrics_tracker_singleton():
    """Test that MetricsTracker is a singleton."""
    logger.info("Testing MetricsTracker singleton pattern...")

    tracker1 = get_metrics_tracker()
    tracker2 = get_metrics_tracker()

    assert tracker1 is tracker2
    assert isinstance(tracker1, MetricsTracker)

    logger.info("✓ MetricsTracker is a singleton")


def test_track_llm_call():
    """Test tracking LLM calls."""
    logger.info("Testing LLM call tracking...")

    tracker = get_metrics_tracker()
    tracker.reset()  # Reset for clean test

    # Track a successful call
    tracker.track_llm_call(
        model="claude-3-5-sonnet",
        prompt="Test prompt",
        response="Test response",
        input_tokens=10,
        output_tokens=5,
        latency_ms=1000.0,
        success=True,
    )

    assert len(tracker.metrics.llm_calls) == 1
    assert tracker.metrics.llm_calls[0].success == True
    assert tracker.metrics.llm_calls[0].input_tokens == 10
    assert tracker.metrics.llm_calls[0].output_tokens == 5

    logger.info("✓ LLM call tracking works")


def test_track_insight_generated():
    """Test tracking successful insight generation."""
    logger.info("Testing insight generation tracking...")

    tracker = get_metrics_tracker()
    tracker.reset()

    # Track some insights
    tracker.track_insight_generated(0.8)
    tracker.track_insight_generated(0.9)
    tracker.track_insight_generated(0.7)

    assert tracker.metrics.total_insights_generated == 3
    assert len(tracker.metrics.relevance_scores) == 3
    assert abs(tracker.metrics.average_relevance_score - (0.8 + 0.9 + 0.7) / 3) < 0.0001

    logger.info(
        f"✓ Insight tracking works (avg score: {tracker.metrics.average_relevance_score:.2f})"
    )


def test_track_insight_failed():
    """Test tracking failed insight generation."""
    logger.info("Testing failed insight tracking...")

    tracker = get_metrics_tracker()
    tracker.reset()

    # Track failed insights
    tracker.track_insight_failed(ValueError("Test error 1"))
    tracker.track_insight_failed(RuntimeError("Test error 2"))
    tracker.track_insight_failed(ValueError("Test error 3"))

    assert tracker.metrics.total_insights_failed == 3
    assert tracker.metrics.errors_by_type["ValueError"] == 2
    assert tracker.metrics.errors_by_type["RuntimeError"] == 1

    logger.info("✓ Failed insight tracking works")


def test_success_rate_calculation():
    """Test success rate calculation."""
    logger.info("Testing success rate calculation...")

    tracker = get_metrics_tracker()
    tracker.reset()

    # Generate some insights (7 success, 3 failures)
    for _ in range(7):
        tracker.track_insight_generated(0.8)

    for _ in range(3):
        tracker.track_insight_failed(ValueError("Test"))

    # Success rate = 7 / (7 + 3) * 100 = 70%
    assert abs(tracker.metrics.success_rate - 70.0) < 0.01

    logger.info(f"✓ Success rate: {tracker.metrics.success_rate:.1f}%")


def test_metrics_summary():
    """Test metrics summary generation."""
    logger.info("Testing metrics summary...")

    tracker = get_metrics_tracker()
    tracker.reset()

    # Add some data
    tracker.track_insight_generated(0.85)
    tracker.track_llm_call(
        model="claude-3-5-sonnet",
        prompt="Test",
        response="Response",
        input_tokens=100,
        output_tokens=50,
        latency_ms=1200.0,
        success=True,
    )

    summary = tracker.get_summary()

    assert "insights" in summary
    assert "llm" in summary
    assert "errors" in summary
    assert summary["insights"]["total_generated"] == 1
    assert summary["llm"]["total_calls"] == 1

    logger.info(f"✓ Summary generated: {summary}")


async def test_analyzer_metrics_integration():
    """Test that analyzer integrates with metrics tracker."""
    logger.info("Testing analyzer metrics integration...")

    tracker = get_metrics_tracker()
    tracker.reset()

    # Create test signal
    signal = RawSignal(
        id="550e8400-e29b-41d4-a716-446655440000",
        source="test",
        url="https://test.com",
        content="Test signal content for metrics tracking",
        extra_metadata={},
        processed=False,
    )

    # Mock the agent
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

        # Analyze signal
        insight = await analyze_signal(signal)

        # Verify metrics were tracked
        assert tracker.metrics.total_insights_generated == 1
        assert len(tracker.metrics.llm_calls) == 1
        assert tracker.metrics.llm_calls[0].success == True
        assert tracker.metrics.relevance_scores[0] == 0.75

    logger.info("✓ Analyzer metrics integration works")


def run_all_tests():
    """Run all Phase 2.6 tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.6 Test Suite: Monitoring & Logging")
    logger.info("=" * 60 + "\n")

    try:
        # Sync tests
        test_llm_call_metrics_cost_calculation()
        test_metrics_tracker_singleton()
        test_track_llm_call()
        test_track_insight_generated()
        test_track_insight_failed()
        test_success_rate_calculation()
        test_metrics_summary()

        # Async tests
        asyncio.run(test_analyzer_metrics_integration())

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.6 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.6 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
