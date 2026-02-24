"""Pydantic schemas for Admin API - Phase 4.2 admin portal.

See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field

# ============================================
# Enums
# ============================================


class AgentType(str, Enum):
    """Valid agent types."""

    REDDIT_SCRAPER = "reddit_scraper"
    PRODUCT_HUNT_SCRAPER = "product_hunt_scraper"
    TRENDS_SCRAPER = "trends_scraper"
    ANALYZER = "analyzer"


class AgentState(str, Enum):
    """Agent execution states."""

    RUNNING = "running"
    PAUSED = "paused"
    TRIGGERED = "triggered"


class ExecutionStatus(str, Enum):
    """Execution log status values."""

    RUNNING = "running"
    COMPLETED = "completed"
    FAILED = "failed"
    SKIPPED = "skipped"


class AdminRole(str, Enum):
    """Admin user roles."""

    SUPERADMIN = "superadmin"
    ADMIN = "admin"
    MODERATOR = "moderator"
    VIEWER = "viewer"


# ============================================
# Agent Status Schemas
# ============================================


class AgentStatusResponse(BaseModel):
    """Single agent status."""

    agent_type: str
    state: AgentState = AgentState.RUNNING
    last_run: datetime | None = None
    last_status: ExecutionStatus | None = None
    items_processed_today: int = 0
    errors_today: int = 0


class AgentControlRequest(BaseModel):
    """Request for agent control actions."""

    agent_type: AgentType


class AgentControlResponse(BaseModel):
    """Response for agent control actions."""

    status: str
    agent_type: str
    triggered_by: str | None = None
    job_id: str | None = None
    timestamp: datetime


# ============================================
# Execution Log Schemas
# ============================================


class ExecutionLogResponse(BaseModel):
    """Execution log entry response."""

    id: UUID
    agent_type: str
    source: str | None = None
    status: str
    started_at: datetime
    completed_at: datetime | None = None
    duration_ms: int | None = None
    items_processed: int = 0
    items_failed: int = 0
    error_message: str | None = None
    metadata: dict = Field(default_factory=dict, validation_alias="extra_metadata")

    model_config = ConfigDict(from_attributes=True, populate_by_name=True)


class ExecutionLogListResponse(BaseModel):
    """Paginated execution logs."""

    items: list[ExecutionLogResponse]
    total: int
    limit: int
    offset: int


# ============================================
# System Metric Schemas
# ============================================


class MetricResponse(BaseModel):
    """Single metric entry."""

    id: UUID
    metric_type: str
    metric_value: float
    dimensions: dict = Field(default_factory=dict)
    recorded_at: datetime

    model_config = ConfigDict(from_attributes=True)


class MetricQueryRequest(BaseModel):
    """Request for querying metrics."""

    metric_type: str | None = None
    start_date: datetime | None = None
    end_date: datetime | None = None
    dimensions: dict | None = None
    limit: int = Field(default=100, ge=1, le=1000)


class MetricSummaryResponse(BaseModel):
    """Aggregated metric summary."""

    metric_type: str
    count: int
    total: float
    average: float
    min_value: float
    max_value: float
    period_start: datetime
    period_end: datetime


# ============================================
# Dashboard Schemas
# ============================================


class DashboardMetricsResponse(BaseModel):
    """Real-time dashboard metrics."""

    agent_states: dict[str, str] = Field(
        description="Agent states: {reddit_scraper: running, ...}"
    )
    recent_logs: list[ExecutionLogResponse] = Field(
        default_factory=list, description="Last 10 execution logs"
    )
    llm_cost_today: float = Field(default=0.0, description="LLM cost in USD today")
    pending_insights: int = Field(
        default=0, description="Insights pending admin review"
    )
    total_insights_today: int = Field(
        default=0, description="Total insights generated today"
    )
    errors_today: int = Field(default=0, description="Total errors today")
    timestamp: datetime


class SSEMessage(BaseModel):
    """Server-Sent Event message format."""

    event: str = "metrics_update"
    data: dict
    retry: int = 5000


# ============================================
# Insight Management Schemas
# ============================================


class InsightAdminCreate(BaseModel):
    """Admin create schema for manually adding insights (Phase A1)."""

    title: str = Field(..., max_length=200)
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str = Field(..., max_length=20)
    relevance_score: float = Field(0.8, ge=0.0, le=1.0)
    admin_status: str = Field("approved", pattern="^(approved|rejected|pending)$")

    # 8-dimension scores (1-10)
    opportunity_score: int | None = Field(None, ge=1, le=10)
    problem_score: int | None = Field(None, ge=1, le=10)
    feasibility_score: int | None = Field(None, ge=1, le=10)
    why_now_score: int | None = Field(None, ge=1, le=10)
    execution_difficulty: int | None = Field(None, ge=1, le=10)
    go_to_market_score: int | None = Field(None, ge=1, le=10)
    founder_fit_score: int | None = Field(None, ge=1, le=10)

    revenue_potential: str | None = Field(
        None, pattern=r"^\${1,4}$", description="$, $$, $$$, or $$$$"
    )
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None


class InsightAdminUpdate(BaseModel):
    """Admin update for insight moderation and full editing (Phase 15.1)."""

    # Moderation fields
    admin_status: str | None = Field(
        None, pattern="^(approved|rejected|pending)$", description="Admin approval status"
    )
    admin_notes: str | None = Field(None, max_length=1000)
    admin_override_score: float | None = Field(None, ge=0.0, le=1.0)

    # Core content fields
    title: str | None = Field(None, max_length=200)
    problem_statement: str | None = None
    proposed_solution: str | None = None
    market_size_estimate: str | None = Field(None, max_length=20)

    # 8-dimension scores (1-10)
    opportunity_score: int | None = Field(None, ge=1, le=10)
    problem_score: int | None = Field(None, ge=1, le=10)
    feasibility_score: int | None = Field(None, ge=1, le=10)
    why_now_score: int | None = Field(None, ge=1, le=10)
    execution_difficulty: int | None = Field(None, ge=1, le=10)
    go_to_market_score: int | None = Field(None, ge=1, le=10)
    founder_fit_score: int | None = Field(None, ge=1, le=10)

    # Business metrics
    revenue_potential: str | None = Field(
        None, pattern=r"^\${1,4}$", description="$, $$, $$$, or $$$$"
    )

    # Analysis text
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None

    # JSONB fields (AI generates these as lists or dicts)
    value_ladder: list | dict | None = None
    proof_signals: list | dict | None = None
    execution_plan: list | dict | None = None
    competitor_analysis: list | dict | None = None


class InsightAdminResponse(BaseModel):
    """Full insight response for admin view (Phase 15.1)."""

    id: UUID
    title: str | None = None
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float
    admin_status: str | None = "approved"
    admin_notes: str | None = None
    admin_override_score: float | None = None
    source: str
    created_at: datetime
    edited_at: datetime | None = None

    # 8-dimension scores
    opportunity_score: int | None = None
    problem_score: int | None = None
    feasibility_score: int | None = None
    why_now_score: int | None = None
    execution_difficulty: int | None = None
    go_to_market_score: int | None = None
    founder_fit_score: int | None = None
    revenue_potential: str | None = None

    # Analysis
    market_gap_analysis: str | None = None
    why_now_analysis: str | None = None

    # JSONB (AI generates these as lists or dicts depending on prompt)
    value_ladder: list | dict | None = None
    proof_signals: list | dict | None = None
    execution_plan: list | dict | None = None
    competitor_analysis: list | dict | None = None

    model_config = ConfigDict(from_attributes=True)


class InsightReviewResponse(BaseModel):
    """Insight in admin review queue."""

    id: UUID
    problem_statement: str
    proposed_solution: str
    relevance_score: float
    admin_status: str = "pending"
    admin_notes: str | None = None
    source: str
    created_at: datetime


class InsightAdminListResponse(BaseModel):
    """Paginated admin insights list (Phase 15.1)."""

    items: list[InsightAdminResponse]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int


class ReviewQueueResponse(BaseModel):
    """Paginated review queue."""

    items: list[InsightReviewResponse]
    total: int
    pending_count: int
    approved_count: int
    rejected_count: int


# ============================================
# Error Tracking Schemas
# ============================================


class ErrorEntry(BaseModel):
    """Single error entry."""

    id: UUID
    error_type: str
    source: str | None = None
    message: str | None = None
    occurred_at: datetime


class ErrorSummaryResponse(BaseModel):
    """Error summary for admin dashboard."""

    total_errors_today: int
    errors_by_type: dict[str, int] = Field(default_factory=dict)
    errors_by_source: dict[str, int] = Field(default_factory=dict)
    recent_errors: list[ErrorEntry] = Field(default_factory=list)


# ============================================
# Admin User Schemas
# ============================================


class AdminUserCreate(BaseModel):
    """Create admin user."""

    user_id: UUID
    role: AdminRole


class AdminUserPromoteRequest(BaseModel):
    """Promote a user to admin by email."""

    email: str = Field(..., description="Email of the user to promote")
    role: AdminRole = Field(AdminRole.ADMIN, description="Admin role to assign")


class AdminUserUpdateRequest(BaseModel):
    """Update admin user role."""

    role: AdminRole = Field(..., description="New admin role")


class AdminUserResponse(BaseModel):
    """Admin user response."""

    id: UUID
    user_id: UUID
    role: str
    permissions: dict = Field(default_factory=dict)
    created_at: datetime
    user_email: str | None = None
    user_display_name: str | None = None

    model_config = ConfigDict(from_attributes=True)


class AdminUserListResponse(BaseModel):
    """List of admin users."""

    items: list[AdminUserResponse]
    total: int
