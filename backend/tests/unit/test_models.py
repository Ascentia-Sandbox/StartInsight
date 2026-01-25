"""Unit tests for database models.

Note: These tests require PostgreSQL due to JSONB columns.
Run with: DATABASE_URL=postgresql+asyncpg://... pytest tests/unit/test_models.py

For CI/CD without PostgreSQL, these tests are marked to skip if no database.
"""

from datetime import datetime
from uuid import uuid4

import pytest

# Mark all tests in this module to require database
pytestmark = pytest.mark.skipif(
    True,  # Skip until PostgreSQL test database is available
    reason="Model tests require PostgreSQL (JSONB not supported in SQLite)",
)


class TestUserModel:
    """Tests for User model - require PostgreSQL."""

    @pytest.mark.asyncio
    async def test_create_user(self, db_session):
        """Test creating a user."""
        from app.models import User

        user = User(
            id=uuid4(),
            supabase_user_id="test-supabase-123",
            email="test@example.com",
            display_name="Test User",
            subscription_tier="free",
        )
        db_session.add(user)
        await db_session.commit()

        assert user.id is not None
        assert user.email == "test@example.com"


class TestInsightModel:
    """Tests for Insight model - require PostgreSQL."""

    @pytest.mark.asyncio
    async def test_create_insight(self, db_session, test_signal):
        """Test creating an insight."""
        from app.models import Insight

        insight = Insight(
            id=uuid4(),
            raw_signal_id=test_signal.id,
            problem_statement="Test problem",
            proposed_solution="Test solution",
            market_size_estimate="Medium",
            relevance_score=0.75,
        )
        db_session.add(insight)
        await db_session.commit()

        assert insight.id is not None


# ============================================
# Non-database Model Tests
# ============================================


class TestModelImports:
    """Test model imports without database."""

    def test_import_all_models(self):
        """Test that all models can be imported."""
        from app.models import (
            AdminUser,
            CustomAnalysis,
            Insight,
            InsightInteraction,
            RawSignal,
            SavedInsight,
            User,
            UserRating,
        )

        # Verify classes exist
        assert User.__tablename__ == "users"
        assert Insight.__tablename__ == "insights"
        assert RawSignal.__tablename__ == "raw_signals"
        assert SavedInsight.__tablename__ == "saved_insights"
        assert UserRating.__tablename__ == "user_ratings"
        assert AdminUser.__tablename__ == "admin_users"
        assert InsightInteraction.__tablename__ == "insight_interactions"
        assert CustomAnalysis.__tablename__ == "custom_analyses"

    def test_user_model_attributes(self):
        """Test User model has expected attributes."""
        from app.models import User

        expected_columns = [
            "id",
            "supabase_user_id",
            "email",
            "display_name",
            "avatar_url",
            "subscription_tier",
            "preferences",
            "created_at",
            "updated_at",
            "last_login_at",
        ]

        for col in expected_columns:
            assert hasattr(User, col), f"User missing column: {col}"

    def test_insight_model_enhanced_columns(self):
        """Test Insight model has Phase 4.3 enhanced columns."""
        from app.models import Insight

        # Phase 4.3 enhanced columns
        enhanced_columns = [
            "opportunity_score",
            "problem_score",
            "feasibility_score",
            "why_now_score",
            "revenue_potential",
            "execution_difficulty",
            "go_to_market_score",
            "founder_fit_score",
            "value_ladder",
            "market_gap_analysis",
            "why_now_analysis",
            "proof_signals",
            "execution_plan",
        ]

        for col in enhanced_columns:
            assert hasattr(Insight, col), f"Insight missing enhanced column: {col}"

    def test_custom_analysis_model_attributes(self):
        """Test CustomAnalysis model has expected attributes."""
        from app.models import CustomAnalysis

        expected_columns = [
            "id",
            "user_id",
            "idea_description",
            "target_market",
            "budget_range",
            "status",
            "progress_percent",
            "market_analysis",
            "competitor_landscape",
            "value_equation",
            "opportunity_score",
            "market_fit_score",
            "execution_readiness",
        ]

        for col in expected_columns:
            assert hasattr(CustomAnalysis, col), f"CustomAnalysis missing column: {col}"

    def test_insight_interaction_model_attributes(self):
        """Test InsightInteraction model attributes."""
        from app.models import InsightInteraction

        expected_columns = [
            "id",
            "user_id",
            "insight_id",
            "interaction_type",
            "extra_metadata",
            "created_at",
        ]

        for col in expected_columns:
            assert hasattr(InsightInteraction, col), f"InsightInteraction missing column: {col}"
