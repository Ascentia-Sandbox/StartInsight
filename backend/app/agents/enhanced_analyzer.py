"""Enhanced AI analyzer agent for 8-dimension scoring (Phase 4.3).

This agent extends the base analyzer with IdeaBrowser-parity features:
- 8-dimension scoring model
- Value ladder (4-tier pricing)
- Market gap analysis
- Why now analysis
- Proof signals
- Execution plan

Uses PydanticAI with Gemini 2.0 Flash for structured output.
See architecture.md "Enhanced Scoring Architecture" for specification.
"""

import logging
import time
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl
from pydantic_ai import Agent
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.models.insight import Insight
from app.models.raw_signal import RawSignal
from app.monitoring.metrics import get_metrics_tracker

logger = logging.getLogger(__name__)


# ============================================================
# Pydantic Schemas for Enhanced Structured LLM Output
# ============================================================


class Competitor(BaseModel):
    """Individual competitor entry in the analysis."""

    name: str = Field(description="Competitor company/product name")
    url: HttpUrl = Field(description="Competitor website URL")
    description: str = Field(
        description="Brief description of what they do (max 100 chars)"
    )
    market_position: Literal["Small", "Medium", "Large"] | None = Field(
        None, description="Estimated market presence"
    )


class ValueLadderTier(BaseModel):
    """Single tier in the value ladder (4 tiers total)."""

    tier: Literal["lead_magnet", "frontend", "core", "backend"] = Field(
        description="Tier name"
    )
    price: str = Field(
        description="Price range: Free, $9-$29/mo, $49-$99/mo, $299+/mo"
    )
    name: str = Field(description="Product name for this tier (max 50 chars)")
    description: str = Field(description="What this tier offers (max 200 chars)")
    features: list[str] = Field(
        default_factory=list,
        max_length=5,
        description="Key features (3-5 bullet points)",
    )


class ProofSignal(BaseModel):
    """Validation evidence piece (3-5 required)."""

    signal_type: Literal[
        "search_trend", "competitor_growth", "community_discussion", "market_report"
    ] = Field(description="Type of proof signal")
    description: str = Field(description="Evidence description (max 200 chars)")
    source: str = Field(description="Where found (URL or platform name)")
    confidence: Literal["Low", "Medium", "High"] = Field(
        description="Confidence level"
    )


class ExecutionStep(BaseModel):
    """Single step in the execution plan (5-7 required)."""

    step_number: int = Field(ge=1, le=10, description="Step number (1-7)")
    title: str = Field(description="Step title (max 100 chars)")
    description: str = Field(description="What to do (max 500 chars)")
    estimated_time: str = Field(description="e.g., '1 week', '2-3 days'")
    resources_needed: list[str] = Field(
        default_factory=list, max_length=5, description="Required resources"
    )


