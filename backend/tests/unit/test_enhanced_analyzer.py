"""Unit tests for enhanced_analyzer agent schemas and language negotiation.

Covers:
- EnhancedInsightSchema Pydantic validation (constraints, literals, nested models)
- get_enhanced_system_prompt() language dispatch
"""

import pytest
from pydantic import ValidationError

from app.agents.enhanced_analyzer import (
    ENHANCED_SYSTEM_PROMPT,
    ENHANCED_SYSTEM_PROMPT_ZH_CN,
    Competitor,
    EnhancedInsightSchema,
    MarketSizing,
    ProofSignal,
    ValueLadderTier,
    get_enhanced_system_prompt,
)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def make_valid_schema_data() -> dict:
    """Return a dict that passes EnhancedInsightSchema validation."""
    return {
        "title": "AI Market Research Platform",
        "problem_statement": "A " * 250,  # 500+ chars
        "proposed_solution": "AI Research Hub",
        "market_size_estimate": "Large",
        "relevance_score": 0.85,
        "competitor_analysis": [
            {
                "name": "CB Insights",
                "url": "https://cbinsights.com",
                "description": "Market intelligence platform",
            }
        ],
        "opportunity_score": 8,
        "problem_score": 7,
        "feasibility_score": 6,
        "why_now_score": 8,
        "revenue_potential": "$$$",
        "execution_difficulty": 5,
        "go_to_market_score": 7,
        "founder_fit_score": 8,
        "value_ladder": [
            {
                "tier": "lead_magnet",
                "price": "Free",
                "name": "Free Report",
                "description": "Basic market overview",
                "features": ["Overview"],
            }
        ],
        "market_gap_analysis": "Gap analysis text here...",
        "why_now_analysis": "Why now analysis text here...",
        "proof_signals": [
            {
                "signal_type": "search_trend",
                "description": "Growing search interest",
                "source": "Google Trends",
                "confidence": "High",
            }
        ],
        "execution_plan": [
            {
                "step_number": 1,
                "title": "MVP Build",
                "description": "Build core features",
                "estimated_time": "2 weeks",
                "resources_needed": ["Developer"],
            }
        ],
        "community_signals": [
            {
                "platform": "Reddit",
                "communities": "4 subreddits",
                "members": "2.5M+ members",
                "score": 8,
                "top_community": "r/startups",
            }
        ],
        "trend_keywords": [{"keyword": "market research ai", "volume": "5.2K", "growth": "+180%"}],
        "market_sizing": {
            "tam": "$45B global",
            "sam": "$8.2B SMB",
            "som": "$120M AI tools",
            "growth_rate": "12.4%",
        },
    }


# ---------------------------------------------------------------------------
# EnhancedInsightSchema — valid construction
# ---------------------------------------------------------------------------


class TestEnhancedInsightSchema:
    def test_valid_parse(self):
        """A fully populated dict passes validation without error."""
        data = make_valid_schema_data()
        schema = EnhancedInsightSchema(**data)
        assert schema.title == "AI Market Research Platform"
        assert schema.opportunity_score == 8

    def test_score_out_of_range_above(self):
        """opportunity_score above 10 raises ValidationError."""
        data = make_valid_schema_data()
        data["opportunity_score"] = 11
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_score_below_range(self):
        """problem_score below 1 raises ValidationError."""
        data = make_valid_schema_data()
        data["problem_score"] = 0
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_invalid_revenue_potential(self):
        """A revenue_potential value outside the Literal set raises ValidationError."""
        data = make_valid_schema_data()
        data["revenue_potential"] = "$$$$$"
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_missing_required_field(self):
        """Omitting the required 'title' field raises ValidationError."""
        data = make_valid_schema_data()
        del data["title"]
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_invalid_competitor_url(self):
        """A non-URL string in Competitor.url raises ValidationError."""
        data = make_valid_schema_data()
        data["competitor_analysis"] = [{"name": "Bad", "url": "not-a-url", "description": "test"}]
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_relevance_score_above_one(self):
        """relevance_score > 1.0 raises ValidationError (le=1.0 constraint)."""
        data = make_valid_schema_data()
        data["relevance_score"] = 1.5
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_relevance_score_boundary_values(self):
        """relevance_score at exactly 0.0 and 1.0 are both valid."""
        for boundary in (0.0, 1.0):
            data = make_valid_schema_data()
            data["relevance_score"] = boundary
            schema = EnhancedInsightSchema(**data)
            assert schema.relevance_score == boundary

    def test_invalid_market_size_estimate(self):
        """A market_size_estimate outside the Literal set raises ValidationError."""
        data = make_valid_schema_data()
        data["market_size_estimate"] = "Huge"
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_empty_lists_are_allowed(self):
        """Fields with default_factory=list accept empty lists without error."""
        data = make_valid_schema_data()
        data["competitor_analysis"] = []
        data["value_ladder"] = []
        data["proof_signals"] = []
        data["execution_plan"] = []
        data["community_signals"] = []
        data["trend_keywords"] = []
        schema = EnhancedInsightSchema(**data)
        assert schema.competitor_analysis == []

    def test_execution_step_number_out_of_range(self):
        """ExecutionStep.step_number above 10 (ge=1, le=10) raises ValidationError."""
        data = make_valid_schema_data()
        data["execution_plan"] = [
            {
                "step_number": 11,
                "title": "Too far",
                "description": "...",
                "estimated_time": "1 day",
            }
        ]
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_community_signal_score_out_of_range(self):
        """CommunitySignal.score above 10 raises ValidationError."""
        data = make_valid_schema_data()
        data["community_signals"] = [
            {
                "platform": "Reddit",
                "communities": "3 subreddits",
                "members": "1M+ members",
                "score": 11,
                "top_community": "r/test",
            }
        ]
        with pytest.raises(ValidationError):
            EnhancedInsightSchema(**data)

    def test_all_revenue_potential_literals_accepted(self):
        """All four Literal values for revenue_potential are valid."""
        for value in ("$", "$$", "$$$", "$$$$"):
            data = make_valid_schema_data()
            data["revenue_potential"] = value
            schema = EnhancedInsightSchema(**data)
            assert schema.revenue_potential == value

    def test_all_market_size_literals_accepted(self):
        """All three Literal values for market_size_estimate are valid."""
        for value in ("Small", "Medium", "Large"):
            data = make_valid_schema_data()
            data["market_size_estimate"] = value
            schema = EnhancedInsightSchema(**data)
            assert schema.market_size_estimate == value


