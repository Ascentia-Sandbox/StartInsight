"""Unit tests for Pydantic schemas."""

from datetime import datetime
from uuid import uuid4

import pytest
from pydantic import ValidationError

from app.schemas import (
    EnhancedInsightCreate,
    EnhancedScoreBase,
    InsightResponse,
    RatingCreate,
    ResearchRequestCreate,
    SavedInsightCreate,
    ScoreFilter,
    UserCreate,
    UserUpdate,
)
from app.schemas.research import (
    ACPFramework,
    CompetitorProfile,
    ExecutionPhase,
    MarketAnalysis,
    MarketMatrix,
    ResearchAnalysisResponse,
    RiskAssessment,
    ValidationSignal,
    ValueEquation,
)


class TestUserSchemas:
    """Tests for user schemas."""

    def test_user_create_valid(self):
        """Test valid user creation."""
        user = UserCreate(
            email="test@example.com",
            supabase_user_id="test-123",
            display_name="Test User",
        )
        assert user.email == "test@example.com"

    def test_user_create_invalid_email(self):
        """Test user creation with invalid email."""
        with pytest.raises(ValidationError):
            UserCreate(
                email="invalid-email",
                supabase_user_id="test-123",
            )

    def test_user_update_partial(self):
        """Test partial user update."""
        update = UserUpdate(display_name="New Name")
        assert update.display_name == "New Name"
        assert update.avatar_url is None


class TestSavedInsightSchemas:
    """Tests for saved insight schemas."""

    def test_saved_insight_create(self):
        """Test saved insight creation."""
        saved = SavedInsightCreate(
            insight_id=uuid4(),
            notes="Great idea!",
            tags=["ai", "saas"],
        )
        assert len(saved.tags) == 2


class TestRatingSchemas:
    """Tests for rating schemas."""

    def test_rating_create_valid(self):
        """Test valid rating creation."""
        rating = RatingCreate(rating=5, feedback="Excellent!")
        assert rating.rating == 5

    def test_rating_create_invalid_range(self):
        """Test rating outside valid range."""
        with pytest.raises(ValidationError):
            RatingCreate(rating=6)  # Max is 5

        with pytest.raises(ValidationError):
            RatingCreate(rating=0)  # Min is 1


class TestEnhancedScoreSchemas:
    """Tests for enhanced 8-dimension scoring schemas."""

    def test_enhanced_score_base_valid(self):
        """Test valid enhanced scores."""
        scores = EnhancedScoreBase(
            opportunity_score=8,
            problem_score=7,
            feasibility_score=6,
            why_now_score=8,
            revenue_potential="$$$",
            execution_difficulty=5,
            go_to_market_score=7,
            founder_fit_score=8,
        )
        assert scores.opportunity_score == 8
        assert scores.revenue_potential == "$$$"

    def test_enhanced_score_invalid_range(self):
        """Test scores outside 1-10 range."""
        with pytest.raises(ValidationError):
            EnhancedScoreBase(
                opportunity_score=11,  # Max is 10
                problem_score=7,
                feasibility_score=6,
                why_now_score=8,
                revenue_potential="$$",
                execution_difficulty=5,
                go_to_market_score=7,
                founder_fit_score=8,
            )

    def test_enhanced_score_invalid_revenue(self):
        """Test invalid revenue potential."""
        with pytest.raises(ValidationError):
            EnhancedScoreBase(
                opportunity_score=8,
                problem_score=7,
                feasibility_score=6,
                why_now_score=8,
                revenue_potential="$$$$$",  # Max is $$$$
                execution_difficulty=5,
                go_to_market_score=7,
                founder_fit_score=8,
            )

    def test_score_filter(self):
        """Test score filter schema."""
        filter = ScoreFilter(
            min_opportunity=7,
            min_feasibility=5,
            revenue_potential=["$$", "$$$"],
        )
        assert filter.min_opportunity == 7
        assert len(filter.revenue_potential) == 2


