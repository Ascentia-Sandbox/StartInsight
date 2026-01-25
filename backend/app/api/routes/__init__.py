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
"""

from app.api.routes import (
    admin,
    api_keys,
    build_tools,
    export,
    feed,
    insights,
    payments,
    research,
    signals,
    teams,
    tenants,
    users,
)

__all__ = [
    "signals",
    "insights",
    "users",
    "admin",
    "research",
    "build_tools",
    "export",
    "feed",
    "payments",
    "teams",
    "api_keys",
    "tenants",
]
