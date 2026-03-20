"""Feature tests for the signal → AI analysis → Insight creation pipeline.

Rather than exercising the full analyze_signal_enhanced() function (which
requires live AI API credentials and many complex collaborators), these tests
validate the components that the pipeline is built from:

1. EnhancedInsightSchema can be unpacked to construct an Insight model.
2. Missing required schema fields raise ValidationError before any DB write.
3. SOURCE_CREDIBILITY_WEIGHTS contains the expected multipliers used by
   _apply_credibility_weight() during insight creation.
"""

import pytest
from pydantic import ValidationError

from app.agents.enhanced_analyzer import (
    EnhancedInsightSchema,
    _apply_credibility_weight,
)
from app.core.constants import SOURCE_CREDIBILITY_WEIGHTS
from app.models.insight import Insight

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_valid_schema_data() -> dict:
    """Minimal valid dict for EnhancedInsightSchema."""
    return {
        "title": "Test Insight",
        "problem_statement": "B " * 260,  # > 500 chars
        "proposed_solution": "Test Solution",
        "market_size_estimate": "Medium",
        "relevance_score": 0.75,
        "competitor_analysis": [],
        "opportunity_score": 7,
        "problem_score": 7,
        "feasibility_score": 7,
        "why_now_score": 7,
        "revenue_potential": "$$",
        "execution_difficulty": 4,
        "go_to_market_score": 7,
        "founder_fit_score": 7,
        "value_ladder": [],
        "market_gap_analysis": "Some gap analysis.",
        "why_now_analysis": "Some timing analysis.",
        "proof_signals": [],
        "execution_plan": [],
        "community_signals": [],
        "trend_keywords": [],
        "market_sizing": {
            "tam": "$10B global",
            "sam": "$1B segment",
            "som": "$50M target",
            "growth_rate": "8%",
        },
    }


# ---------------------------------------------------------------------------
# Test 1: Valid schema can be used to instantiate an Insight model
# ---------------------------------------------------------------------------


class TestEnhancedSchemaToInsight:
    def test_valid_schema_creates_insight_fields(self):
        """Fields from EnhancedInsightSchema map correctly onto an Insight instance."""
        from uuid import uuid4

        schema = EnhancedInsightSchema(**make_valid_schema_data())
        signal_id = uuid4()

        insight = Insight(
            raw_signal_id=signal_id,
            title=schema.title,
            problem_statement=schema.problem_statement,
            proposed_solution=schema.proposed_solution,
            market_size_estimate=schema.market_size_estimate,
            relevance_score=schema.relevance_score,
            competitor_analysis=[c.model_dump() for c in schema.competitor_analysis],
            opportunity_score=schema.opportunity_score,
            problem_score=schema.problem_score,
            feasibility_score=schema.feasibility_score,
            why_now_score=schema.why_now_score,
            revenue_potential=schema.revenue_potential,
            execution_difficulty=schema.execution_difficulty,
            go_to_market_score=schema.go_to_market_score,
            founder_fit_score=schema.founder_fit_score,
            value_ladder=[t.model_dump() for t in schema.value_ladder],
            market_gap_analysis=schema.market_gap_analysis,
            why_now_analysis=schema.why_now_analysis,
            proof_signals=[p.model_dump() for p in schema.proof_signals],
            execution_plan=[s.model_dump() for s in schema.execution_plan],
            community_signals_chart=[c.model_dump() for c in schema.community_signals],
            trend_keywords=[t.model_dump() for t in schema.trend_keywords],
            market_sizing=schema.market_sizing.model_dump(),
        )

        assert insight.title == "Test Insight"
        assert insight.opportunity_score == 7
        assert insight.relevance_score == 0.75
        assert insight.raw_signal_id == signal_id

    # -----------------------------------------------------------------------
    # Test 2: Missing required schema field raises before any Insight is built
    # -----------------------------------------------------------------------

    def test_schema_missing_field_raises(self):
        """Missing required field raises ValidationError, preventing Insight creation."""
        data = make_valid_schema_data()
        del data["market_sizing"]  # Required — no default
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    # -----------------------------------------------------------------------
    # Test 3: Empty-string optional text fields still pass validation
    # -----------------------------------------------------------------------

    def test_empty_analysis_text_is_valid(self):
        """market_gap_analysis and why_now_analysis accept empty strings (no min_length)."""
        data = make_valid_schema_data()
        data["market_gap_analysis"] = ""
        data["why_now_analysis"] = ""
        schema = EnhancedInsightSchema(**data)
        assert schema.market_gap_analysis == ""
        assert schema.why_now_analysis == ""


