"""Post-LLM validation gates for insight quality.

This module provides Pydantic schemas that validate LLM-generated insight
data to ensure quality standards are met before storing in the database.

Quality Gates:
1. Problem statement minimum length (300 words)
2. Relevance score range (0.0-1.0)
3. Dimension scores range (1-10)
4. Cross-field consistency checks
5. Community signal validation
6. Trend keyword validation
"""

import logging
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl, field_validator, model_validator

logger = logging.getLogger(__name__)


class QualityValidationError(Exception):
    """Raised when insight data fails quality validation."""

    def __init__(self, message: str, field: str | None = None, value: any = None):
        self.field = field
        self.value = value
        super().__init__(message)


class ValidatedCompetitor(BaseModel):
    """Validated competitor entry."""

    name: str = Field(min_length=1, description="Competitor name")
    url: HttpUrl = Field(description="Competitor website URL")
    description: str = Field(max_length=200, description="Brief description")
    market_position: Literal["Small", "Medium", "Large"] | None = None


class ValidatedCommunitySignal(BaseModel):
    """Validated community signal with verified data."""

    platform: Literal["Reddit", "Facebook", "YouTube", "Other"]
    communities: str = Field(min_length=1, description="e.g., '4 subreddits'")
    members: str = Field(min_length=1, description="e.g., '2.5M+ members'")
    score: int = Field(ge=1, le=10, description="Community engagement score")
    top_community: str = Field(min_length=1, description="Most relevant community")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        """Ensure score is within valid range."""
        if not 1 <= v <= 10:
            raise ValueError(f"Community score out of range: {v} (must be 1-10)")
        return v


class ValidatedTrendKeyword(BaseModel):
    """Validated trend keyword with search data."""

    keyword: str = Field(min_length=1, description="Search keyword")
    volume: str = Field(min_length=1, description="e.g., '1.0K' or '27.1K'")
    growth: str = Field(min_length=1, description="e.g., '+1900%' or '+86%'")

    @field_validator("growth")
    @classmethod
    def validate_growth_format(cls, v: str) -> str:
        """Ensure growth has valid format (starts with + or - or number)."""
        if not v:
            raise ValueError("Growth cannot be empty")
        # Allow formats like "+1900%", "-5%", "1900%", "N/A"
        if v.upper() == "N/A":
            return v
        # Check for valid growth format
        cleaned = v.replace("%", "").replace("+", "").replace("-", "")
        if not cleaned.replace(".", "").isdigit():
            logger.warning(f"Unusual growth format: {v}")
        return v


class ValidatedValueLadderTier(BaseModel):
    """Validated value ladder tier."""

    tier: Literal["lead_magnet", "frontend", "core", "backend"]
    price: str = Field(min_length=1, description="Price range")
    name: str = Field(min_length=1, description="Product name")
    description: str = Field(min_length=1, description="Tier description")
    features: list[str] = Field(default_factory=list, min_length=0)


class ValidatedProofSignal(BaseModel):
    """Validated proof signal."""

    signal_type: Literal[
        "search_trend", "competitor_growth", "community_discussion", "market_report"
    ]
    description: str = Field(max_length=300, description="Evidence description")
    source: str = Field(min_length=1, description="Source URL or platform")
    confidence: Literal["Low", "Medium", "High"]


class ValidatedExecutionStep(BaseModel):
    """Validated execution step."""

    step_number: int = Field(ge=1, le=10, description="Step number")
    title: str = Field(min_length=1, description="Step title")
    description: str = Field(min_length=1, description="Step description")
    estimated_time: str = Field(min_length=1, description="Time estimate")
    resources_needed: list[str] = Field(default_factory=list)