# ---------------------------------------------------------------------------
# Nested sub-models
# ---------------------------------------------------------------------------


class TestNestedModels:
    def test_competitor_valid_url(self):
        """Competitor accepts a valid https URL."""
        c = Competitor(name="Acme", url="https://acme.com", description="An example competitor")
        assert str(c.url).startswith("https://")

    def test_competitor_market_position_optional(self):
        """Competitor.market_position is nullable (defaults to None)."""
        c = Competitor(name="Acme", url="https://acme.com", description="desc")
        assert c.market_position is None

    def test_value_ladder_tier_literals(self):
        """ValueLadderTier.tier only accepts its four Literal values."""
        for tier in ("lead_magnet", "frontend", "core", "backend"):
            t = ValueLadderTier(tier=tier, price="Free", name="Test", description="desc")
            assert t.tier == tier

        with pytest.raises(ValidationError):
            ValueLadderTier(tier="premium", price="$99", name="Test", description="desc")

    def test_proof_signal_confidence_literals(self):
        """ProofSignal.confidence only accepts Low, Medium, High."""
        for confidence in ("Low", "Medium", "High"):
            ps = ProofSignal(
                signal_type="search_trend",
                description="Some evidence",
                source="Google Trends",
                confidence=confidence,
            )
            assert ps.confidence == confidence

        with pytest.raises(ValidationError):
            ProofSignal(
                signal_type="search_trend",
                description="Bad",
                source="x",
                confidence="Very High",
            )

    def test_market_sizing_requires_all_fields(self):
        """MarketSizing raises ValidationError if any of the four fields are missing."""
        with pytest.raises(ValidationError):
            MarketSizing(tam="$1B", sam="$100M", som="$10M")  # growth_rate missing


# ---------------------------------------------------------------------------
# Language negotiation — get_enhanced_system_prompt
# ---------------------------------------------------------------------------


class TestLanguageNegotiation:
    def test_english_prompt(self):
        """Language code 'en' returns the English system prompt."""
        prompt = get_enhanced_system_prompt("en")
        assert prompt is ENHANCED_SYSTEM_PROMPT

    def test_chinese_prompt(self):
        """Language code 'zh-CN' returns the Mandarin system prompt."""
        prompt = get_enhanced_system_prompt("zh-CN")
        assert prompt is ENHANCED_SYSTEM_PROMPT_ZH_CN

    def test_unsupported_language_falls_back_to_english(self):
        """Any unknown language code falls back to the English prompt."""
        prompt = get_enhanced_system_prompt("fr-FR")
        assert prompt is ENHANCED_SYSTEM_PROMPT

    def test_default_language_is_english(self):
        """Calling with no argument returns the English prompt."""
        prompt = get_enhanced_system_prompt()
        assert prompt is ENHANCED_SYSTEM_PROMPT

    def test_prompts_are_non_empty(self):
        """Both registered prompts contain non-trivial content."""
        assert len(ENHANCED_SYSTEM_PROMPT) > 500
        assert len(ENHANCED_SYSTEM_PROMPT_ZH_CN) > 200

    def test_chinese_prompt_contains_chinese_text(self):
        """ENHANCED_SYSTEM_PROMPT_ZH_CN contains at least one Chinese character."""
        assert any("\u4e00" <= ch <= "\u9fff" for ch in ENHANCED_SYSTEM_PROMPT_ZH_CN)
