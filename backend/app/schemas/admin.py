"""Pydantic schemas for Admin API - Phase 4.2 admin portal.

See architecture.md Section "Admin Portal Architecture" for full specification.
"""

from datetime import datetime
from enum import Enum
from uuid import UUID

from pydantic import BaseModel, Field

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
    metadata: dict = Field(default_factory=dict)

    class Config:
        from_attributes = True


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

    class Config:
        from_attributes = True


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


class InsightAdminUpdate(BaseModel):
    """Admin update for insight moderation."""

    admin_status: str | None = Field(
        None, pattern="^(approved|rejected|pending)$", description="Admin approval status"
    )
    admin_notes: str | None = Field(None, max_length=1000)
    admin_override_score: float | None = Field(None, ge=0.0, le=1.0)


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


class AdminUserResponse(BaseModel):
    """Admin user response."""

    id: UUID
    user_id: UUID
    role: str
    permissions: dict = Field(default_factory=dict)
    created_at: datetime
    user_email: str | None = None

    class Config:
        from_attributes = True


class AdminUserListResponse(BaseModel):
    """List of admin users."""

    items: list[AdminUserResponse]
    total: int
