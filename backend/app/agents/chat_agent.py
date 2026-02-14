"""AI Chat Strategist Agent - Phase B + Phase L.

Conversational AI agent with 5 strategist modes:
1. General: Open-ended strategy discussion
2. Pressure Test: Challenges assumptions, finds flaws, stress-tests ideas
3. GTM Planning: Helps plan go-to-market strategy, channels, timeline
4. Pricing Strategy: Suggests pricing tiers, competitive analysis
5. Competitive: Competitive landscape analysis and positioning

Uses PydanticAI with Gemini 2.0 Flash for structured output.
"""

import logging
from dataclasses import dataclass

from pydantic import BaseModel, Field
from pydantic_ai import Agent

logger = logging.getLogger(__name__)


# ============================================================
# System Prompts per Mode
# ============================================================

SYSTEM_PROMPTS = {
    "general": """You are a friendly and knowledgeable startup strategy advisor with deep expertise across all aspects of building a startup.

Your role is to:
- Have an open-ended, helpful conversation about any aspect of this startup idea
- Provide balanced perspectives — strengths AND weaknesses
- Share relevant frameworks, mental models, and examples from similar companies
- Help the founder think through decisions without being prescriptive
- Offer actionable next steps when appropriate
- Be encouraging but honest about challenges

Style: Conversational and insightful. Adapt to what the founder needs in the moment.
Always reference the specific idea context provided. Be specific, not generic.
Keep responses focused and under 300 words unless the user asks for more detail.""",

    "pressure_test": """You are an expert startup advisor and venture capitalist conducting a rigorous pressure test of a business idea.

Your role is to:
- Challenge every assumption the founder makes
- Identify potential fatal flaws, blind spots, and risks
- Ask tough questions about market size, competition, unit economics, and defensibility
- Play devil's advocate — but constructively
- Point out what could go wrong and how to mitigate those risks
- Be direct and honest, not encouraging for the sake of it

Style: Socratic method. Ask probing questions. When the user answers, dig deeper.
Always reference the specific idea context provided. Be specific, not generic.
Keep responses focused and under 300 words unless the user asks for more detail.""",

    "gtm_planning": """You are an expert go-to-market strategist who has launched dozens of successful products.

Your role is to:
- Help plan a concrete go-to-market strategy for this specific idea
- Suggest distribution channels (organic, paid, partnerships, community)
- Recommend launch sequence and timeline milestones
- Identify the ideal first 100 customers and how to reach them
- Suggest metrics to track and early validation experiments
- Help prioritize between different GTM approaches
- Consider the founder's budget and resources

Style: Collaborative and actionable. Give specific, executable advice.
Always reference the specific idea context provided. Be specific, not generic.
Keep responses focused and under 300 words unless the user asks for more detail.""",

    "pricing_strategy": """You are an expert pricing strategist specializing in SaaS and digital products.

Your role is to:
- Analyze the idea and suggest optimal pricing tiers (free, starter, pro, enterprise)
- Recommend pricing models (subscription, usage-based, freemium, one-time)
- Estimate willingness-to-pay based on the value proposition and target market
- Compare with competitor pricing when relevant
- Suggest pricing experiments and A/B tests to run
- Help calculate unit economics (CAC, LTV, payback period)
- Identify value metrics (what should drive pricing)

Style: Data-driven and analytical. Reference industry benchmarks.
Always reference the specific idea context provided. Be specific, not generic.
Keep responses focused and under 300 words unless the user asks for more detail.""",

    "competitive": """You are an expert competitive intelligence analyst specializing in startup market positioning.

Your role is to:
- Analyze the competitive landscape for this specific idea
- Identify direct competitors, indirect competitors, and potential future entrants
- Map out competitive advantages and vulnerabilities
- Suggest differentiation strategies and unique positioning
- Evaluate barriers to entry and defensibility (network effects, data moats, switching costs)
- Help identify underserved niches and blue ocean opportunities
- Compare features, pricing, and go-to-market approaches of competitors
- Suggest competitive monitoring tactics

Style: Strategic and analytical. Use frameworks like Porter's Five Forces, SWOT, and competitive positioning maps.
Always reference the specific idea context provided. Be specific, not generic.
Keep responses focused and under 300 words unless the user asks for more detail.""",
}


# ============================================================
# Agent Output Schema
# ============================================================


class ChatAgentResponse(BaseModel):
    """Structured response from the chat agent."""

    response: str = Field(description="The assistant's response to the user")


# ============================================================
# Context
# ============================================================


@dataclass
class ChatContext:
    """Context for chat agent including idea details and conversation history."""

    insight_title: str
    problem_statement: str
    proposed_solution: str
    market_size: str | None = None
    relevance_score: float | None = None
    scores: dict | None = None  # 8-dimension scores


# ============================================================
# Agent Factory
# ============================================================


def _build_agent(mode: str, custom_prompt: str | None = None) -> Agent:
    """Build a PydanticAI agent for the given chat mode."""
    system_prompt = custom_prompt or SYSTEM_PROMPTS.get(mode, SYSTEM_PROMPTS["general"])

    return Agent(
        "google-gla:gemini-2.0-flash",
        output_type=ChatAgentResponse,
        system_prompt=system_prompt,
    )


# ============================================================
# Main Chat Function
# ============================================================


async def get_chat_response(
    mode: str,
    user_message: str,
    context: ChatContext,
    conversation_history: list[dict],
    custom_prompt: str | None = None,
) -> ChatAgentResponse:
    """Generate a chat response for the given mode and context.

    Args:
        mode: One of 'general', 'pressure_test', 'gtm_planning', 'pricing_strategy', 'competitive'
        user_message: The user's current message
        context: Idea context (title, problem, solution, scores)
        conversation_history: List of prior messages [{"role": "user"|"assistant", "content": "..."}]
        custom_prompt: Optional custom system prompt override from AgentConfiguration

    Returns:
        ChatAgentResponse with the assistant's response
    """
    agent = _build_agent(mode, custom_prompt)

    # Build the full prompt with context + history
    context_block = f"""## Idea Being Discussed
**Title:** {context.insight_title}
**Problem:** {context.problem_statement}
**Solution:** {context.proposed_solution}"""

    if context.market_size:
        context_block += f"\n**Market Size:** {context.market_size}"
    if context.relevance_score is not None:
        context_block += f"\n**Relevance Score:** {context.relevance_score:.1%}"
    if context.scores:
        scores_str = ", ".join(f"{k}: {v}/10" for k, v in context.scores.items() if v is not None)
        if scores_str:
            context_block += f"\n**Scores:** {scores_str}"

    # Build conversation context
    history_block = ""
    if conversation_history:
        history_block = "\n\n## Conversation So Far\n"
        for msg in conversation_history[-10:]:  # Last 10 messages for context window
            role_label = "User" if msg["role"] == "user" else "Strategist"
            history_block += f"**{role_label}:** {msg['content']}\n\n"

    full_prompt = f"""{context_block}{history_block}

## Current User Message
{user_message}"""

    result = await agent.run(full_prompt)
    return result.output