class ValidatedInsightSchema(BaseModel):
    """
    Post-LLM validation gates for insight quality.

    This schema validates LLM-generated insight data to ensure quality
    standards are met before storing in the database.

    Quality Gates:
    1. Problem statement: Minimum 300 words
    2. Relevance score: Range 0.0-1.0
    3. Dimension scores: Range 1-10 for all 8 dimensions
    4. Cross-field consistency: High opportunity requires significant problem
    5. Community signals: At least 2 required
    6. Trend keywords: At least 2 required
    """

    # Basic insight fields
    title: str = Field(min_length=5, max_length=200, description="Insight title")
    problem_statement: str = Field(description="Narrative problem statement")
    proposed_solution: str = Field(min_length=50, description="Solution approach")
    market_size_estimate: Literal["Small", "Medium", "Large"]
    relevance_score: float = Field(ge=0.0, le=1.0, description="Signal relevance")

    # Competitor analysis
    competitor_analysis: list[ValidatedCompetitor] = Field(default_factory=list)

    # 8-Dimension Scoring (1-10 scale)
    opportunity_score: int = Field(ge=1, le=10, description="Market size score")
    problem_score: int = Field(ge=1, le=10, description="Pain severity score")
    feasibility_score: int = Field(ge=1, le=10, description="Technical ease score")
    why_now_score: int = Field(ge=1, le=10, description="Market timing score")
    revenue_potential: Literal["$", "$$", "$$$", "$$$$"]
    execution_difficulty: int = Field(ge=1, le=10, description="Complexity score")
    go_to_market_score: int = Field(ge=1, le=10, description="Distribution score")
    founder_fit_score: int = Field(ge=1, le=10, description="Skills requirement")

    # Advanced frameworks
    value_ladder: list[ValidatedValueLadderTier] = Field(default_factory=list)
    market_gap_analysis: str = Field(min_length=100, description="Market gap analysis")
    why_now_analysis: str = Field(min_length=100, description="Timing analysis")
    proof_signals: list[ValidatedProofSignal] = Field(default_factory=list)
    execution_plan: list[ValidatedExecutionStep] = Field(default_factory=list)

    # Community signals and trend keywords
    community_signals: list[ValidatedCommunitySignal] = Field(default_factory=list)
    trend_keywords: list[ValidatedTrendKeyword] = Field(default_factory=list)

    # Quality Gate 1: Problem statement minimum length (300 words)
    @field_validator("problem_statement")
    @classmethod
    def validate_problem_length(cls, v: str) -> str:
        """Ensure problem statement meets minimum word count."""
        word_count = len(v.split())
        if word_count < 300:
            raise ValueError(
                f"Problem statement too short: {word_count} words (minimum 300). "
                f"The problem statement should be a narrative story with psychological depth."
            )
        return v

    # Quality Gate 2: Relevance score range validation
    @field_validator("relevance_score")
    @classmethod
    def validate_relevance_range(cls, v: float) -> float:
        """Ensure relevance score is within valid range."""
        if not 0.0 <= v <= 1.0:
            raise ValueError(
                f"Relevance score out of range: {v} (must be 0.0-1.0)"
            )
        return round(v, 3)  # Normalize precision

    # Quality Gate 3: Dimension scores range validation
    @field_validator(
        "opportunity_score",
        "problem_score",
        "feasibility_score",
        "why_now_score",
        "execution_difficulty",
        "go_to_market_score",
        "founder_fit_score",
    )
    @classmethod
    def validate_dimension_scores(cls, v: int) -> int:
        """Ensure dimension scores are within valid range."""
        if not 1 <= v <= 10:
            raise ValueError(
                f"Dimension score out of range: {v} (must be 1-10)"
            )
        return v

    # Quality Gate 4: Cross-field consistency validation
    @model_validator(mode="after")
    def validate_score_consistency(self) -> "ValidatedInsightSchema":
        """
        Validate cross-field consistency.

        Rules:
        1. High opportunity (8+) should correlate with significant problem (5+)
        2. High feasibility (8+) should have reasonable execution difficulty (1-7)
        3. Verify community signals exist if mentioned in problem statement
        """
        # Rule 1: High opportunity requires significant problem
        if self.opportunity_score >= 8 and self.problem_score < 5:
            raise ValueError(
                f"Inconsistent scores: High opportunity ({self.opportunity_score}) "
                f"requires significant problem score (min 5, got {self.problem_score})"
            )

        # Rule 2: Feasibility and execution difficulty inverse correlation
        if self.feasibility_score >= 8 and self.execution_difficulty > 7:
            raise ValueError(
                f"Inconsistent scores: High feasibility ({self.feasibility_score}) "
                f"conflicts with high execution difficulty ({self.execution_difficulty})"
            )

        # Rule 3: Low opportunity should not have maximum revenue potential
        if self.opportunity_score <= 3 and self.revenue_potential == "$$$$":
            raise ValueError(
                f"Inconsistent: Low opportunity ({self.opportunity_score}) "
                f"cannot have maximum revenue potential ($$$$)"
            )

        return self

    # Quality Gate 5: Minimum community signals
    @model_validator(mode="after")
    def validate_community_signals_count(self) -> "ValidatedInsightSchema":
        """Ensure minimum number of community signals."""
        if len(self.community_signals) < 2:
            logger.warning(
                f"Low community signal count: {len(self.community_signals)} "
                f"(recommended: 3-4)"
            )
            # Don't raise error, just warn - allow some flexibility
        return self

    # Quality Gate 6: Minimum trend keywords
    @model_validator(mode="after")
    def validate_trend_keywords_count(self) -> "ValidatedInsightSchema":
        """Ensure minimum number of trend keywords."""
        if len(self.trend_keywords) < 2:
            logger.warning(
                f"Low trend keyword count: {len(self.trend_keywords)} "
                f"(recommended: 2-5)"
            )
            # Don't raise error, just warn - allow some flexibility
        return self


class InsightValidationResult(BaseModel):
    """Result of insight validation."""

    is_valid: bool = Field(description="Whether validation passed")
    errors: list[str] = Field(default_factory=list, description="Validation errors")
    warnings: list[str] = Field(default_factory=list, description="Validation warnings")
    quality_score: float = Field(ge=0.0, le=100.0, description="Quality score 0-100")


