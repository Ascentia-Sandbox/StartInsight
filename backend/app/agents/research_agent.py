"""AI Research Agent for 40-step deep analysis - Phase 5.1.

Performs comprehensive startup idea analysis using Claude 3.5 Sonnet:
- Market analysis (TAM/SAM/SOM)
- Competitor landscape
- Value equation (Hormozi framework)
- Market matrix positioning
- A-C-P framework
- Validation signals
- Execution roadmap
- Risk assessment

See architecture.md "Research Agent Architecture" for specification.
"""

import asyncio
import logging
import time
from typing import Any

from pydantic import BaseModel, Field
from pydantic_ai import Agent
from tenacity import (
    retry,
    retry_if_exception_type,
    stop_after_attempt,
    wait_exponential,
)

from app.core.config import settings
from app.monitoring.metrics import get_metrics_tracker
from app.schemas.research import (
    ACPFramework,
    CompetitorProfile,
    ExecutionPhase,
    MarketAnalysis,
    MarketMatrix,
    RiskAssessment,
    ValidationSignal,
    ValueEquation,
)

logger = logging.getLogger(__name__)


# ============================================================
# Combined Research Output Schema
# ============================================================


class ResearchResult(BaseModel):
    """Complete research analysis output from LLM."""

    # Market Analysis
    market_analysis: MarketAnalysis

    # Competitors (top 5-10)
    competitor_landscape: list[CompetitorProfile] = Field(
        min_length=3, max_length=10, description="Top 5-10 competitors"
    )

    # Value Equation
    value_equation: ValueEquation

    # Market Matrix
    market_matrix: MarketMatrix

    # A-C-P Framework
    acp_framework: ACPFramework

    # Validation Signals (3-5)
    validation_signals: list[ValidationSignal] = Field(
        min_length=3, max_length=5, description="3-5 validation signals"
    )

    # Execution Roadmap (4-5 phases)
    execution_roadmap: list[ExecutionPhase] = Field(
        min_length=4, max_length=5, description="4-5 execution phases"
    )

    # Risk Assessment
    risk_assessment: RiskAssessment

    # Summary Scores (0-1)
    opportunity_score: float = Field(
        ge=0, le=1, description="Overall opportunity score (0-1)"
    )
    market_fit_score: float = Field(
        ge=0, le=1, description="Product-market fit score (0-1)"
    )
    execution_readiness: float = Field(
        ge=0, le=1, description="Execution readiness score (0-1)"
    )


# ============================================================
# Research Agent System Prompt
# ============================================================

