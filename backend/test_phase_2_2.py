"""Test Phase 2.2: AI Analyzer Agent (PydanticAI)."""

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, patch
from uuid import uuid4

from pydantic import HttpUrl

from app.agents.analyzer import (
    Competitor,
    InsightSchema,
    analyze_signal,
    analyze_signal_with_retry,
)
from app.models.raw_signal import RawSignal

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def test_competitor_schema():
    """Test Competitor Pydantic schema validation."""
    logger.info("Testing Competitor schema...")

    # Valid competitor
    competitor = Competitor(
        name="Test Competitor",
        url="https://competitor.com",
        description="A test competitor description",
        market_position="Large",
    )

    assert competitor.name == "Test Competitor"
    assert str(competitor.url) == "https://competitor.com/"
    assert competitor.market_position == "Large"

    # Test model_dump for JSON serialization
    data = competitor.model_dump()
    assert isinstance(data, dict)
    assert data["name"] == "Test Competitor"

    logger.info("✓ Competitor schema validation works")


def test_insight_schema():
    """Test InsightSchema Pydantic schema validation."""
    logger.info("Testing InsightSchema...")

    # Valid insight
    insight = InsightSchema(
        problem_statement="Legal professionals spend too much time on document review",
        proposed_solution="AI-powered contract analysis tool",
        market_size_estimate="Large",
        relevance_score=0.85,
        competitor_analysis=[
            Competitor(
                name="LegalZoom",
                url="https://legalzoom.com",
                description="Online legal services platform",
                market_position="Large",
            )
        ],
        title="AI for Legal Document Review",
    )

    assert insight.problem_statement.startswith("Legal")
    assert insight.relevance_score == 0.85
    assert insight.market_size_estimate == "Large"
    assert len(insight.competitor_analysis) == 1
    assert insight.title == "AI for Legal Document Review"

    logger.info("✓ InsightSchema validation works")


def test_insight_schema_validation_errors():
    """Test InsightSchema validation catches errors."""
    logger.info("Testing InsightSchema validation errors...")

    # Test invalid relevance_score (> 1.0)
    try:
        InsightSchema(
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Medium",
            relevance_score=1.5,  # Invalid - must be <= 1.0
            competitor_analysis=[],
            title="Test",
        )
        assert False, "Should have raised ValidationError for relevance_score > 1.0"
    except Exception as e:
        assert "relevance_score" in str(e).lower()
        logger.info("✓ Catches relevance_score > 1.0")

    # Test invalid market_size_estimate
    try:
        InsightSchema(
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Huge",  # Invalid - must be Small/Medium/Large
            relevance_score=0.5,
            competitor_analysis=[],
            title="Test",
        )
        assert False, "Should have raised ValidationError for invalid market_size"
    except Exception as e:
        logger.info("✓ Catches invalid market_size_estimate")

    # Test too many competitors (> 3)
    try:
        InsightSchema(
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Medium",
            relevance_score=0.5,
            competitor_analysis=[
                Competitor(
                    name=f"Comp {i}",
                    url=f"https://comp{i}.com",
                    description=f"Competitor {i}",
                )
                for i in range(5)  # 5 competitors - too many
            ],
            title="Test",
        )
        assert False, "Should have raised ValidationError for >3 competitors"
    except Exception as e:
        assert "competitor_analysis" in str(e).lower() or "at most 3 items" in str(e).lower()
        logger.info("✓ Catches >3 competitors")


async def test_analyze_signal_with_mock():
    """Test analyze_signal with mocked PydanticAI agent."""
    logger.info("Testing analyze_signal with mocked agent...")

    # Create a mock raw signal
    raw_signal = RawSignal(
        id=uuid4(),
        source="reddit",
        url="https://reddit.com/r/startups/test",
        content="# Startup Idea: AI Legal Assistant\n\nLawyers spend too much time on document review. We need an AI tool to automate this.",
        extra_metadata={"upvotes": 100},
        processed=False,
    )

    # Mock the PydanticAI agent response
    mock_insight_data = InsightSchema(
        problem_statement="Legal professionals spend too much time on document review",
        proposed_solution="AI-powered contract analysis tool",
        market_size_estimate="Large",
        relevance_score=0.85,
        competitor_analysis=[
            Competitor(
                name="LegalZoom",
                url="https://legalzoom.com",
                description="Online legal services",
                market_position="Large",
            )
        ],
        title="AI for Legal Document Review",
    )

    # Mock the agent.run method
    mock_result = Mock()
    mock_result.data = mock_insight_data

    # Create a mock agent
    mock_agent = Mock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("app.agents.analyzer.get_agent") as mock_get_agent:
        mock_get_agent.return_value = mock_agent

        # Run analysis
        insight = await analyze_signal(raw_signal)

        # Verify Insight model was created correctly
        assert insight.raw_signal_id == raw_signal.id
        assert insight.problem_statement == mock_insight_data.problem_statement
        assert insight.proposed_solution == mock_insight_data.proposed_solution
        assert insight.market_size_estimate == "Large"
        assert insight.relevance_score == 0.85
        assert len(insight.competitor_analysis) == 1
        assert insight.competitor_analysis[0]["name"] == "LegalZoom"

        # Verify agent.run was called once
        mock_agent.run.assert_called_once()

        logger.info("✓ analyze_signal with mock works")


