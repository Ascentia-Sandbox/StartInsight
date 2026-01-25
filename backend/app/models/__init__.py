"""Database models package.

Phase 1-3: RawSignal, Insight (v0.1)
Phase 4.1: User, SavedInsight, UserRating (authentication & workspace)
Phase 4.2: AdminUser, AgentExecutionLog, SystemMetric (admin portal)
Phase 4.4: InsightInteraction (analytics tracking)
Phase 5.1: CustomAnalysis (AI research agent)
Phase 5.2: ResearchRequest (admin approval queue for research)
Phase 5.2-5.4: Build tools, export, and real-time feed
Phase 6.1: Subscription, PaymentHistory, WebhookEvent (Stripe payments)
Phase 6.4: Team, TeamMember, TeamInvitation, SharedInsight (collaboration)
Phase 7.2: APIKey, APIKeyUsageLog (public API)
Phase 7.3: Tenant, TenantUser (multi-tenancy)
"""

from app.models.insight import Insight
from app.models.raw_signal import RawSignal
from app.models.user import User
from app.models.saved_insight import SavedInsight
from app.models.user_rating import UserRating
from app.models.admin_user import AdminUser
from app.models.agent_execution_log import AgentExecutionLog
from app.models.system_metric import SystemMetric
from app.models.insight_interaction import InsightInteraction
from app.models.custom_analysis import CustomAnalysis
from app.models.research_request import ResearchRequest
from app.models.subscription import PaymentHistory, Subscription
from app.models.webhook_event import WebhookEvent
from app.models.team import SharedInsight, Team, TeamInvitation, TeamMember
from app.models.api_key import APIKey, APIKeyUsageLog
from app.models.tenant import Tenant, TenantUser

__all__ = [
    # Phase 1-3
    "RawSignal",
    "Insight",
    # Phase 4.1
    "User",
    "SavedInsight",
    "UserRating",
    # Phase 4.2
    "AdminUser",
    "AgentExecutionLog",
    "SystemMetric",
    # Phase 4.4
    "InsightInteraction",
    # Phase 5.1
    "CustomAnalysis",
    # Phase 5.2
    "ResearchRequest",
    # Phase 6.1: Payments
    "Subscription",
    "PaymentHistory",
    "WebhookEvent",
    # Phase 6.4: Teams
    "Team",
    "TeamMember",
    "TeamInvitation",
    "SharedInsight",
    # Phase 7.2: Public API
    "APIKey",
    "APIKeyUsageLog",
    # Phase 7.3: Multi-tenancy
    "Tenant",
    "TenantUser",
]