RESEARCH_SYSTEM_PROMPT = """You are an expert startup analyst and venture capital advisor with deep expertise in:
- Market sizing and TAM/SAM/SOM analysis
- Competitive intelligence and landscape mapping
- Go-to-market strategy and execution planning
- Risk assessment and mitigation strategies

Your task is to perform a comprehensive 40-step analysis of a startup idea.

## Analysis Framework

### 1. Market Analysis (TAM/SAM/SOM)
- TAM: Total Addressable Market (global opportunity)
- SAM: Serviceable Addressable Market (target segment)
- SOM: Serviceable Obtainable Market (realistic 3-year capture)
- Growth Rate: Annual market growth rate (as decimal, e.g., 0.15 for 15%)
- Market Maturity: nascent, growing, mature, or declining
- Key Trends: 3-5 major market trends driving growth

### 2. Competitor Landscape (5-10 competitors)
For each competitor:
- Name, URL, funding stage
- Unique value proposition
- Key weakness or gap we can exploit
- Estimated market share (0-100%)
- Threat level: low, medium, or high

### 3. Value Equation (Hormozi Framework)
Value = (Dream Outcome × Perceived Likelihood) / (Time Delay × Effort/Sacrifice)
- Score each factor 1-10
- Calculate value_score = (dream × likelihood) / (time × effort)
- Provide 200-word analysis

### 4. Market Matrix (2x2 Positioning)
- Demand Score (1-10): Market pull strength
- Difficulty Score (1-10): Execution complexity
- Quadrant:
  - star: High demand, Low difficulty (best)
  - cash_cow: High demand, High difficulty
  - question_mark: Low demand, Low difficulty
  - dog: Low demand, High difficulty (avoid)
- Positioning strategy recommendation

### 5. A-C-P Framework (Awareness → Consideration → Purchase)
- Awareness Score (1-10): Target market awareness
- Consideration Score (1-10): Likelihood to consider product
- Purchase Score (1-10): Purchase readiness
- Identify primary funnel bottleneck
- Recommend top 3 acquisition channels

### 6. Validation Signals (3-5 signals)
Evidence supporting the opportunity:
- Source platform (Reddit, Product Hunt, HN, Twitter, etc.)
- Signal type: discussion, launch, trend, review
- Description of the signal
- Sentiment: positive, neutral, negative
- Strength: weak, moderate, strong

### 7. Execution Roadmap (4-5 phases)
For each phase:
- Phase number and name (MVP, Launch, Growth, Scale, etc.)
- Duration estimate
- Key milestones (3-5)
- Budget estimate
- Phase-specific risks

### 8. Risk Assessment
- Technical Risk (1-10)
- Market Risk (1-10)
- Team Risk (1-10)
- Financial Risk (1-10)
- Overall Risk = weighted average (0-1)
- Top 3 mitigation strategies

### 9. Summary Scores (0-1 scale)
- opportunity_score: Overall opportunity attractiveness
- market_fit_score: Product-market fit potential
- execution_readiness: How ready the idea is for execution

## Guidelines
- Be specific and actionable, not generic
- Use real competitor names when possible
- Provide realistic, not optimistic, assessments
- Consider the user's stated budget range
- Format all monetary values consistently (e.g., "$5M")

## Output Format
Return a structured JSON object matching the ResearchResult schema."""


# ============================================================
# PydanticAI Agent Configuration
# ============================================================


def get_research_agent() -> Agent:
    """Get PydanticAI agent for research analysis (API key from environment)."""
    return Agent(
        model="anthropic:claude-3-5-sonnet-20241022",
        system_prompt=RESEARCH_SYSTEM_PROMPT,
        result_type=ResearchResult,
    )


# ============================================================
# Cost Limits and Timeouts
# ============================================================

# Maximum cost per analysis ($5 USD)
MAX_COST_PER_ANALYSIS = 5.0

# Maximum execution time (5 minutes)
MAX_ANALYSIS_TIMEOUT_SECONDS = 300


# ============================================================
# Research Analysis Function
# ============================================================


