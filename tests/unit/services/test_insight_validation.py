"""Tests for insight validation service.

Tests quality gates for LLM-generated insight data:
1. Problem statement minimum length
2. Score ranges
3. Cross-field consistency
4. Quality score calculation
"""

import pytest

from app.schemas.insight_validation import (
    QualityValidationError,
    ValidatedInsightSchema,
    calculate_quality_score,
    validate_insight_data,
)


class TestValidatedInsightSchema:
    """Test ValidatedInsightSchema validation gates."""

    @pytest.fixture
    def valid_insight_data(self):
        """Create valid insight data for testing."""
        # Generate 300+ word problem statement
        problem_statement = " ".join(["word"] * 350)

        return {
            "title": "Test Startup Idea",
            "problem_statement": problem_statement,
            "proposed_solution": "A comprehensive solution with multiple components and features.",
            "market_size_estimate": "Medium",
            "relevance_score": 0.75,
            "competitor_analysis": [],
            "opportunity_score": 7,
            "problem_score": 6,
            "feasibility_score": 8,
            "why_now_score": 7,
            "revenue_potential": "$$",
            "execution_difficulty": 4,
            "go_to_market_score": 7,
            "founder_fit_score": 8,
            "value_ladder": [],
            "market_gap_analysis": "Detailed market gap analysis with multiple paragraphs explaining the competitive landscape.",
            "why_now_analysis": "Timing analysis explaining why this is the right moment to enter the market.",
            "proof_signals": [],
            "execution_plan": [],
            "community_signals": [],
            "trend_keywords": [],
        }

    def test_valid_insight_passes(self, valid_insight_data):
        """Test that valid insight data passes validation."""
        insight = ValidatedInsightSchema(**valid_insight_data)
        assert insight.title == "Test Startup Idea"
        assert insight.opportunity_score == 7

    def test_problem_statement_too_short_fails(self, valid_insight_data):
        """Test that short problem statement fails validation."""
        valid_insight_data["problem_statement"] = "This is too short."

        with pytest.raises(ValueError, match="Problem statement too short"):
            ValidatedInsightSchema(**valid_insight_data)

    def test_problem_statement_exact_minimum(self, valid_insight_data):
        """Test that exactly 300 words passes."""
        valid_insight_data["problem_statement"] = " ".join(["word"] * 300)
        insight = ValidatedInsightSchema(**valid_insight_data)
        assert len(insight.problem_statement.split()) == 300

    def test_relevance_score_above_range_fails(self, valid_insight_data):
        """Test that relevance score > 1.0 fails."""
        valid_insight_data["relevance_score"] = 1.5

        with pytest.raises(ValueError, match="less than or equal to 1"):
            ValidatedInsightSchema(**valid_insight_data)

    def test_relevance_score_below_range_fails(self, valid_insight_data):
        """Test that relevance score < 0.0 fails."""
        valid_insight_data["relevance_score"] = -0.1

        with pytest.raises(ValueError, match="greater than or equal to 0"):
            ValidatedInsightSchema(**valid_insight_data)

    def test_dimension_score_above_range_fails(self, valid_insight_data):
        """Test that dimension score > 10 fails."""
        valid_insight_data["opportunity_score"] = 11

        with pytest.raises(ValueError):
            ValidatedInsightSchema(**valid_insight_data)

    def test_dimension_score_below_range_fails(self, valid_insight_data):
        """Test that dimension score < 1 fails."""
        valid_insight_data["problem_score"] = 0

        with pytest.raises(ValueError):
            ValidatedInsightSchema(**valid_insight_data)

    def test_high_opportunity_low_problem_fails(self, valid_insight_data):
        """Test cross-field consistency: high opportunity requires significant problem."""
        valid_insight_data["opportunity_score"] = 9
        valid_insight_data["problem_score"] = 3

        with pytest.raises(ValueError, match="Inconsistent scores"):
            ValidatedInsightSchema(**valid_insight_data)

    def test_high_feasibility_high_difficulty_fails(self, valid_insight_data):
        """Test cross-field consistency: high feasibility conflicts with high difficulty."""
        valid_insight_data["feasibility_score"] = 9
        valid_insight_data["execution_difficulty"] = 9

        with pytest.raises(ValueError, match="Inconsistent scores"):
            ValidatedInsightSchema(**valid_insight_data)

    def test_low_opportunity_max_revenue_fails(self, valid_insight_data):
        """Test cross-field consistency: low opportunity cannot have max revenue."""
        valid_insight_data["opportunity_score"] = 2
        valid_insight_data["revenue_potential"] = "$$$$"

        with pytest.raises(ValueError, match="Inconsistent"):
            ValidatedInsightSchema(**valid_insight_data)


