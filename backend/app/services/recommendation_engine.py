"""Recommendation Engine Service - AI-powered personalized content recommendations.

Sprint 4.1: Provides personalized insight recommendations based on:
- User interaction history (views, saves, ratings)
- User preferences (industries, interests)
- Content similarity (embedding-based)
- Trending signals (recent popularity)
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, Field
from sqlalchemy import and_, desc, func, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.models.insight import Insight
from app.models.user import User
from app.models.user_rating import UserRating

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class UserPreferences(BaseModel):
    """User preference profile for recommendations"""

    industries: list[str] = Field(default_factory=list, description="Preferred industries")
    categories: list[str] = Field(default_factory=list, description="Preferred idea categories")
    revenue_models: list[str] = Field(default_factory=list, description="Preferred revenue models")
    stage_preference: str | None = Field(None, description="Startup stage preference")
    min_score: float = Field(default=0.0, description="Minimum viability score filter")
    email_digest: str = Field(default="weekly", description="Email digest frequency")


class RecommendationScore(BaseModel):
    """Score breakdown for a single recommendation"""

    insight_id: str
    total_score: float = Field(..., ge=0, le=100)
    preference_score: float = Field(..., ge=0, le=100, description="Based on user preferences")
    interaction_score: float = Field(..., ge=0, le=100, description="Based on similar interactions")
    trending_score: float = Field(..., ge=0, le=100, description="Based on recent popularity")
    freshness_score: float = Field(..., ge=0, le=100, description="Based on content recency")
    diversity_penalty: float = Field(default=0.0, description="Penalty for too similar content")


class RecommendedInsight(BaseModel):
    """A recommended insight with explanation"""

    insight_id: str
    title: str
    category: str | None
    viability_score: float | None
    recommendation_score: float
    recommendation_reason: str
    score_breakdown: RecommendationScore
    is_new: bool = False
    is_trending: bool = False


class RecommendationResponse(BaseModel):
    """Response containing personalized recommendations"""

    user_id: str
    recommendations: list[RecommendedInsight]
    total_candidates: int
    algorithm_version: str = "v1.0"
    generated_at: str


# ============================================================================
# RECOMMENDATION ENGINE
# ============================================================================

class RecommendationEngine:
    """
    AI-powered recommendation engine for personalized content discovery.

    Algorithm Components:
    1. Preference Matching (40%): Match content to user's stated preferences
    2. Interaction Signals (30%): Recommend similar to previously liked content
    3. Trending Boost (20%): Boost recently popular content
    4. Freshness (10%): Slight preference for newer content
    5. Diversity Penalty: Prevent too much similar content

    Learning Signals:
    - Views: Implicit positive signal
    - Saves: Strong positive signal (2x weight)
    - Ratings: Explicit signal (scaled by rating value)
    - Time on page: Quality signal (future enhancement)
    """

    # Weight configuration
    PREFERENCE_WEIGHT = 0.40
    INTERACTION_WEIGHT = 0.30
    TRENDING_WEIGHT = 0.20
    FRESHNESS_WEIGHT = 0.10

    # Time windows
    TRENDING_WINDOW_DAYS = 7
    FRESHNESS_WINDOW_DAYS = 30

    def __init__(self):
        """Initialize the recommendation engine."""
        self.logger = logger

    async def get_user_preferences(
        self,
        user_id: UUID,
        session: AsyncSession,
    ) -> UserPreferences:
        """
        Get user preference profile from database.

        Args:
            user_id: User ID
            session: Database session

        Returns:
            UserPreferences with extracted preferences
        """
        stmt = select(User).where(User.id == user_id)
        result = await session.execute(stmt)
        user = result.scalar_one_or_none()

        if not user:
            self.logger.warning(f"User {user_id} not found, using defaults")
            return UserPreferences()

        # Extract preferences from JSONB field
        prefs = user.preferences or {}

        return UserPreferences(
            industries=prefs.get("industries", []),
            categories=prefs.get("categories", []),
            revenue_models=prefs.get("revenue_models", []),
            stage_preference=prefs.get("stage_preference"),
            min_score=prefs.get("min_score", 0.0),
            email_digest=prefs.get("email_digest", "weekly"),
        )

    async def get_user_interaction_history(
        self,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 50,
    ) -> dict[str, list[UUID]]:
        """
        Get user's recent interaction history.

        Args:
            user_id: User ID
            session: Database session
            limit: Max interactions per type

        Returns:
            Dict with lists of insight IDs by interaction type
        """
        # Get rated insights
        ratings_stmt = (
            select(UserRating.insight_id, UserRating.overall_rating)
            .where(UserRating.user_id == user_id)
            .order_by(UserRating.created_at.desc())
            .limit(limit)
        )
        ratings_result = await session.execute(ratings_stmt)
        rated_insights = ratings_result.all()

        # Separate positively and negatively rated
        positive_ratings = [r.insight_id for r in rated_insights if r.overall_rating >= 3.5]
        negative_ratings = [r.insight_id for r in rated_insights if r.overall_rating < 2.5]

        return {
            "positive": positive_ratings,
            "negative": negative_ratings,
            "all_rated": [r.insight_id for r in rated_insights],
        }

    def _calculate_preference_score(
        self,
        insight: Insight,
        preferences: UserPreferences,
    ) -> float:
        """
        Calculate preference match score.

        Args:
            insight: Insight to score
            preferences: User preferences

        Returns:
            Score from 0-100
        """
        score = 50.0  # Base score

        # Category match (+20)
        if insight.category and preferences.categories:
            if insight.category.lower() in [c.lower() for c in preferences.categories]:
                score += 20

        # Revenue model match (+15)
        if insight.revenue_model and preferences.revenue_models:
            if insight.revenue_model.lower() in [r.lower() for r in preferences.revenue_models]:
                score += 15

        # Minimum score filter
        if insight.viability_score and preferences.min_score > 0:
            if insight.viability_score >= preferences.min_score:
                score += 15
            else:
                score -= 30  # Significant penalty for below threshold

        return min(100, max(0, score))

    def _calculate_interaction_score(
        self,
        insight: Insight,
        history: dict[str, list[UUID]],
    ) -> float:
        """
        Calculate interaction-based similarity score.

        Args:
            insight: Insight to score
            history: User interaction history

        Returns:
            Score from 0-100
        """
        # Skip if already interacted
        if insight.id in history.get("all_rated", []):
            return 0.0  # Don't recommend already rated content

        # Penalty if similar to negatively rated
        if insight.id in history.get("negative", []):
            return 10.0

        # Boost if category/type matches positively rated content
        # (simplified - would use embeddings in production)
        base_score = 50.0

        return base_score

    async def _calculate_trending_score(
        self,
        insight: Insight,
        session: AsyncSession,
    ) -> float:
        """
        Calculate trending/popularity score.

        Args:
            insight: Insight to score
            session: Database session

        Returns:
            Score from 0-100
        """
        # Count recent ratings
        cutoff = datetime.now(UTC) - timedelta(days=self.TRENDING_WINDOW_DAYS)
        ratings_stmt = select(func.count(UserRating.id)).where(
            and_(
                UserRating.insight_id == insight.id,
                UserRating.created_at >= cutoff,
            )
        )
        recent_ratings = await session.scalar(ratings_stmt) or 0

        # Scale: 0 ratings = 30, 5+ ratings = 100
        score = min(100, 30 + (recent_ratings * 14))

        return score

    def _calculate_freshness_score(self, insight: Insight) -> float:
        """
        Calculate content freshness score.

        Args:
            insight: Insight to score

        Returns:
            Score from 0-100
        """
        if not insight.created_at:
            return 50.0

        days_old = (datetime.now(UTC) - insight.created_at.replace(tzinfo=None)).days

        # Scale: 0 days = 100, 30+ days = 30
        if days_old <= 0:
            return 100.0
        elif days_old >= self.FRESHNESS_WINDOW_DAYS:
            return 30.0
        else:
            return 100 - (days_old * (70 / self.FRESHNESS_WINDOW_DAYS))

    def _generate_recommendation_reason(
        self,
        insight: Insight,
        score_breakdown: RecommendationScore,
        preferences: UserPreferences,
        is_trending: bool,
    ) -> str:
        """
        Generate human-readable recommendation reason.

        Args:
            insight: Insight being recommended
            score_breakdown: Score components
            preferences: User preferences
            is_trending: Whether insight is trending

        Returns:
            Explanation string
        """
        reasons = []

        if score_breakdown.preference_score > 60:
            if insight.category and preferences.categories:
                if insight.category.lower() in [c.lower() for c in preferences.categories]:
                    reasons.append(f"matches your interest in {insight.category}")

        if is_trending:
            reasons.append("trending this week")

        if score_breakdown.freshness_score > 80:
            reasons.append("recently added")

        if insight.viability_score and insight.viability_score >= 7.0:
            reasons.append(f"high viability score ({insight.viability_score:.1f}/10)")

        if not reasons:
            reasons.append("recommended based on your activity")

        return "This idea " + " and ".join(reasons)

    async def get_recommendations(
        self,
        user_id: UUID,
        session: AsyncSession,
        limit: int = 10,
        exclude_ids: list[UUID] | None = None,
    ) -> RecommendationResponse:
        """
        Get personalized recommendations for a user.

        Args:
            user_id: User ID
            session: Database session
            limit: Number of recommendations to return
            exclude_ids: Insight IDs to exclude

        Returns:
            RecommendationResponse with ranked insights
        """
        self.logger.info(f"Generating recommendations for user {user_id}")

        # Get user preferences and history
        preferences = await self.get_user_preferences(user_id, session)
        history = await self.get_user_interaction_history(user_id, session)

        # Get candidate insights (exclude already rated)
        already_rated = history.get("all_rated", [])
        exclude = set(already_rated)
        if exclude_ids:
            exclude.update(exclude_ids)

        # Build candidate query
        query = (
            select(Insight)
            .where(
                and_(
                    Insight.status == "completed",
                    Insight.id.notin_(list(exclude)) if exclude else True,
                )
            )
            .order_by(Insight.created_at.desc())
            .limit(100)  # Get more candidates than needed for scoring
        )

        result = await session.execute(query)
        candidates = result.scalars().all()

        self.logger.info(f"Found {len(candidates)} candidate insights")

        # Score each candidate
        scored_insights = []
        for insight in candidates:
            # Calculate component scores
            preference_score = self._calculate_preference_score(insight, preferences)
            interaction_score = self._calculate_interaction_score(insight, history)
            trending_score = await self._calculate_trending_score(insight, session)
            freshness_score = self._calculate_freshness_score(insight)

            # Calculate weighted total
            total_score = (
                preference_score * self.PREFERENCE_WEIGHT
                + interaction_score * self.INTERACTION_WEIGHT
                + trending_score * self.TRENDING_WEIGHT
                + freshness_score * self.FRESHNESS_WEIGHT
            )

            score_breakdown = RecommendationScore(
                insight_id=str(insight.id),
                total_score=total_score,
                preference_score=preference_score,
                interaction_score=interaction_score,
                trending_score=trending_score,
                freshness_score=freshness_score,
            )

            is_trending = trending_score > 60
            is_new = freshness_score > 80

            reason = self._generate_recommendation_reason(
                insight, score_breakdown, preferences, is_trending
            )

            scored_insights.append(
                RecommendedInsight(
                    insight_id=str(insight.id),
                    title=insight.title or "Untitled Insight",
                    category=insight.category,
                    viability_score=insight.viability_score,
                    recommendation_score=total_score,
                    recommendation_reason=reason,
                    score_breakdown=score_breakdown,
                    is_new=is_new,
                    is_trending=is_trending,
                )
            )

        # Sort by total score and take top N
        scored_insights.sort(key=lambda x: x.recommendation_score, reverse=True)
        top_recommendations = scored_insights[:limit]

        self.logger.info(
            f"Generated {len(top_recommendations)} recommendations for user {user_id}"
        )

        return RecommendationResponse(
            user_id=str(user_id),
            recommendations=top_recommendations,
            total_candidates=len(candidates),
            generated_at=datetime.now(UTC).isoformat(),
        )


# ============================================================================
# CONVENIENCE FUNCTIONS
# ============================================================================

async def get_personalized_recommendations(
    user_id: UUID,
    session: AsyncSession,
    limit: int = 10,
) -> RecommendationResponse:
    """
    Get personalized recommendations for a user.

    Args:
        user_id: User ID
        session: Database session
        limit: Number of recommendations

    Returns:
        RecommendationResponse with personalized insights
    """
    engine = RecommendationEngine()
    return await engine.get_recommendations(user_id, session, limit)


async def get_similar_insights(
    insight_id: UUID,
    session: AsyncSession,
    limit: int = 5,
) -> list[RecommendedInsight]:
    """
    Get insights similar to a given insight.

    Based on category, tags, and content similarity.

    Args:
        insight_id: Reference insight ID
        session: Database session
        limit: Number of similar insights

    Returns:
        List of similar RecommendedInsight objects
    """
    # Get reference insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    reference = result.scalar_one_or_none()

    if not reference:
        return []

    # Find similar by category
    similar_query = (
        select(Insight)
        .where(
            and_(
                Insight.id != insight_id,
                Insight.status == "completed",
                or_(
                    Insight.category == reference.category,
                    Insight.revenue_model == reference.revenue_model,
                ),
            )
        )
        .order_by(Insight.viability_score.desc().nullslast())
        .limit(limit)
    )

    similar_result = await session.execute(similar_query)
    similar_insights = similar_result.scalars().all()

    return [
        RecommendedInsight(
            insight_id=str(i.id),
            title=i.title or "Untitled",
            category=i.category,
            viability_score=i.viability_score,
            recommendation_score=70.0,  # Similarity-based
            recommendation_reason=f"Similar to insights you viewed in {reference.category or 'this category'}",
            score_breakdown=RecommendationScore(
                insight_id=str(i.id),
                total_score=70.0,
                preference_score=60.0,
                interaction_score=80.0,
                trending_score=50.0,
                freshness_score=50.0,
            ),
        )
        for i in similar_insights
    ]


async def update_user_preferences(
    user_id: UUID,
    preferences: UserPreferences,
    session: AsyncSession,
) -> bool:
    """
    Update user preferences for recommendations.

    Args:
        user_id: User ID
        preferences: New preference settings
        session: Database session

    Returns:
        True if updated successfully
    """
    stmt = select(User).where(User.id == user_id)
    result = await session.execute(stmt)
    user = result.scalar_one_or_none()

    if not user:
        logger.warning(f"User {user_id} not found for preference update")
        return False

    # Merge with existing preferences
    existing_prefs = user.preferences or {}
    existing_prefs.update(preferences.model_dump(exclude_unset=True))
    user.preferences = existing_prefs

    session.add(user)
    await session.commit()

    logger.info(f"Updated preferences for user {user_id}")
    return True