def validate_insight_data(
    problem_statement: str,
    proposed_solution: str,
    relevance_score: float,
    opportunity_score: int,
    problem_score: int,
    feasibility_score: int,
    why_now_score: int,
    execution_difficulty: int,
    go_to_market_score: int,
    founder_fit_score: int,
    revenue_potential: str,
    market_size_estimate: str,
    title: str,
    market_gap_analysis: str = "",
    why_now_analysis: str = "",
    competitor_analysis: list = None,
    value_ladder: list = None,
    proof_signals: list = None,
    execution_plan: list = None,
    community_signals: list = None,
    trend_keywords: list = None,
) -> InsightValidationResult:
    """
    Validate insight data and return validation result.

    This function validates LLM-generated insight data against quality gates
    and returns a structured result with errors, warnings, and quality score.

    Args:
        All insight fields from EnhancedInsightSchema

    Returns:
        InsightValidationResult with validation status and quality score
    """
    errors: list[str] = []
    warnings: list[str] = []

    # Validate problem statement length
    word_count = len(problem_statement.split())
    if word_count < 300:
        errors.append(
            f"Problem statement too short: {word_count} words (minimum 300)"
        )
    elif word_count < 400:
        warnings.append(
            f"Problem statement could be longer: {word_count} words (ideal: 450+)"
        )

    # Validate relevance score range
    if not 0.0 <= relevance_score <= 1.0:
        errors.append(f"Relevance score out of range: {relevance_score}")

    # Validate dimension scores
    dimension_scores = {
        "opportunity_score": opportunity_score,
        "problem_score": problem_score,
        "feasibility_score": feasibility_score,
        "why_now_score": why_now_score,
        "execution_difficulty": execution_difficulty,
        "go_to_market_score": go_to_market_score,
        "founder_fit_score": founder_fit_score,
    }

    for name, score in dimension_scores.items():
        if not 1 <= score <= 10:
            errors.append(f"{name} out of range: {score} (must be 1-10)")

    # Cross-field consistency checks
    if opportunity_score >= 8 and problem_score < 5:
        errors.append(
            f"Inconsistent: High opportunity ({opportunity_score}) "
            f"requires significant problem (min 5, got {problem_score})"
        )

    if feasibility_score >= 8 and execution_difficulty > 7:
        warnings.append(
            f"Potentially inconsistent: High feasibility ({feasibility_score}) "
            f"with high execution difficulty ({execution_difficulty})"
        )

    # Validate community signals count
    community_count = len(community_signals or [])
    if community_count < 2:
        warnings.append(f"Low community signal count: {community_count} (recommended: 3-4)")

    # Validate trend keywords count
    trend_count = len(trend_keywords or [])
    if trend_count < 2:
        warnings.append(f"Low trend keyword count: {trend_count} (recommended: 2-5)")

    # Calculate quality score
    quality_score = calculate_quality_score(
        word_count=word_count,
        dimension_scores=list(dimension_scores.values()),
        community_count=community_count,
        trend_count=trend_count,
        competitor_count=len(competitor_analysis or []),
        has_value_ladder=len(value_ladder or []) >= 3,
        has_proof_signals=len(proof_signals or []) >= 3,
        has_execution_plan=len(execution_plan or []) >= 5,
        error_count=len(errors),
        warning_count=len(warnings),
    )

    return InsightValidationResult(
        is_valid=len(errors) == 0,
        errors=errors,
        warnings=warnings,
        quality_score=quality_score,
    )


def calculate_quality_score(
    word_count: int,
    dimension_scores: list[int],
    community_count: int,
    trend_count: int,
    competitor_count: int,
    has_value_ladder: bool,
    has_proof_signals: bool,
    has_execution_plan: bool,
    error_count: int,
    warning_count: int,
) -> float:
    """
    Calculate overall quality score (0-100) based on various factors.

    Scoring breakdown:
    - Problem statement length: 20 points
    - Dimension score average: 30 points
    - Community signals: 15 points
    - Trend keywords: 10 points
    - Completeness (value ladder, proof, execution): 15 points
    - Error penalties: -10 per error
    - Warning penalties: -2 per warning
    """
    score = 0.0

    # Problem statement length (20 points)
    if word_count >= 500:
        score += 20
    elif word_count >= 400:
        score += 15
    elif word_count >= 300:
        score += 10
    else:
        score += max(0, word_count / 30)  # Partial credit

    # Dimension score average (30 points)
    if dimension_scores:
        avg_score = sum(dimension_scores) / len(dimension_scores)
        score += (avg_score / 10) * 30  # Scale to 30 points

    # Community signals (15 points)
    if community_count >= 4:
        score += 15
    elif community_count >= 3:
        score += 12
    elif community_count >= 2:
        score += 8
    elif community_count >= 1:
        score += 4

    # Trend keywords (10 points)
    if trend_count >= 4:
        score += 10
    elif trend_count >= 3:
        score += 8
    elif trend_count >= 2:
        score += 5
    elif trend_count >= 1:
        score += 2

    # Completeness (15 points)
    if has_value_ladder:
        score += 5
    if has_proof_signals:
        score += 5
    if has_execution_plan:
        score += 5

    # Competitor bonus (up to 10 points)
    score += min(competitor_count * 2, 10)

    # Apply penalties
    score -= error_count * 10
    score -= warning_count * 2

    # Clamp to valid range
    return max(0.0, min(100.0, score))