class TestValidateInsightData:
    """Test validate_insight_data function."""

    def test_returns_valid_result_for_good_data(self):
        """Test that valid data returns is_valid=True."""
        result = validate_insight_data(
            title="Test Idea",
            problem_statement=" ".join(["word"] * 400),
            proposed_solution="A good solution approach.",
            relevance_score=0.8,
            opportunity_score=7,
            problem_score=7,
            feasibility_score=8,
            why_now_score=7,
            execution_difficulty=4,
            go_to_market_score=7,
            founder_fit_score=8,
            revenue_potential="$$",
            market_size_estimate="Medium",
            market_gap_analysis="Analysis text here.",
            why_now_analysis="Timing analysis here.",
            community_signals=[{"platform": "Reddit"}, {"platform": "Facebook"}],
            trend_keywords=[{"keyword": "test"}, {"keyword": "example"}],
        )

        assert result.is_valid is True
        assert len(result.errors) == 0

    def test_returns_errors_for_short_problem(self):
        """Test that short problem statement returns errors."""
        result = validate_insight_data(
            title="Test",
            problem_statement="Too short.",
            proposed_solution="Solution.",
            relevance_score=0.8,
            opportunity_score=7,
            problem_score=7,
            feasibility_score=8,
            why_now_score=7,
            execution_difficulty=4,
            go_to_market_score=7,
            founder_fit_score=8,
            revenue_potential="$$",
            market_size_estimate="Medium",
        )

        assert result.is_valid is False
        assert any("too short" in e.lower() for e in result.errors)

    def test_returns_warnings_for_low_community_signals(self):
        """Test that low community signal count returns warnings."""
        result = validate_insight_data(
            title="Test",
            problem_statement=" ".join(["word"] * 400),
            proposed_solution="Solution.",
            relevance_score=0.8,
            opportunity_score=7,
            problem_score=7,
            feasibility_score=8,
            why_now_score=7,
            execution_difficulty=4,
            go_to_market_score=7,
            founder_fit_score=8,
            revenue_potential="$$",
            market_size_estimate="Medium",
            community_signals=[{"platform": "Reddit"}],  # Only 1
        )

        assert any("community signal" in w.lower() for w in result.warnings)


class TestCalculateQualityScore:
    """Test quality score calculation."""

    def test_high_quality_returns_high_score(self):
        """Test that high quality data returns high score."""
        score = calculate_quality_score(
            word_count=500,
            dimension_scores=[8, 8, 8, 8, 4, 8, 8],
            community_count=4,
            trend_count=4,
            competitor_count=3,
            has_value_ladder=True,
            has_proof_signals=True,
            has_execution_plan=True,
            error_count=0,
            warning_count=0,
        )

        assert score >= 80

    def test_low_quality_returns_low_score(self):
        """Test that low quality data returns low score."""
        score = calculate_quality_score(
            word_count=100,
            dimension_scores=[3, 3, 3, 3, 8, 3, 3],
            community_count=0,
            trend_count=0,
            competitor_count=0,
            has_value_ladder=False,
            has_proof_signals=False,
            has_execution_plan=False,
            error_count=5,
            warning_count=3,
        )

        assert score < 30

    def test_errors_reduce_score(self):
        """Test that errors reduce the quality score."""
        base_score = calculate_quality_score(
            word_count=400,
            dimension_scores=[7, 7, 7, 7, 5, 7, 7],
            community_count=3,
            trend_count=3,
            competitor_count=2,
            has_value_ladder=True,
            has_proof_signals=True,
            has_execution_plan=True,
            error_count=0,
            warning_count=0,
        )

        score_with_errors = calculate_quality_score(
            word_count=400,
            dimension_scores=[7, 7, 7, 7, 5, 7, 7],
            community_count=3,
            trend_count=3,
            competitor_count=2,
            has_value_ladder=True,
            has_proof_signals=True,
            has_execution_plan=True,
            error_count=3,
            warning_count=0,
        )

        assert score_with_errors < base_score
        assert base_score - score_with_errors >= 25  # 3 errors * 10 points penalty

    def test_score_capped_at_100(self):
        """Test that score cannot exceed 100."""
        score = calculate_quality_score(
            word_count=1000,
            dimension_scores=[10, 10, 10, 10, 1, 10, 10],
            community_count=10,
            trend_count=10,
            competitor_count=10,
            has_value_ladder=True,
            has_proof_signals=True,
            has_execution_plan=True,
            error_count=0,
            warning_count=0,
        )

        assert score <= 100

    def test_score_minimum_zero(self):
        """Test that score cannot go below 0."""
        score = calculate_quality_score(
            word_count=10,
            dimension_scores=[1, 1, 1, 1, 10, 1, 1],
            community_count=0,
            trend_count=0,
            competitor_count=0,
            has_value_ladder=False,
            has_proof_signals=False,
            has_execution_plan=False,
            error_count=20,
            warning_count=20,
        )

        assert score >= 0