class TestResearchSchemas:
    """Tests for research agent schemas."""

    def test_research_request_create_valid(self):
        """Test valid research request."""
        request = ResearchRequestCreate(
            idea_description="An AI platform that helps startups validate their ideas using market signals",
            target_market="Early-stage founders",
            budget_range="10k-50k",
        )
        assert request.budget_range == "10k-50k"

    def test_research_request_too_short(self):
        """Test research request with too short description."""
        with pytest.raises(ValidationError):
            ResearchRequestCreate(
                idea_description="Short",  # Min 50 chars
                target_market="Startups",
            )

    def test_research_request_invalid_budget(self):
        """Test research request with invalid budget."""
        with pytest.raises(ValidationError):
            ResearchRequestCreate(
                idea_description="A" * 100,  # Valid length
                target_market="Startups",
                budget_range="invalid",  # Not in allowed values
            )

    def test_market_analysis_schema(self):
        """Test market analysis schema."""
        analysis = MarketAnalysis(
            tam="$50B",
            sam="$5B",
            som="$50M",
            growth_rate=0.15,
            market_maturity="growing",
            key_trends=["AI adoption", "Remote work", "Automation"],
        )
        assert analysis.growth_rate == 0.15
        assert len(analysis.key_trends) == 3

    def test_competitor_profile_schema(self):
        """Test competitor profile schema."""
        competitor = CompetitorProfile(
            name="Competitor A",
            url="https://competitor-a.com",
            funding="$5M Series A",
            unique_value_prop="Best-in-class analytics",
            weakness="Expensive pricing",
            market_share_estimate=15.5,
            threat_level="medium",
        )
        assert competitor.market_share_estimate == 15.5

    def test_value_equation_schema(self):
        """Test Hormozi value equation schema."""
        value = ValueEquation(
            dream_outcome_score=9,
            perceived_likelihood_score=7,
            time_delay_score=4,
            effort_sacrifice_score=3,
            value_score=5.25,  # (9*7)/(4*3) = 5.25
            analysis="The value proposition is strong...",
        )
        assert value.value_score == 5.25

    def test_market_matrix_schema(self):
        """Test market matrix schema."""
        matrix = MarketMatrix(
            demand_score=8,
            difficulty_score=4,
            quadrant="star",
            positioning_strategy="Focus on premium market segment",
        )
        assert matrix.quadrant == "star"

    def test_acp_framework_schema(self):
        """Test A-C-P framework schema."""
        acp = ACPFramework(
            awareness_score=6,
            consideration_score=7,
            purchase_score=5,
            funnel_bottleneck="Purchase conversion",
            recommended_channels=["Content marketing", "SEO", "Partnerships"],
        )
        assert len(acp.recommended_channels) == 3

    def test_validation_signal_schema(self):
        """Test validation signal schema."""
        signal = ValidationSignal(
            source="Reddit",
            signal_type="discussion",
            description="Active discussion about need for this solution",
            url="https://reddit.com/r/startups/...",
            sentiment="positive",
            strength="strong",
        )
        assert signal.sentiment == "positive"

    def test_execution_phase_schema(self):
        """Test execution phase schema."""
        phase = ExecutionPhase(
            phase_number=1,
            name="MVP",
            duration="4-6 weeks",
            milestones=["Define core features", "Build prototype", "Test with 5 users"],
            budget_estimate="$5K-$10K",
            key_risks=["Technical complexity", "Market validation"],
        )
        assert phase.phase_number == 1

    def test_risk_assessment_schema(self):
        """Test risk assessment schema."""
        risk = RiskAssessment(
            technical_risk=4,
            market_risk=6,
            team_risk=3,
            financial_risk=5,
            overall_risk=0.45,
            mitigation_strategies=["Hire senior engineer", "Validate with pilots", "Secure runway"],
        )
        assert risk.overall_risk == 0.45
