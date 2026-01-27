"""AI agents package for PydanticAI-powered analysis.

Phase 1-3: Basic analyzer (analyze_signal)
Phase 4.3: Enhanced 8-dimension scoring (analyze_signal_enhanced)
Phase 5.1: Research agent (analyze_idea)
"""

from app.agents.analyzer import analyze_signal, analyze_signal_with_retry
from app.agents.enhanced_analyzer import (
    analyze_signal_enhanced,
    analyze_signal_enhanced_with_retry,
    calculate_aggregate_score,
    upgrade_insight_scoring,
)
from app.agents.research_agent import (
    RESEARCH_QUOTA_LIMITS,
    analyze_idea,
    analyze_idea_with_retry,
    get_quota_limit,
)

__all__ = [
    # Basic analyzer (Phase 1-3)
    "analyze_signal",
    "analyze_signal_with_retry",
    # Enhanced analyzer (Phase 4.3)
    "analyze_signal_enhanced",
    "analyze_signal_enhanced_with_retry",
    "upgrade_insight_scoring",
    "calculate_aggregate_score",
    # Research agent (Phase 5.1)
    "analyze_idea",
    "analyze_idea_with_retry",
    "get_quota_limit",
    "RESEARCH_QUOTA_LIMITS",
]
