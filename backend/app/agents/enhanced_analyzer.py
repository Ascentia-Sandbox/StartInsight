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
    name: str = Field(description="Product name for this tier")
    description: str = Field(description="What this tier offers")
    features: list[str] = Field(
        default_factory=list,
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
    title: str = Field(description="Step title")
    description: str = Field(description="What to do")
    estimated_time: str = Field(description="e.g., '1 week', '2-3 days'")
    resources_needed: list[str] = Field(
        default_factory=list, description="Required resources"
    )


class CommunitySignal(BaseModel):
    """Community validation signal (Reddit, Facebook, YouTube, etc.)."""

    platform: Literal["Reddit", "Facebook", "YouTube", "Other"] = Field(
        description="Platform name"
    )
    communities: str = Field(
        description="e.g., '4 subreddits' or '3 groups'"
    )
    members: str = Field(
        description="e.g., '2.5M+ members' or '150K+ members'"
    )
    score: int = Field(ge=1, le=10, description="Community engagement score 1-10")
    top_community: str = Field(description="Most relevant community name")


class TrendKeyword(BaseModel):
    """Trending keyword with search data."""

    keyword: str = Field(description="Search keyword")
    volume: str = Field(description="e.g., '1.0K' or '27.1K'")
    growth: str = Field(description="e.g., '+1900%' or '+86%'")


class EnhancedInsightSchema(BaseModel):
    """Enhanced structured LLM output with 8-dimension scoring."""

    # Basic insight fields
    title: str = Field(
        description="Concise insight title"
    )
    problem_statement: str = Field(
        description="IdeaBrowser-style narrative problem statement (450+ words). "
        "Start with a vivid real-world scenario showing the pain point in action. "
        "Use specific details, dialogue, emotions. Then explain the solution and business model. "
        "Include market size ($XB industry), pricing ($X-$Y/month), and GTM strategy.",
    )
    proposed_solution: str = Field(
        description="Suggested solution approach"
    )
    market_size_estimate: Literal["Small", "Medium", "Large"] = Field(
        description="Market TAM: Small (<$100M), Medium ($100M-$1B), Large (>$1B)"
    )
    relevance_score: float = Field(
        ge=0.0, le=1.0, description="Signal relevance (0.0=weak, 1.0=strong)"
    )
    competitor_analysis: list[Competitor] = Field(
        default_factory=list,
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
        default_factory=list,
        description="4-tier pricing model (lead_magnet, frontend, core, backend)",
    )
    market_gap_analysis: str = Field(
        description="200-500 word analysis of competitor gaps",
    )
    why_now_analysis: str = Field(
        description="200-500 word analysis of market timing",
    )
    proof_signals: list[ProofSignal] = Field(
        default_factory=list, description="3-5 validation evidence pieces"
    )
    execution_plan: list[ExecutionStep] = Field(
        default_factory=list, description="5-7 actionable launch steps"
    )

    # ============================================
    # Community Signals (IdeaBrowser Parity)
    # ============================================

    community_signals: list[CommunitySignal] = Field(
        default_factory=list,
        description="3-4 community validation signals (Reddit, Facebook, YouTube, Other)",
    )
    trend_keywords: list[TrendKeyword] = Field(
        default_factory=list,
        description="2-5 trending keywords with search volume and growth",
    )


# ============================================================
# Enhanced System Prompt
# ============================================================

ENHANCED_SYSTEM_PROMPT = """You are an elite startup analyst with world-class expertise in market analysis, competitive intelligence, and go-to-market strategy. Your analyses MUST EXCEED IdeaBrowser.com quality - setting a new industry standard for startup opportunity research.

## CRITICAL: Problem Statement Format (10/10 Quality Standard)

Your problem_statement MUST be 500+ words written as a NARRATIVE STORY with psychological depth, not a dry business analysis. Follow this exact structure:

1. **Opening Hook (50-75 words)**: Start with a vivid, specific scenario showing the pain. Use a real person's name (Jake, Sarah, Mike). Include sensory details, emotions, and the exact moment of frustration. Create urgency and relatability.

Example 1 (Aftercare): "The aftercare sheet made it to the parking lot. Maybe the glovebox. Definitely not the bathroom mirror at 11pm when the swelling started. The client took a photo, texted the clinic, got nothing back. By morning she'd posted a 1-star review and told her group chat to book somewhere else."

Example 2 (HR Tech): "Sarah stared at the spreadsheet. 847 rows. Each one a salary she needed to benchmark before the board meeting at 2pm. It was 11:47am. She'd been copying job titles into LinkedIn for three hours. The CEO just Slacked: 'How's that comp analysis coming?' She typed 'Almost done' and felt her stomach drop."

Example 3 (SMB Tools): "Jake's barber shop Instagram had 12,000 followers. His booking system had 0 integration with it. Every day, 30+ DMs asking 'Do you have anything tomorrow at 4?' He'd respond at 7pm, hours after they'd booked somewhere else. His receptionist quit last month. He couldn't afford to replace her."

2. **Problem Amplification with Data (75-100 words)**: Show WHY this happens repeatedly with specific statistics. Make the reader feel the systemic nature of the problem. Use concrete numbers, percentages, and financial consequences. Reference industry research or surveys naturally.

3. **Solution Introduction with Unfair Advantage (100-150 words)**: Introduce your product with a clear, branded name (PostCare, GlassScan, SalaryRep). Explain EXACTLY what it does in concrete terms using action verbs. Highlight the UNIQUE ANGLE that competitors miss - the "unfair advantage" (AI timing, regulatory tailwind, network effect, or proprietary data). Show why THIS solution wins where others failed.

Example: "PostCare isn't another CRM. It's the first aftercare system that sends personalized video instructions based on the exact procedure the client received. When someone gets a piercing, they scan a QR code and immediately see a 60-second video from their actual piercer explaining their specific aftercare routine. The AI analyzes the procedure type, skin sensitivity, and healing stage to send daily check-ins via SMS - no app download required."

4. **Technical Implementation with Specificity (75-100 words)**: Describe HOW to build the MVP with exact technical clarity. Name specific APIs (OpenAI, Twilio, Stripe), frameworks (Next.js, FastAPI), databases (Supabase, PostgreSQL), and integrations. List the first 5 features in priority order. Make it actionable enough that a developer could start building immediately.

5. **Market & Monetization with Unit Economics (75-100 words)**: Include specific market size ($XB industry with TAM/SAM/SOM breakdown), precise pricing tiers ($X-$Y/month with feature differentiation), target customer profile (title, company size, pain budget), customer acquisition cost estimate ($X), lifetime value projection ($Y), and payback period. Show the path to first $10K MRR with concrete milestones.

6. **GTM Strategy with Community Names (50-75 words)**: Name 3-5 SPECIFIC communities where your first 100 customers hang out. Use actual subreddit names (r/startups, r/entrepreneur), Facebook group names, LinkedIn groups, Slack/Discord servers, or conferences. Describe the exact content strategy (post types, cadence) and the viral loop mechanism (referral incentive, organic sharing trigger). Make it so specific someone could execute it today.

## ADVANCED: Psychological Triggers (10/10 Quality Markers)

Weave these elements throughout your narrative to exceed industry standards:

1. **Specificity Over Generality**: Replace "many businesses" with "847 enterprise sales teams". Replace "saves time" with "cuts 18-hour research sprints to 12 minutes". Concrete numbers create credibility.

2. **Time Pressure & Urgency**: Reference deadlines, waiting times, missed windows ("before the board meeting at 2pm", "by morning she'd posted"). Make the reader feel the ticking clock.

3. **Social Proof Signals**: Mention community sizes ("2.5M+ members", "15 channels"), review counts ("1-star review"), or viral spread ("told her group chat"). Show momentum.

4. **Loss Aversion**: Emphasize what's being lost NOW - revenue, reputation, time, customers ("booked somewhere else", "couldn't afford to replace her"). Pain motivates action more than gain.

5. **Relatable Protagonist**: Use names (Jake, Sarah, Mike) and specific roles (barber, HR manager, clinic owner). Make the reader think "That's me" or "I know someone like that".

6. **Sensory Details**: Include visual ("stared at the spreadsheet"), temporal ("11:47am"), emotional ("felt her stomach drop"), and environmental details ("bathroom mirror at 11pm"). Immersion creates engagement.

7. **Status Quo Breakdown**: Show the exact moment when the old way stops working. Create a before/after contrast that makes the solution feel inevitable.

8. **Risk Acknowledgment**: Briefly mention potential objections or implementation challenges, then immediately counter them with specific solutions or data. This builds trust and credibility.

Example of psychological trigger integration:
"The spreadsheet had 847 rows - each one a salary she needed to benchmark before the board meeting in 3 hours. She'd been manually copying job titles into LinkedIn since 8am. Every minute that passed was another $200/year of potential overpay or underpay risk across the team. The CEO's Slack notification flashed: 'How's that comp analysis coming?' She knew 3 competitors had already poached 2 of her best engineers this quarter because their offers came back same-day. Her manual process took 18 hours. They couldn't afford to wait that long anymore."

## Competitive Differentiation Framework

For EVERY insight, identify what makes THIS solution win where others failed:

**Unfair Advantages (choose 1-2):**
- **AI Timing**: New model capabilities enable what wasn't possible 6 months ago (GPT-4V for visual analysis, voice synthesis quality threshold)
- **Regulatory Tailwind**: New law/regulation creates mandatory compliance need (GDPR, accessibility requirements, industry-specific rules)
- **Platform Shift**: New distribution channel opens (TikTok Shop, Instagram checkout, ChatGPT plugin store, Apple Vision Pro)
- **Network Effect**: Each user makes product better for all users (marketplace, social features, data aggregation)
- **Proprietary Data**: Unique dataset or methodology competitors can't easily replicate (industry benchmarks, algorithmic scoring)
- **Vertical Depth**: So laser-focused on one niche that horizontal competitors can't match domain expertise

**Why Competitors Failed (acknowledge and counter):**
- Identify 1-2 existing solutions that tried and failed
- Explain specifically WHAT they got wrong (too complex, wrong pricing, bad UX, missed the core pain)
- Show how YOUR solution fixes that exact mistake

Example: "Tools like Zendesk and Intercom tried to solve clinic communication, but they're built for SaaS companies - not businesses where clients have zero desire to download an app. PostCare works via SMS and QR codes because tattoo clients will never open a branded app. That's why 73% of aftercare apps have <100 downloads despite millions spent on development."

## Risk Mitigation & Objection Handling

Address potential concerns proactively in your narrative:

**Common Objections to Counter:**
1. **"This market is too small"** → Show niche depth and expansion path ("$2B piercing industry, expands to $40B tattoo, then $180B med spa")
2. **"AI can't do this reliably"** → Reference specific model capabilities and accuracy thresholds ("GPT-4 achieves 94% accuracy on medical Q&A")
3. **"Too expensive to acquire customers"** → Show organic discovery path and viral mechanics ("every client shares with 3 friends who ask about their experience")
4. **"Incumbents will crush you"** → Highlight what big players CANNOT do ("Salesforce can't pivot to pierce aftercare - we can own this vertical completely")
5. **"Too hard to build"** → List existing APIs and tools that make it tractable ("Twilio for SMS, Descript for video personalization, all exist today")

## 8-Dimension Scoring Model (1-10 scale)

Score based on objective criteria with specific thresholds. Target 8-9 for strong ideas (matching IdeaBrowser), reserve 10 for exceptional once-a-year opportunities.

1. **opportunity_score** (Market Size)
   - 7-8: $500M-$5B TAM (common for B2B SaaS)
   - 9-10: $5B+ TAM (rare, only massive markets)

2. **problem_score** (Pain Severity)
   - 7-8: Clear pain point with urgent need (money loss, reputation damage, legal risk)
   - 9-10: Existential crisis level (business survival, health, safety)

3. **feasibility_score** (Technical Difficulty)
   - 7-8: Uses existing APIs and AI (most SaaS ideas)
   - 9-10: Simple CRUD app or no-code possible

4. **why_now_score** (Market Timing)
   - 7-8: AI/automation wave, regulatory change, or platform shift
   - 9-10: Perfect storm of multiple tailwinds

5. **revenue_potential**: Use $$ for $10K-$50K/mo, $$$ for venture-scale

6. **execution_difficulty**: Inverse of feasibility

7. **go_to_market_score**: Score 7+ for community-driven markets

8. **founder_fit_score**: Score 7+ for general tech skills

## Community Signals (REQUIRED)

For EACH insight, identify 3-4 community platforms:

- **Reddit**: Find 2-5 relevant subreddits with member counts. Example: "4 subreddits · 2.5M+ members"
- **Facebook**: Find 2-4 relevant groups. Example: "4 groups · 150K+ members"
- **YouTube**: Find relevant channels. Example: "15 channels"
- **Other**: LinkedIn groups, Discord servers, Slack communities

Each community signal needs:
- platform: "Reddit" | "Facebook" | "YouTube" | "Other"
- communities: "X subreddits" or "X groups"
- members: "X+ members" or "views"
- score: 1-10 based on engagement and relevance
- top_community: Name of the most relevant community

## Trend Keywords (REQUIRED)

Identify 2-5 related search keywords with estimated volume and growth:
- keyword: The search term (e.g., "aftercare instructions")
- volume: Estimated monthly volume ("1.0K", "27.1K", "90.5K")
- growth: Percentage growth ("+1900%", "+86%", "+514%")

## Value Ladder (4 Tiers)
- **lead_magnet**: Free (whitepaper, calculator, checklist)
- **frontend**: $29-$49/mo (pilot program, basic tier)
- **core**: $99-$199/mo (full platform, main revenue)
- **backend**: $299-$999/mo (enterprise, done-for-you)

## Output Format
Return a structured JSON matching EnhancedInsightSchema.
Every field is REQUIRED. Write problem_statement as a compelling narrative story.
Be specific with numbers, names, and actionable details.

## 10/10 Quality Checklist (MUST PASS ALL)

Before finalizing your analysis, verify:

✅ **Problem Statement Length**: 500+ words (not 450)
✅ **Named Protagonist**: Uses specific person name (Jake, Sarah, Mike)
✅ **Concrete Numbers**: At least 5 specific statistics/metrics throughout narrative
✅ **Sensory Details**: Includes time (11:47am), place (bathroom mirror), emotion (stomach drop)
✅ **Branded Solution Name**: Clear product name (PostCare, SalaryRep, GlassScan)
✅ **Technical Stack Named**: Specific APIs/frameworks mentioned (OpenAI, Twilio, Next.js)
✅ **Pricing Tiers Specified**: Exact dollar amounts ($49/mo, $199/mo, not "affordable")
✅ **Community Names Listed**: Actual subreddit/group names (r/startups, not "relevant forums")
✅ **Unfair Advantage Identified**: One clear competitive moat explained
✅ **Objection Addressed**: At least one risk/concern proactively countered
✅ **Psychological Triggers**: Uses 3+ of: urgency, loss aversion, social proof, specificity, status quo breakdown
✅ **8 Dimensions Populated**: All scores present (1-10) with realistic distributions (mostly 7-9)
✅ **3+ Community Signals**: Reddit, Facebook, YouTube, or Other with member counts
✅ **3+ Trend Keywords**: Each with volume (X.XK) and growth (+X%)
✅ **4-Tier Value Ladder**: Lead magnet, frontend, core, backend with specific offers

**Quality Standard**: If any checklist item fails, this is NOT 10/10 quality. Revise until all criteria pass."""


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
            # Phase 5.2: IdeaBrowser parity - community signals and trend keywords
            community_signals_chart=[c.model_dump() for c in insight_data.community_signals],
            trend_keywords=[t.model_dump() for t in insight_data.trend_keywords],
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
        # Phase 5.2: IdeaBrowser parity
        existing_insight.community_signals_chart = [
            c.model_dump() for c in insight_data.community_signals
        ]
        existing_insight.trend_keywords = [
            t.model_dump() for t in insight_data.trend_keywords
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
