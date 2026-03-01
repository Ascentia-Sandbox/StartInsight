"""Pydantic schemas for User API - Phase 4.1 authentication and workspace.

See architecture.md Section "API Architecture Phase 4+" for full specification.
"""

from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, ConfigDict, EmailStr, Field

# ============================================
# User Profile Schemas
# ============================================


class UserBase(BaseModel):
    """Base user fields."""

    email: EmailStr
    display_name: str | None = None
    avatar_url: str | None = None


class UserCreate(UserBase):
    """Schema for creating a user (internal use only)."""

    supabase_user_id: str


class UserUpdate(BaseModel):
    """Schema for updating user profile."""

    display_name: str | None = Field(None, max_length=255)
    avatar_url: str | None = None
    preferences: dict | None = None


class UserResponse(UserBase):
    """User profile response."""

    id: UUID
    subscription_tier: str = "free"
    preferences: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class UserPublicResponse(BaseModel):
    """Public user info (for shared insights, etc.)."""

    id: UUID
    display_name: str | None = None
    avatar_url: str | None = None

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Saved Insight Schemas
# ============================================


class SavedInsightCreate(BaseModel):
    """Schema for saving an insight."""

    notes: str | None = Field(None, max_length=2000)
    tags: list[str] | None = Field(None, max_length=10)


class SavedInsightUpdate(BaseModel):
    """Schema for updating a saved insight."""

    notes: str | None = Field(None, max_length=2000)
    tags: list[str] | None = Field(None, max_length=10)
    status: str | None = Field(None, pattern="^(interested|saved|building|not_interested)$")


class SavedInsightResponse(BaseModel):
    """Saved insight response."""

    id: UUID
    insight_id: UUID
    notes: str | None = None
    tags: list[str] = Field(default_factory=list)
    status: str = "saved"
    claimed_at: datetime | None = None
    saved_at: datetime
    shared_count: int = 0

    model_config = ConfigDict(from_attributes=True)


class SavedInsightWithDetails(SavedInsightResponse):
    """Saved insight with full insight details."""

    insight: "InsightSummary"


class SavedInsightListResponse(BaseModel):
    """Paginated saved insights response."""

    items: list[SavedInsightWithDetails]
    total: int
    limit: int
    offset: int


# ============================================
# User Rating Schemas
# ============================================


class RatingCreate(BaseModel):
    """Schema for rating an insight."""

    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    feedback: str | None = Field(None, max_length=1000)


class RatingUpdate(BaseModel):
    """Schema for updating a rating."""

    rating: int | None = Field(None, ge=1, le=5)
    feedback: str | None = Field(None, max_length=1000)


class RatingResponse(BaseModel):
    """Rating response."""

    id: UUID
    insight_id: UUID
    rating: int = Field(ge=1, le=5)
    feedback: str | None = None
    rated_at: datetime

    model_config = ConfigDict(from_attributes=True)


class RatingListResponse(BaseModel):
    """List of user ratings."""

    items: list[RatingResponse]
    total: int


# ============================================
# Workspace Status Schemas
# ============================================


class WorkspaceStatusResponse(BaseModel):
    """User workspace statistics."""

    saved_count: int = Field(description="Total saved insights")
    interested_count: int = Field(description="Insights marked as interested")
    building_count: int = Field(description="Ideas claimed for building")
    ratings_count: int = Field(description="Total ratings given")


class ClaimResponse(BaseModel):
    """Response when claiming an idea."""

    status: str = "building"
    claimed_at: datetime
    insight_id: UUID


class ShareResponse(BaseModel):
    """Response for share tracking."""

    insight_id: UUID
    shared_count: int
    share_url: str | None = None


# ============================================
# Insight Summary (for nested responses)
# ============================================


class InsightSummary(BaseModel):
    """Brief insight summary for saved insights list."""

    id: UUID
    problem_statement: str
    proposed_solution: str
    market_size_estimate: str
    relevance_score: float = Field(ge=0.0, le=1.0)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


# ============================================
# Interaction Tracking Schemas (Phase 4.4)
# ============================================


class InteractionCreate(BaseModel):
    """Schema for tracking an interaction."""

    interaction_type: str = Field(
        description="Type: view, interested, claim, share, export"
    )
    extra_metadata: dict = Field(
        default_factory=dict,
        description="Additional context (e.g., share platform, export format)",
    )


class InteractionResponse(BaseModel):
    """Interaction tracking response."""

    id: UUID
    user_id: UUID
    insight_id: UUID
    interaction_type: str
    extra_metadata: dict = Field(default_factory=dict)
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class InteractionStatsResponse(BaseModel):
    """Interaction statistics for an insight."""

    insight_id: UUID
    total_views: int = 0
    total_interested: int = 0
    total_claims: int = 0
    total_shares: int = 0
    total_exports: int = 0


# ============================================
# Referral Program Schemas
# ============================================


class ReferralStatsResponse(BaseModel):
    """Referral program statistics for the current user."""

    referral_code: str
    referral_link: str
    referrals_count: int
    reward_status: str

    model_config = ConfigDict(from_attributes=True)


# Update forward references
SavedInsightWithDetails.model_rebuild()
