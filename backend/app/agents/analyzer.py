"""AI analyzer agent using PydanticAI with Gemini 2.0 Flash."""

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
# Pydantic Schemas for Structured LLM Output
# ============================================================


class Competitor(BaseModel):
    """Individual competitor entry in the analysis."""

    name: str = Field(description="Competitor company/product name")
    url: HttpUrl = Field(description="Competitor website URL")
    description: str = Field(description="Brief description of what they do (max 100 chars)")
    market_position: Literal["Small", "Medium", "Large"] | None = Field(
        None, description="Estimated market presence"
    )


class InsightSchema(BaseModel):
    """Structured LLM output from signal analysis."""

    problem_statement: str = Field(
        description="Clearly articulated market problem or pain point"
    )
    proposed_solution: str = Field(
        description="Suggested solution approach or opportunity"
    )
    market_size_estimate: Literal["Small", "Medium", "Large"] = Field(
        description=(
            "Market size: Small (<$100M TAM), Medium ($100M-$1B), Large (>$1B)"
        )
    )
    relevance_score: float = Field(
        ge=0.0,
        le=1.0,
        description=(
            "Signal relevance score (0.0=weak/low quality, 1.0=strong/high quality)"
        ),
    )
    competitor_analysis: list[Competitor] = Field(
        default_factory=list,
        max_length=3,
        description="Top 3 competitors (if any). Empty list if no competitors identified.",
    )
    title: str = Field(
        description="Auto-generated concise insight title (max 100 chars)"
    )


# ============================================================
# PydanticAI Agent Configuration
# ============================================================

# System prompt for Claude 3.5 Sonnet
SYSTEM_PROMPT = """You are a startup analyst extracting market insights from web content.

Your task is to analyze market signals (scraped content from Reddit, Product Hunt, Google Trends) and identify:
1. The core problem being discussed or pain point mentioned
2. The proposed solution or business opportunity
3. Market size estimate based on Total Addressable Market (TAM) indicators
4. Relevance score based on signal strength, discussion quality, and actionability
5. Up to 3 direct competitors (with URLs, descriptions, market position)

Guidelines:
- Be concise but accurate
- Focus on actionable insights, not generic observations
- For relevance_score: 0.8+ = strong signal with clear opportunity, 0.5-0.8 = moderate signal, <0.5 = weak/speculative
- For competitors: Only include direct competitors (not tangential tools/services)
- For market_size_estimate: Use TAM indicators from the content (mentions of market size, user base, revenue potential)
- For title: Create a clear, descriptive title like "AI for Legal Document Review" or "No-Code Workflow Automation"

Output Format:
Return a structured JSON object matching the InsightSchema format."""

# Create PydanticAI agent (API key read from GOOGLE_API_KEY environment variable)
def get_agent() -> Agent[None, InsightSchema]:
    """Get PydanticAI agent (API key from environment)."""
    # PydanticAI automatically reads GOOGLE_API_KEY from environment
    return Agent(
        model="google-gla:gemini-2.0-flash",  # Using Gemini instead of Claude
        system_prompt=SYSTEM_PROMPT,
        output_type=InsightSchema,  # Changed from result_type in PydanticAI v1.x
    )


# ============================================================
# Core Analysis Function
# ============================================================


async def analyze_signal(raw_signal: RawSignal) -> Insight:
    """
    Analyze a raw signal and extract structured insights using PydanticAI.

    Args:
        raw_signal: The raw signal to analyze

    Returns:
        Insight: Structured insight extracted from the signal

    Raises:
        Exception: If analysis fails after retries
    """
    metrics_tracker = get_metrics_tracker()
    start_time = time.time()

    try:
        # Get agent instance with API key
        agent = get_agent()

        # Call PydanticAI agent
        result = await agent.run(raw_signal.content)

        # Calculate latency
        latency_ms = (time.time() - start_time) * 1000

        # Extract structured data from agent response
        insight_data = result.output  # Changed from result.data in PydanticAI v1.x

        # Estimate tokens (rough approximation: ~4 chars per token)
        input_tokens = len(raw_signal.content) // 4
        output_tokens = (
            len(insight_data.problem_statement)
            + len(insight_data.proposed_solution)
            + len(insight_data.title)
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

        # Convert to database Insight model
        insight = Insight(
            raw_signal_id=raw_signal.id,
            problem_statement=insight_data.problem_statement,
            proposed_solution=insight_data.proposed_solution,
            market_size_estimate=insight_data.market_size_estimate,
            relevance_score=insight_data.relevance_score,
            competitor_analysis=[
                c.model_dump() for c in insight_data.competitor_analysis
            ],
        )

        # Track successful insight generation
        metrics_tracker.track_insight_generated(insight_data.relevance_score)

        logger.info(
            f"Successfully analyzed signal {raw_signal.id}: "
            f"{insight_data.title} (score: {insight_data.relevance_score})"
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

        logger.error(f"Failed to analyze signal {raw_signal.id}: {e}")
        raise


# ============================================================
# Retry Logic with Tenacity
# ============================================================


@retry(
    stop=stop_after_attempt(3),
    wait=wait_exponential(multiplier=1, min=1, max=10),
    retry=retry_if_exception_type(Exception),  # Retry on any exception
    reraise=True,
)
async def analyze_signal_with_retry(raw_signal: RawSignal) -> Insight:
    """
    Analyze signal with automatic retry on failures.

    Retries up to 3 times with exponential backoff (1s, 2s, 4s, max 10s).

    Args:
        raw_signal: The raw signal to analyze

    Returns:
        Insight: Structured insight extracted from the signal

    Raises:
        Exception: If analysis fails after all retries
    """
    try:
        return await analyze_signal(raw_signal)

    except Exception as e:
        logger.error(
            f"Analysis failed for signal {raw_signal.id} after retries: {e}"
        )
        raise


# ============================================================
# Fallback to GPT-4o (Optional)
# ============================================================


async def fallback_gpt4o_analysis(raw_signal: RawSignal) -> Insight:
    """
    Fallback to GPT-4o if Claude fails (rate limits, etc.).

    Note: This is a placeholder. Implement if needed for rate limit handling.

    Args:
        raw_signal: The raw signal to analyze

    Returns:
        Insight: Structured insight extracted from the signal
    """
    from openai import AsyncOpenAI

    if not settings.openai_api_key:
        raise ValueError("OpenAI API key not configured for fallback")

    client = AsyncOpenAI(api_key=settings.openai_api_key)

    # Create GPT-4o completion with structured output
    response = await client.chat.completions.create(
        model="gpt-4o",
        messages=[
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": raw_signal.content},
        ],
        response_format={"type": "json_object"},
    )

    # Parse JSON response
    import json

    insight_data = InsightSchema.model_validate_json(
        response.choices[0].message.content
    )

    # Convert to database Insight model
    insight = Insight(
        raw_signal_id=raw_signal.id,
        problem_statement=insight_data.problem_statement,
        proposed_solution=insight_data.proposed_solution,
        market_size_estimate=insight_data.market_size_estimate,
        relevance_score=insight_data.relevance_score,
        competitor_analysis=[
            c.model_dump() for c in insight_data.competitor_analysis
        ],
    )

    logger.info(
        f"Fallback GPT-4o analysis successful for signal {raw_signal.id}"
    )

    return insight