async def test_analyze_signal_with_retry_mock():
    """Test analyze_signal_with_retry with mock."""
    logger.info("Testing analyze_signal_with_retry...")

    raw_signal = RawSignal(
        id=uuid4(),
        source="test",
        url="https://test.com",
        content="Test content for retry test",
        extra_metadata={},
        processed=False,
    )

    # Mock successful response
    mock_insight_data = InsightSchema(
        problem_statement="Test problem",
        proposed_solution="Test solution",
        market_size_estimate="Medium",
        relevance_score=0.7,
        competitor_analysis=[],
        title="Test Insight",
    )

    mock_result = Mock()
    mock_result.data = mock_insight_data

    # Create a mock agent
    mock_agent = Mock()
    mock_agent.run = AsyncMock(return_value=mock_result)

    with patch("app.agents.analyzer.get_agent") as mock_get_agent:
        mock_get_agent.return_value = mock_agent

        # Run analysis with retry
        insight = await analyze_signal_with_retry(raw_signal)

        assert insight.problem_statement == "Test problem"
        assert insight.relevance_score == 0.7

        logger.info("✓ analyze_signal_with_retry works")


async def test_retry_logic_on_failure():
    """Test that retry logic attempts multiple times on failure."""
    logger.info("Testing retry logic on failure...")

    raw_signal = RawSignal(
        id=uuid4(),
        source="test",
        url="https://test.com",
        content="Test content",
        extra_metadata={},
        processed=False,
    )

    # Make agent.run fail 2 times, then succeed on 3rd attempt
    mock_insight_data = InsightSchema(
        problem_statement="Test problem",
        proposed_solution="Test solution",
        market_size_estimate="Small",
        relevance_score=0.6,
        competitor_analysis=[],
        title="Test",
    )
    mock_result = Mock()
    mock_result.data = mock_insight_data

    # Create a mock agent with side effects
    mock_agent = Mock()
    mock_agent.run = AsyncMock(
        side_effect=[
            Exception("API Error 1"),
            Exception("API Error 2"),
            mock_result,  # Success on 3rd try
        ]
    )

    with patch("app.agents.analyzer.get_agent") as mock_get_agent:
        mock_get_agent.return_value = mock_agent

        # Run analysis with retry
        insight = await analyze_signal_with_retry(raw_signal)

        # Verify it succeeded after retries
        assert insight.problem_statement == "Test problem"

        # Verify it was called 3 times (2 failures + 1 success)
        assert mock_agent.run.call_count == 3

        logger.info("✓ Retry logic works (3 attempts)")


def run_all_tests():
    """Run all Phase 2.2 tests."""
    logger.info("=" * 60)
    logger.info("Phase 2.2 Test Suite: AI Analyzer Agent")
    logger.info("=" * 60 + "\n")

    try:
        # Synchronous tests
        test_competitor_schema()
        test_insight_schema()
        test_insight_schema_validation_errors()

        # Async tests
        asyncio.run(test_analyze_signal_with_mock())
        asyncio.run(test_analyze_signal_with_retry_mock())
        asyncio.run(test_retry_logic_on_failure())

        logger.info("\n" + "=" * 60)
        logger.info("✓ ALL PHASE 2.2 TESTS PASSED")
        logger.info("=" * 60)
        return True

    except Exception as e:
        logger.error("=" * 60)
        logger.error(f"✗ PHASE 2.2 TESTS FAILED: {e}")
        logger.error("=" * 60)
        import traceback

        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = run_all_tests()
    exit(0 if success else 1)
