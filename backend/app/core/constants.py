"""Application constants and enums - Code simplification Phase 4.

Centralized constants to replace magic strings and hardcoded values across the codebase.
Single source of truth for analysis types, insight statuses, and user roles.
"""

from enum import Enum


class AnalysisType(str, Enum):
    """Types of research analysis supported."""

    IDEA_VALIDATION = "idea_validation"
    MARKET_RESEARCH = "market_research"
    COMPETITOR_ANALYSIS = "competitor_analysis"


class InsightStatus(str, Enum):
    """Admin status for insights."""

    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"


class AnalysisStatus(str, Enum):
    """Status for custom analysis requests."""

    PENDING = "pending"
    PROCESSING = "processing"
    COMPLETED = "completed"
    FAILED = "failed"


class UserRole(str, Enum):
    """User roles for admin access control."""

    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


class SubscriptionTier(str, Enum):
    """Subscription tiers for user accounts."""

    FREE = "free"
    STARTER = "starter"
    PRO = "pro"
    ENTERPRISE = "enterprise"


class SavedInsightStatus(str, Enum):
    """Status for saved insights in user workspace."""

    SAVED = "saved"
    INTERESTED = "interested"
    BUILDING = "building"
    NOT_INTERESTED = "not_interested"


# Analysis quota limits by subscription tier
ANALYSIS_QUOTA: dict[str, int] = {
    SubscriptionTier.FREE: 1,
    SubscriptionTier.STARTER: 3,
    SubscriptionTier.PRO: 10,
    SubscriptionTier.ENTERPRISE: 100,
}

# Rate limits by subscription tier (requests per hour)
RATE_LIMITS: dict[str, dict[str, int]] = {
    SubscriptionTier.FREE: {
        "requests_per_minute": 20,
        "requests_per_hour": 200,
        "analyses_per_hour": 1,
    },
    SubscriptionTier.STARTER: {
        "requests_per_minute": 60,
        "requests_per_hour": 1000,
        "analyses_per_hour": 2,
    },
    SubscriptionTier.PRO: {
        "requests_per_minute": 200,
        "requests_per_hour": 5000,
        "analyses_per_hour": 5,
    },
    SubscriptionTier.ENTERPRISE: {
        "requests_per_minute": 1000,
        "requests_per_hour": 50000,
        "analyses_per_hour": 999999,  # Effectively unlimited
    },
}