# ---------------------------------------------------------------------------
# Test 4–6: SOURCE_CREDIBILITY_WEIGHTS values used by _apply_credibility_weight
# ---------------------------------------------------------------------------


class TestCredibilityWeights:
    def test_hacker_news_gets_1_2x_weight(self):
        """hacker_news credibility weight is 1.2 (curated technical audience)."""
        assert SOURCE_CREDIBILITY_WEIGHTS["hacker_news"] == 1.2

    def test_twitter_gets_0_8x_weight(self):
        """twitter credibility weight is 0.8 (noisy, short-form)."""
        assert SOURCE_CREDIBILITY_WEIGHTS["twitter"] == 0.8

    def test_reddit_baseline_weight(self):
        """reddit credibility weight is 1.0 (the baseline)."""
        assert SOURCE_CREDIBILITY_WEIGHTS["reddit"] == 1.0

    def test_product_hunt_weight(self):
        """product_hunt credibility weight is 1.1 (curated launches)."""
        assert SOURCE_CREDIBILITY_WEIGHTS["product_hunt"] == 1.1

    def test_google_trends_weight(self):
        """google_trends credibility weight is 0.9 (volume signal, not quality)."""
        assert SOURCE_CREDIBILITY_WEIGHTS["google_trends"] == 0.9

    # -----------------------------------------------------------------------
    # Test: _apply_credibility_weight mutates relevance_score in-place
    # -----------------------------------------------------------------------

    def test_credibility_weight_applied_in_place(self):
        """_apply_credibility_weight multiplies relevance_score by the source weight."""
        insight = Insight(
            raw_signal_id=None,
            title="T",
            problem_statement="P",
            proposed_solution="S",
            relevance_score=1.0,
            opportunity_score=5,
            problem_score=5,
            feasibility_score=5,
            why_now_score=5,
            revenue_potential="$$",
            execution_difficulty=5,
            go_to_market_score=5,
            founder_fit_score=5,
            market_gap_analysis="",
            why_now_analysis="",
        )
        _apply_credibility_weight(insight, "twitter")
        assert insight.relevance_score == pytest.approx(0.8)

    def test_credibility_weight_capped_at_one(self):
        """relevance_score is capped at 1.0 even when weight > 1."""
        insight = Insight(
            raw_signal_id=None,
            title="T",
            problem_statement="P",
            proposed_solution="S",
            relevance_score=1.0,
            opportunity_score=5,
            problem_score=5,
            feasibility_score=5,
            why_now_score=5,
            revenue_potential="$$",
            execution_difficulty=5,
            go_to_market_score=5,
            founder_fit_score=5,
            market_gap_analysis="",
            why_now_analysis="",
        )
        _apply_credibility_weight(insight, "hacker_news")
        # 1.0 * 1.2 = 1.2 → capped to 1.0
        assert insight.relevance_score == pytest.approx(1.0)

    def test_unknown_source_uses_default_weight_of_one(self):
        """An unrecognised source name falls back to weight 1.0."""
        insight = Insight(
            raw_signal_id=None,
            title="T",
            problem_statement="P",
            proposed_solution="S",
            relevance_score=0.6,
            opportunity_score=5,
            problem_score=5,
            feasibility_score=5,
            why_now_score=5,
            revenue_potential="$$",
            execution_difficulty=5,
            go_to_market_score=5,
            founder_fit_score=5,
            market_gap_analysis="",
            why_now_analysis="",
        )
        _apply_credibility_weight(insight, "unknown_source")
        assert insight.relevance_score == pytest.approx(0.6)
