"""API routes package.

Phase 1-3: signals, insights
Phase 4.1: users (authentication & workspace)
Phase 4.2: admin (admin portal)
Phase 5.1: research (AI research agent)
Phase 5.2: build_tools (brand packages, landing pages)
Phase 5.3: export (PDF, CSV, JSON exports)
Phase 5.4: feed (real-time insight updates)
Phase 6.1: payments (Stripe subscription management)
Phase 6.4: teams (team collaboration)
Phase 7.2: api_keys (public API key management)
Phase 7.3: tenants (multi-tenancy & white-label)
Phase 8.1: content_review (content quality management)
Phase 8.2: pipeline (pipeline monitoring & alerts)
Phase 8.3: analytics (user & revenue intelligence)
Phase 8.4-8.5: agent_control (AI agent control & security audit)
Phase 9.1: preferences (user preferences & email settings)
Phase 9.3: build (builder integrations), community (voting & comments)
Phase 9.6: gamification (achievements, points, credits)
Phase 10: integrations (external services, browser extension, bots)
Phase 12.3: tools, success_stories, trends, market_insights (public content)
"""

from app.api.routes import (
    admin,
    agent_control,
    analytics,
    api_keys,
    build,
    build_tools,
    community,
    content_review,
    export,
    gamification,
    integrations,
    pipeline,
    feed,
    insights,
    market_insights,
    payments,
    preferences,
    research,
    signals,
    success_stories,
    teams,
    tenants,
    tools,
    trends,
    users,
)

__all__ = [
    "signals",
    "insights",
    "users",
    "admin",
    "agent_control",
    "analytics",
    "research",
    "build_tools",
    "community",
    "content_review",
    "export",
    "gamification",
    "integrations",
    "pipeline",
    "feed",
    "payments",
    "preferences",
    "teams",
    "api_keys",
    "tenants",
    "build",
    "tools",
    "success_stories",
    "trends",
    "market_insights",
]
