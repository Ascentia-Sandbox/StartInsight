"""Enhanced Insight schemas - Phase 4.3 multi-dimensional scoring.

8-Dimension Scoring Model:
- opportunity_score: Market size (1-10)
- problem_score: Pain severity (1-10)
- feasibility_score: Technical difficulty (1-10)
- why_now_score: Market timing (1-10)
- revenue_potential: $, $$, $$$, $$$$
- execution_difficulty: Complexity (1-10)
- go_to_market_score: Distribution ease (1-10)
- founder_fit_score: Skill requirements (1-10)

See architecture.md "Enhanced Scoring Architecture" for full specification.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================
# Score Enums and Types
# ============================================


class RevenuePotential(str):
    """Revenue potential levels."""

    LOW = "$"
    MEDIUM = "$$"
    HIGH = "$$$"
    VERY_HIGH = "$$$$"


# ============================================
# Value Ladder Schemas (IdeaBrowser Parity)
# ============================================


class ValueLadderTier(BaseModel):
    """Single tier in the value ladder."""

    tier: str = Field(
        description="Tier name: lead_magnet, frontend, core, backend"
    )
    price: str = Field(
        description="Price range: Free, $9-$29/mo, $49-$99/mo, $299+/mo"
    )
    name: str = Field(description="Product name for this tier")
    description: str = Field(description="What this tier offers")
    features: list[str] = Field(default_factory=list, description="Key features")


# ============================================
# Proof Signal Schemas
# ============================================


class ProofSignal(BaseModel):
    """Validation evidence piece."""

    signal_type: str = Field(
        description="Type: search_trend, competitor_growth, community_discussion, market_report"
    )
    description: str = Field(description="Evidence description")
    source: str = Field(description="Where found (URL or platform)")
    confidence: str = Field(description="Low, Medium, High")


# ============================================
# Execution Plan Schemas
# ============================================


class ExecutionStep(BaseModel):
    """Single step in execution plan."""

    step_number: int = Field(ge=1, le=10)
    title: str = Field(max_length=100)
    description: str = Field(max_length=500)
    estimated_time: str = Field(description="e.g., '1 week', '2-3 days'")
    resources_needed: list[str] = Field(default_factory=list)


# ============================================
# Enhanced Score Schemas
# ============================================


class EnhancedScoreBase(BaseModel):
    """Base 8-dimension scores."""

    # Core Opportunity Metrics (1-10)
    opportunity_score: int = Field(
        ge=1, le=10, description="Market size: 1=tiny, 10=massive"
    )
    problem_score: int = Field(
        ge=1, le=10, description="Pain severity: 1=nice-to-have, 10=existential"
    )
    feasibility_score: int = Field(
        ge=1, le=10, description="Technical ease: 1=breakthrough needed, 10=weekend project"
    )
    why_now_score: int = Field(
        ge=1, le=10, description="Market timing: 1=too early/late, 10=perfect inflection"
    )

    # Business Fit Metrics
    revenue_potential: str = Field(
        pattern="^\\${1,4}$", description="$=low, $$=medium, $$$=high, $$$$=very high"
    )
    execution_difficulty: int = Field(
        ge=1, le=10, description="Complexity: 1=weekend, 10=multi-year enterprise"
    )
    go_to_market_score: int = Field(
        ge=1, le=10, description="Distribution: 1=enterprise sales, 10=viral PLG"
    )
    founder_fit_score: int = Field(
        ge=1, le=10, description="Skills: 1=PhD + 10 years, 10=anyone can learn"
    )


class EnhancedInsightCreate(EnhancedScoreBase):
    """Schema for creating enhanced insight from LLM analysis."""

    # Basic insight fields
    title: str = Field(max_length=200)
    problem_statement: str = Field(max_length=1000)
    proposed_solution: str = Field(max_length=1000)
    market_size_estimate: str = Field(
        pattern="^(Small|Medium|Large)$", description="Market TAM category"
    )
    relevance_score: float = Field(ge=0.0, le=1.0)
    competitor_analysis: list[dict] = Field(default_factory=list)

    # Advanced frameworks
    value_ladder: list[ValueLadderTier] = Field(
        min_length=4, max_length=4, description="4-tier pricing model"
    )
    market_gap_analysis: str = Field(
        min_length=100, max_length=2000, description="200-500 words on competitor gaps"
    )
    why_now_analysis: str = Field(
        min_length=100, max_length=2000, description="200-500 words on timing"
    )
    proof_signals: list[ProofSignal] = Field(
        min_length=3, max_length=5, description="3-5 validation evidence pieces"
    )
    execution_plan: list[ExecutionStep] = Field(
        min_length=5, max_length=7, description="5-7 actionable launch steps"
    )


class EnhancedScoreResponse(EnhancedScoreBase):
    """Enhanced scores in API response."""

    # Computed aggregate score
    aggregate_score: float = Field(
        ge=0.0, le=10.0, description="Weighted average of all scores"
    )


class EnhancedInsightResponse(BaseModel):
    """Full enhanced insight response."""

    id: UUID
    raw_signal_id: UUID

    # Basic fields
    title: str | None = None
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float

    # Enhanced 8-dimension scores
    opportunity_score: int | None = None
    problem_score: int | None = None
    feasibility_score: int | None = None
    why_now_score: int | None = None
    revenue_potential: str | None = None
    execution_difficulty: int | None = None
    go_to_market_score: int | None = None
    founder_fit_score: int | None = None

    # Advanced frameworks
    value_ladder: list[dict] | None = None
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None
    proof_signals: list[dict] | None = None
    execution_plan: list[dict] | None = None

    # Metadata
    created_at: datetime
    competitor_analysis: list[dict] = Field(default_factory=list)

    # Computed
    aggregate_score: float | None = None

    model_config = ConfigDict(from_attributes=True)

    def calculate_aggregate_score(self) -> float | None:
        """Calculate weighted aggregate of all scores."""
        if not all(
            [
                self.opportunity_score,
                self.problem_score,
                self.feasibility_score,
                self.why_now_score,
                self.execution_difficulty,
                self.go_to_market_score,
                self.founder_fit_score,
            ]
        ):
            return None

        # Weights for each dimension
        weights = {
            "opportunity": 0.20,
            "problem": 0.20,
            "feasibility": 0.15,
            "why_now": 0.15,
            "go_to_market": 0.15,
            "founder_fit": 0.10,
            # execution_difficulty is inverse (lower = better)
            "execution_ease": 0.05,
        }

        # Calculate weighted score
        execution_ease = 11 - self.execution_difficulty  # Invert: 10->1, 1->10
        score = (
            self.opportunity_score * weights["opportunity"]
            + self.problem_score * weights["problem"]
            + self.feasibility_score * weights["feasibility"]
            + self.why_now_score * weights["why_now"]
            + self.go_to_market_score * weights["go_to_market"]
            + self.founder_fit_score * weights["founder_fit"]
            + execution_ease * weights["execution_ease"]
        )

        return round(score, 2)


class ScoreFilter(BaseModel):
    """Filter criteria for enhanced scores."""

    min_opportunity: int | None = Field(None, ge=1, le=10)
    min_problem: int | None = Field(None, ge=1, le=10)
    min_feasibility: int | None = Field(None, ge=1, le=10)
    min_why_now: int | None = Field(None, ge=1, le=10)
    max_execution_difficulty: int | None = Field(None, ge=1, le=10)
    min_go_to_market: int | None = Field(None, ge=1, le=10)
    min_founder_fit: int | None = Field(None, ge=1, le=10)
    revenue_potential: list[str] | None = Field(None, description="Filter by $, $$, $$$, $$$$")


class ScoreRanking(BaseModel):
    """Ranking criteria for enhanced insights."""

    sort_by: str = Field(
        default="aggregate",
        description="Sort field: aggregate, opportunity, problem, feasibility, why_now, execution, go_to_market, founder_fit",
    )
    ascending: bool = Field(default=False, description="Sort order")