class EnhancedInsightSchema(BaseModel):
    """Enhanced structured LLM output with 8-dimension scoring."""

    # Basic insight fields
    title: str = Field(
        description="Concise insight title (max 200 chars)", max_length=200
    )
    problem_statement: str = Field(
        description="Clearly articulated market problem (max 1000 chars)",
        max_length=1000,
    )
    proposed_solution: str = Field(
        description="Suggested solution approach (max 1000 chars)", max_length=1000
    )
    market_size_estimate: Literal["Small", "Medium", "Large"] = Field(
        description="Market TAM: Small (<$100M), Medium ($100M-$1B), Large (>$1B)"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Signal relevance (0.0=weak, 1.0=strong)"
    )
    competitor_analysis: list[Competitor] = Field(
        default_factory=list,
        max_length=3,
        description="Top 3 competitors (if any)",
    )

    # ============================================
    # 8-Dimension Scoring (1-10 scale)
    # ============================================

    opportunity_score: int = Field(
        ge=1, le=10, description="Market size: 1=tiny niche, 10=massive global market"
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
    revenue_potential: Literal["$", "$$", "$$$", "$$$$"] = Field(
        description="$=<$10K/mo, $$=$10K-$50K/mo, $$$=$50K-$200K/mo, $$$$=>$200K/mo"
    )
    execution_difficulty: int = Field(
        ge=1, le=10, description="Complexity: 1=weekend project, 10=multi-year enterprise"
    )
    go_to_market_score: int = Field(
        ge=1, le=10, description="Distribution: 1=enterprise sales, 10=viral PLG"
    )
    founder_fit_score: int = Field(
        ge=1, le=10, description="Skills: 1=PhD + 10 years, 10=anyone can learn"
    )

    # ============================================
    # Advanced Frameworks (IdeaBrowser Parity)
    # ============================================

    value_ladder: list[ValueLadderTier] = Field(
        min_length=4,
        max_length=4,
        description="4-tier pricing model (lead_magnet, frontend, core, backend)",
    )
    market_gap_analysis: str = Field(
        min_length=100,
        max_length=2000,
        description="200-500 word analysis of competitor gaps",
    )
    why_now_analysis: str = Field(
        min_length=100,
        max_length=2000,
        description="200-500 word analysis of market timing",
    )
    proof_signals: list[ProofSignal] = Field(
        min_length=3, max_length=5, description="3-5 validation evidence pieces"
    )
    execution_plan: list[ExecutionStep] = Field(
        min_length=5, max_length=7, description="5-7 actionable launch steps"
    )


# ============================================================
# Enhanced System Prompt
# ============================================================

ENHANCED_SYSTEM_PROMPT = """You are an expert startup analyst with deep expertise in market analysis, competitive intelligence, and go-to-market strategy.

Your task is to analyze market signals and provide a comprehensive business opportunity assessment using 8-dimension scoring and advanced frameworks.

## 8-Dimension Scoring Model (1-10 scale)

1. **opportunity_score** (Market Size)
   - 1-3: Tiny niche (<$10M TAM)
   - 4-6: Moderate market ($10M-$500M TAM)
   - 7-10: Large/massive market ($500M+ TAM)

2. **problem_score** (Pain Severity)
   - 1-3: Nice-to-have, weak pain point
   - 4-6: Moderate pain, some urgency
   - 7-10: Hair-on-fire, existential problem

3. **feasibility_score** (Technical Difficulty)
   - 1-3: Requires major R&D, breakthrough tech
   - 4-6: Challenging but achievable with good team
   - 7-10: Well-understood tech, can be built quickly

4. **why_now_score** (Market Timing)
   - 1-3: Too early or too late
   - 4-6: Market developing, some tailwinds
   - 7-10: Perfect timing, major inflection point

5. **revenue_potential** (Monthly Revenue at Scale)
   - $: <$10K/mo (lifestyle business)
   - $$: $10K-$50K/mo (solid small business)
   - $$$: $50K-$200K/mo (venture-scale)
   - $$$$: >$200K/mo (unicorn potential)

6. **execution_difficulty** (Operational Complexity)
   - 1-3: Weekend project, solo founder can do
   - 4-6: Needs small team, some ops complexity
   - 7-10: Multi-year, large team, enterprise ops

7. **go_to_market_score** (Distribution Ease)
   - 1-3: Enterprise sales, long cycles
   - 4-6: SMB sales, content marketing
   - 7-10: Viral/PLG, self-serve, community-driven

8. **founder_fit_score** (Skill Requirements)
   - 1-3: Requires PhD, 10+ years domain expertise
   - 4-6: Needs some specialized knowledge
   - 7-10: General skills, anyone can learn

## Advanced Frameworks

### Value Ladder (4 Tiers)
Create a complete pricing strategy:
- **lead_magnet**: Free tier (Free) - Hook to acquire users
- **frontend**: Entry tier ($9-$29/mo) - Low-risk first purchase
- **core**: Main tier ($49-$99/mo) - Main revenue driver
- **backend**: Premium tier ($299+/mo) - High-value enterprise

### Market Gap Analysis (200-500 words)
Identify what competitors are missing:
- Unmet customer needs
- Price/value gaps
- Feature gaps
- Service/support gaps
- Target segment gaps

### Why Now Analysis (200-500 words)
Explain market timing drivers:
- Technology enablers
- Regulatory changes
- Market shifts
- Consumer behavior changes
- Cost structure changes

### Proof Signals (3-5 pieces)
Evidence validating the opportunity:
- search_trend: Google Trends, keyword growth
- competitor_growth: Competitor funding, growth metrics
- community_discussion: Reddit, HN, forum activity
- market_report: Industry reports, analyst insights

### Execution Plan (5-7 steps)
Actionable launch roadmap:
- Step 1: MVP/validation (1-2 weeks)
- Step 2: First 10 users (1-2 weeks)
- Step 3: Product iteration (2-4 weeks)
- Step 4: Growth experiments (2-4 weeks)
- Step 5: Scale preparation (2-4 weeks)

## Output Format
Return a structured JSON object matching the EnhancedInsightSchema format.
Be specific, actionable, and realistic in your analysis."""


# ============================================================
# PydanticAI Agent Configuration
# ============================================================


def get_enhanced_agent() -> Agent:
    """Get PydanticAI agent for enhanced analysis (API key from GOOGLE_API_KEY env)."""
    return Agent(
        model="google-gla:gemini-2.0-flash",
        system_prompt=ENHANCED_SYSTEM_PROMPT,
        output_type=EnhancedInsightSchema,
    )


# ============================================================
# Core Enhanced Analysis Function
# ============================================================


async def analyze_signal_enhanced(raw_signal: RawSignal) -> Insight:
    """
    Analyze a raw signal with enhanced 8-dimension scoring.

    Args:
        raw_signal: The raw signal to analyze

    Returns:
        Insight: Structured insight with 8-dimension scores and advanced frameworks

    Raises:
        Exception: If analysis fails after retries
    """
    metrics_tracker = get_metrics_tracker()
    start_time = time.time()

    try:
        # Get enhanced agent instance
        agent = get_enhanced_agent()

        # Call PydanticAI agent with enhanced schema
        result = await agent.run(raw_signal.content)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Extract structured data from agent response
        insight_data = result.output

        # Estimate tokens (rough approximation: ~4 chars per token)
        input_tokens = len(raw_signal.content) // 4
        output_tokens = (
            len(insight_data.problem_statement)
            + len(insight_data.proposed_solution)
            + len(insight_data.title)
            + len(insight_data.market_gap_analysis)
            + len(insight_data.why_now_analysis)
        ) // 4

        # Track LLM call metrics
        metrics_tracker.track_llm_call(
            model="gemini-2.0-flash",
            prompt=raw_signal.content[:200] + "...",  # Log first 200 chars
            response=insight_data.title,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True,
        )

        # Convert to database Insight model with enhanced fields
        insight = Insight(
            raw_signal_id=raw_signal.id,
            # Basic fields
            title=insight_data.title,
            problem_statement=insight_data.problem_statement,
            proposed_solution=insight_data.proposed_solution,
            market_size_estimate=insight_data.market_size_estimate,
            relevance_score=insight_data.relevance_score,
            competitor_analysis=[
                c.model_dump() for c in insight_data.competitor_analysis
            ],
            # 8-dimension scores
            opportunity_score=insight_data.opportunity_score,
            problem_score=insight_data.problem_score,
            feasibility_score=insight_data.feasibility_score,
            why_now_score=insight_data.why_now_score,
            revenue_potential=insight_data.revenue_potential,
            execution_difficulty=insight_data.execution_difficulty,
            go_to_market_score=insight_data.go_to_market_score,
            founder_fit_score=insight_data.founder_fit_score,
            # Advanced frameworks
            value_ladder=[t.model_dump() for t in insight_data.value_ladder],
            market_gap_analysis=insight_data.market_gap_analysis,
            why_now_analysis=insight_data.why_now_analysis,
            proof_signals=[p.model_dump() for p in insight_data.proof_signals],
            execution_plan=[s.model_dump() for s in insight_data.execution_plan],
        )

        # Track successful insight generation
        metrics_tracker.track_insight_generated(insight_data.relevance_score)

        logger.info(
            f"Enhanced analysis successful for signal {raw_signal.id}: "
            f"{insight_data.title} (opportunity: {insight_data.opportunity_score}, "
            f"feasibility: {insight_data.feasibility_score})"
        )

        return insight

    except Exception as e:
        # Calculate latency even for failed calls
        latency_ms = (time.time() - start_time) * 1000

        # Track failed LLM call
        input_tokens = len(raw_signal.content) // 4
        metrics_tracker.track_llm_call(
            model="gemini-2.0-flash",
            prompt=raw_signal.content[:200] + "...",
            response=None,
            input_tokens=input_tokens,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error=str(e),
        )

        # Track failed insight generation
        metrics_tracker.track_insight_failed(e)

        logger.error(f"Enhanced analysis failed for signal {raw_signal.id}: {e}")
        raise


# ============================================================
# Retry Logic with Tenacity
# ============================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def analyze_signal_enhanced_with_retry(raw_signal: RawSignal) -> Insight:
    """
    Analyze signal with enhanced scoring and automatic retry on failures.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s, max 10s).

    Args:
        raw_signal: The raw signal to analyze

    Returns:
        Insight: Structured insight with 8-dimension scores

    Raises:
        Exception: If analysis fails after all retries
    """
    try:
        return await analyze_signal_enhanced(raw_signal)
    except Exception as e:
        logger.error(
            f"Enhanced analysis failed for signal {raw_signal.id} after retries: {e}"
        )
        raise


# ============================================================
# Upgrade Existing Insight (Re-analyze with Enhanced Scoring)
# ============================================================


async def upgrade_insight_scoring(
    raw_signal: RawSignal, existing_insight: Insight
) -> Insight:
    """
    Upgrade an existing insight with enhanced 8-dimension scoring.

    This preserves the original insight ID and basic fields while adding
    enhanced scoring and frameworks.

    Args:
        raw_signal: The source raw signal
        existing_insight: The existing insight to upgrade

    Returns:
        Insight: Updated insight with enhanced scoring
    """
    metrics_tracker = get_metrics_tracker()
    start_time = time.time()

    try:
        # Get enhanced agent
        agent = get_enhanced_agent()

        # Call with enhanced prompt
        result = await agent.run(raw_signal.content)
        insight_data = result.output

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Update existing insight with enhanced fields
        existing_insight.title = insight_data.title
        existing_insight.opportunity_score = insight_data.opportunity_score
        existing_insight.problem_score = insight_data.problem_score
        existing_insight.feasibility_score = insight_data.feasibility_score
        existing_insight.why_now_score = insight_data.why_now_score
        existing_insight.revenue_potential = insight_data.revenue_potential
        existing_insight.execution_difficulty = insight_data.execution_difficulty
        existing_insight.go_to_market_score = insight_data.go_to_market_score
        existing_insight.founder_fit_score = insight_data.founder_fit_score
        existing_insight.value_ladder = [
            t.model_dump() for t in insight_data.value_ladder
        ]
        existing_insight.market_gap_analysis = insight_data.market_gap_analysis
        existing_insight.why_now_analysis = insight_data.why_now_analysis
        existing_insight.proof_signals = [
            p.model_dump() for p in insight_data.proof_signals
        ]
        existing_insight.execution_plan = [
            s.model_dump() for s in insight_data.execution_plan
        ]

        # Track metrics
        input_tokens = len(raw_signal.content) // 4
        output_tokens = (
            len(insight_data.market_gap_analysis)
            + len(insight_data.why_now_analysis)
        ) // 4

        metrics_tracker.track_llm_call(
            model="gemini-2.0-flash",
            prompt=f"Upgrade insight {existing_insight.id}",
            response=insight_data.title,
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True,
        )

        logger.info(
            f"Upgraded insight {existing_insight.id} with enhanced scoring: "
            f"opportunity={insight_data.opportunity_score}, "
            f"feasibility={insight_data.feasibility_score}"
        )

        return existing_insight

    except Exception as e:
        logger.error(f"Failed to upgrade insight {existing_insight.id}: {e}")
        raise


# ============================================================
# Aggregate Score Calculation
# ============================================================


def calculate_aggregate_score(insight: Insight) -> float | None:
    """
    Calculate weighted aggregate score from 8 dimensions.

    Weights:
    - opportunity_score: 20%
    - problem_score: 20%
    - feasibility_score: 15%
    - why_now_score: 15%
    - go_to_market_score: 15%
    - founder_fit_score: 10%
    - execution_ease (inverse of difficulty): 5%

    Args:
        insight: Insight with 8-dimension scores

    Returns:
        float: Aggregate score (0.0-10.0) or None if scores missing
    """
    if not all([
        insight.opportunity_score,
        insight.problem_score,
        insight.feasibility_score,
        insight.why_now_score,
        insight.execution_difficulty,
        insight.go_to_market_score,
        insight.founder_fit_score,
    ]):
        return None

    # Weights for each dimension
    weights = {
        "opportunity": 0.20,
        "problem": 0.20,
        "feasibility": 0.15,
        "why_now": 0.15,
        "go_to_market": 0.15,
        "founder_fit": 0.10,
        "execution_ease": 0.05,
    }

    # Calculate weighted score (execution_difficulty is inverse)
    execution_ease = 11 - insight.execution_difficulty  # Invert: 10->1, 1->10
    score = (
        insight.opportunity_score * weights["opportunity"]
        + insight.problem_score * weights["problem"]
        + insight.feasibility_score * weights["feasibility"]
        + insight.why_now_score * weights["why_now"]
        + insight.go_to_market_score * weights["go_to_market"]
        + insight.founder_fit_score * weights["founder_fit"]
        + execution_ease * weights["execution_ease"]
    )

    return round(score, 2)