async def analyze_idea(
    idea_description: str,
    target_market: str,
    budget_range: str = "unknown",
) -> tuple[ResearchResult, int, float]:
    """
    Perform 40-step research analysis on a startup idea.

    Args:
        idea_description: User's startup idea (50-2000 chars)
        target_market: Target market description
        budget_range: Budget range (bootstrap, 10k-50k, 50k-200k, 200k+, unknown)

    Returns:
        tuple: (ResearchResult, tokens_used, cost_usd)

    Raises:
        Exception: If analysis fails after retries
    """
    metrics_tracker = get_metrics_tracker()
    start_time = time.time()

    # Construct the analysis prompt
    prompt = f"""Analyze this startup idea:

## Idea Description
{idea_description}

## Target Market
{target_market}

## Budget Range
{budget_range}

Please provide a comprehensive 40-step analysis following all frameworks:
1. Market Analysis (TAM/SAM/SOM)
2. Competitor Landscape (5-10 competitors)
3. Value Equation (Hormozi framework)
4. Market Matrix (2x2 positioning)
5. A-C-P Framework
6. Validation Signals (3-5)
7. Execution Roadmap (4-5 phases)
8. Risk Assessment
9. Summary Scores"""

    try:
        # Get research agent
        agent = get_research_agent()

        # ✅ Execute analysis with timeout protection (5 minutes max)
        try:
            result = await asyncio.wait_for(
                agent.run(prompt),
                timeout=MAX_ANALYSIS_TIMEOUT_SECONDS,
            )
        except asyncio.TimeoutError:
            raise Exception(
                f"Analysis timed out after {MAX_ANALYSIS_TIMEOUT_SECONDS}s. "
                "This may indicate an API issue or overly complex analysis."
            )

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Extract result
        research_data = result.data

        # ✅ Get actual token counts from PydanticAI response
        # PydanticAI stores usage in result.usage() if available
        input_tokens = 0
        output_tokens = 0

        # Try to get actual token counts from result
        if hasattr(result, 'usage') and result.usage:
            usage = result.usage()
            input_tokens = getattr(usage, 'input_tokens', 0) or getattr(usage, 'prompt_tokens', 0)
            output_tokens = getattr(usage, 'output_tokens', 0) or getattr(usage, 'completion_tokens', 0)

        # Fallback to estimation if no usage data
        if input_tokens == 0:
            input_tokens = len(prompt) // 4  # Rough estimate: 4 chars per token
        if output_tokens == 0:
            # Estimate based on serialized output length
            output_str = research_data.model_dump_json()
            output_tokens = len(output_str) // 4

        total_tokens = input_tokens + output_tokens

        # Claude 3.5 Sonnet pricing: $15/M input, $75/M output
        input_cost = (input_tokens / 1_000_000) * 15
        output_cost = (output_tokens / 1_000_000) * 75
        total_cost = input_cost + output_cost

        # ✅ Cost cap validation
        if total_cost > MAX_COST_PER_ANALYSIS:
            logger.error(
                f"Analysis exceeded cost cap: ${total_cost:.4f} > ${MAX_COST_PER_ANALYSIS}. "
                f"Input tokens: {input_tokens}, Output tokens: {output_tokens}"
            )
            raise Exception(
                f"Analysis cost ${total_cost:.2f} exceeds maximum ${MAX_COST_PER_ANALYSIS}. "
                "Please simplify your idea description or target market."
            )

        # Track LLM metrics
        metrics_tracker.track_llm_call(
            model="claude-3-5-sonnet-20241022",
            prompt=f"Research: {idea_description[:100]}...",
            response=f"Opportunity: {research_data.opportunity_score}",
            input_tokens=input_tokens,
            output_tokens=output_tokens,
            latency_ms=latency_ms,
            success=True,
        )

        logger.info(
            f"Research analysis completed: "
            f"opportunity={research_data.opportunity_score}, "
            f"market_fit={research_data.market_fit_score}, "
            f"tokens={total_tokens}, cost=${total_cost:.4f}"
        )

        return research_data, total_tokens, total_cost

    except Exception as e:
        latency_ms = (time.time() - start_time) * 1000

        # Track failed call
        metrics_tracker.track_llm_call(
            model="claude-3-5-sonnet-20241022",
            prompt=f"Research: {idea_description[:100]}...",
            response=None,
            input_tokens=len(prompt) // 4,
            output_tokens=0,
            latency_ms=latency_ms,
            success=False,
            error=str(e),
        )

        logger.error(f"Research analysis failed: {e}")
        raise


# ============================================================
# Retry Logic
# ============================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=2, max=30),
    retry=retry_if_exception_type(Exception),
    reraise=True,
)
async def analyze_idea_with_retry(
    idea_description: str,
    target_market: str,
    budget_range: str = "unknown",
) -> tuple[ResearchResult, int, float]:
    """
    Perform research analysis with automatic retry on failures.

    Retries up to 3 times with exponential backoff (2s, 4s, 8s, max 30s).

    Args:
        idea_description: User's startup idea
        target_market: Target market description
        budget_range: Budget range

    Returns:
        tuple: (ResearchResult, tokens_used, cost_usd)
    """
    try:
        return await analyze_idea(idea_description, target_market, budget_range)
    except Exception as e:
        logger.error(f"Research analysis failed after retries: {e}")
        raise


# ============================================================
# Quota Limits by Tier
# ============================================================

RESEARCH_QUOTA_LIMITS = {
    "free": 1,  # 1 analysis per month
    "starter": 3,  # 3 analyses per month
    "pro": 10,  # 10 analyses per month
    "enterprise": 100,  # 100 analyses per month
}


def get_quota_limit(tier: str) -> int:
    """Get monthly research quota for a subscription tier."""
    return RESEARCH_QUOTA_LIMITS.get(tier, 1)
