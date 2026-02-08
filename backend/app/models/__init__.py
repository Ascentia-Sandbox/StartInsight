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
Phase 8.1: ContentReviewQueue, ContentSimilarity (content quality management)
Phase 8.2: PipelineHealthCheck, APIQuotaUsage, AdminAlert, AdminAlertIncident (pipeline monitoring)
Phase 8.3: UserActivityEvent, UserSession (user analytics)
Phase 8.4-8.5: AgentConfiguration, AuditLog (agent control & security)
Phase 9.1: UserPreferences, EmailPreferences, EmailSend (user preferences & email)
Phase 9.2: IdeaChat, IdeaChatMessage (AI idea chat), CompetitorProfile, CompetitorSnapshot
Phase 9.3: IdeaVote, IdeaComment, CommentUpvote, IdeaPoll, PollResponse (community)
Phase 9.5: FounderProfile, FounderConnection, IdeaClub, ClubMember, ClubPost (social)
Phase 9.6: Achievement, UserAchievement, UserPoints, UserCredits, CreditTransaction (gamification)
Phase 12.2: Tool, SuccessStory, Trend, MarketInsight (IdeaBrowser public content)
"""

from app.models.admin_user import AdminUser
from app.models.agent_execution_log import AgentExecutionLog
from app.models.api_key import APIKey, APIKeyUsageLog
from app.models.competitor_profile import CompetitorProfile, CompetitorSnapshot
from app.models.content_review import ContentReviewQueue, ContentSimilarity
from app.models.pipeline_monitoring import AdminAlert, AdminAlertIncident, APIQuotaUsage, PipelineHealthCheck
from app.models.user_analytics import UserActivityEvent, UserSession
from app.models.agent_control import AgentConfiguration, AuditLog
from app.models.custom_analysis import CustomAnalysis
from app.models.insight import Insight
from app.models.insight_interaction import InsightInteraction
from app.models.market_insight import MarketInsight
from app.models.raw_signal import RawSignal
from app.models.research_request import ResearchRequest
from app.models.saved_insight import SavedInsight
from app.models.subscription import PaymentHistory, Subscription
from app.models.success_story import SuccessStory
from app.models.system_metric import SystemMetric
from app.models.team import SharedInsight, Team, TeamInvitation, TeamMember
from app.models.tenant import Tenant, TenantUser
from app.models.tool import Tool
from app.models.trend import Trend
from app.models.user import User
from app.models.user_rating import UserRating
from app.models.webhook_event import WebhookEvent
# Phase 9.1: User Preferences
from app.models.user_preferences import UserPreferences, EmailPreferences, EmailSend
# Phase 9.2: Idea Chat
from app.models.idea_chat import IdeaChat, IdeaChatMessage
# Phase 9.3: Community
from app.models.community import IdeaVote, IdeaComment, CommentUpvote, IdeaPoll, PollResponse
# Phase 9.5: Social
from app.models.social import FounderProfile, FounderConnection, IdeaClub, ClubMember, ClubPost
# Phase 9.6: Gamification
from app.models.gamification import Achievement, UserAchievement, UserPoints, UserCredits, CreditTransaction
# Phase 10: Integrations
from app.models.integrations import ExternalIntegration, IntegrationWebhook, IntegrationSync, BrowserExtensionToken, BotSubscription

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
    # Phase 8.1: Content Quality Management
    "ContentReviewQueue",
    "ContentSimilarity",
    # Phase 8.2: Pipeline Monitoring
    "PipelineHealthCheck",
    "APIQuotaUsage",
    "AdminAlert",
    "AdminAlertIncident",
    # Phase 8.3: User Analytics
    "UserActivityEvent",
    "UserSession",
    # Phase 8.4-8.5: Agent Control & Security
    "AgentConfiguration",
    "AuditLog",
    # Phase 9.1: User Preferences & Email
    "UserPreferences",
    "EmailPreferences",
    "EmailSend",
    # Phase 9.2: Idea Chat & Competitive Intelligence
    "IdeaChat",
    "IdeaChatMessage",
    "CompetitorProfile",
    "CompetitorSnapshot",
    # Phase 9.3: Community
    "IdeaVote",
    "IdeaComment",
    "CommentUpvote",
    "IdeaPoll",
    "PollResponse",
    # Phase 9.5: Social
    "FounderProfile",
    "FounderConnection",
    "IdeaClub",
    "ClubMember",
    "ClubPost",
    # Phase 9.6: Gamification
    "Achievement",
    "UserAchievement",
    "UserPoints",
    "UserCredits",
    "CreditTransaction",
    # Phase 10: Integrations
    "ExternalIntegration",
    "IntegrationWebhook",
    "IntegrationSync",
    "BrowserExtensionToken",
    "BotSubscription",
    # Phase 12.2: Public Content (IdeaBrowser Replication)
    "Tool",
    "SuccessStory",
    "Trend",
    "MarketInsight",
]
