"""Teams API Routes - Phase 6.4.

Endpoints for team collaboration features.
"""

import logging
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import get_current_user, get_db
from app.models import User
from app.services.team_service import (
    accept_invitation,
    create_team,
    invite_member,
    share_insight_with_team,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/teams", tags=["Teams"])


# ============================================================
# Request/Response Schemas
# ============================================================


class TeamCreateRequest(BaseModel):
    """Team creation request."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class TeamUpdateRequest(BaseModel):
    """Team update request."""

    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class InviteMemberRequest(BaseModel):
    """Invite member request."""

    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class ShareInsightRequest(BaseModel):
    """Share insight with team request."""

    insight_id: UUID
    notes: str | None = Field(None, max_length=500)


class TeamResponse(BaseModel):
    """Team response."""

    id: str
    name: str
    slug: str
    description: str | None
    owner_id: str
    member_count: int
    created_at: str


class TeamMemberResponse(BaseModel):
    """Team member response."""

    id: str
    user_id: str
    email: str
    display_name: str | None
    role: str
    joined_at: str


class InvitationResponse(BaseModel):
    """Invitation response."""

    id: str
    email: str
    role: str
    status: str
    expires_at: str


# ============================================================
# Team CRUD Endpoints
# ============================================================


@router.post("", response_model=TeamResponse, status_code=status.HTTP_201_CREATED)
async def create_new_team(
    request: TeamCreateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Create a new team.

    Requires authentication. User becomes the team owner.
    """
    team_data = await create_team(
        name=request.name,
        owner_id=current_user.id,
        description=request.description,
    )

    # TODO: Save to database and return actual team

    return TeamResponse(
        id=team_data.get("slug", ""),  # Use slug as temp ID
        name=team_data["name"],
        slug=team_data["slug"],
        description=team_data.get("description"),
        owner_id=str(current_user.id),
        member_count=1,
        created_at=team_data["created_at"],
    )


@router.get("", response_model=list[TeamResponse])
async def list_user_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamResponse]:
    """
    List teams the current user belongs to.

    Requires authentication.
    """
    # TODO: Query database for user's teams
    # For now, return empty list
    return []


@router.get("/{team_id}", response_model=TeamResponse)
async def get_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Get team details.

    Requires authentication. User must be a team member.
    """
    # TODO: Query database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Team not found",
    )


@router.patch("/{team_id}", response_model=TeamResponse)
async def update_team(
    team_id: UUID,
    request: TeamUpdateRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> TeamResponse:
    """
    Update team details.

    Requires authentication. User must be team owner or admin.
    """
    # TODO: Verify permissions and update database
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Team not found",
    )


@router.delete("/{team_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_team(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Delete a team.

    Requires authentication. Only team owner can delete.
    """
    # TODO: Verify ownership and delete
    raise HTTPException(
        status_code=status.HTTP_404_NOT_FOUND,
        detail="Team not found",
    )


# ============================================================
# Member Management Endpoints
# ============================================================


@router.get("/{team_id}/members", response_model=list[TeamMemberResponse])
async def list_team_members(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamMemberResponse]:
    """
    List team members.

    Requires authentication. User must be a team member.
    """
    # TODO: Query database
    return []


@router.post("/{team_id}/invitations", response_model=InvitationResponse)
async def invite_team_member(
    team_id: UUID,
    request: InviteMemberRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> InvitationResponse:
    """
    Invite a new member to the team.

    Requires authentication. User must have invite permission.
    """
    # TODO: Verify team exists and user has permission
    result = await invite_member(
        team_id=team_id,
        team_name="Team Name",  # Would come from database
        email=request.email,
        role=request.role,
        inviter_id=current_user.id,
        inviter_name=current_user.display_name or current_user.email,
        base_url="https://app.startinsight.ai",
    )

    return InvitationResponse(
        id=result.get("token", ""),
        email=result["email"],
        role=result["role"],
        status=result["status"],
        expires_at=result["expires_at"],
    )


@router.get("/{team_id}/invitations", response_model=list[InvitationResponse])
async def list_pending_invitations(
    team_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[InvitationResponse]:
    """
    List pending team invitations.

    Requires authentication. User must be team admin or owner.
    """
    # TODO: Query database
    return []


@router.delete("/{team_id}/invitations/{invitation_id}", status_code=status.HTTP_204_NO_CONTENT)
async def revoke_invitation(
    team_id: UUID,
    invitation_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Revoke a pending invitation.

    Requires authentication. User must be team admin or owner.
    """
    # TODO: Verify and delete invitation
    pass


@router.post("/invitations/{token}/accept")
async def accept_team_invitation(
    token: str,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Accept a team invitation.

    Requires authentication.
    """
    result = await accept_invitation(token=token, user_id=current_user.id)

    return {
        "status": "accepted",
        "joined_at": result["joined_at"],
    }


@router.delete("/{team_id}/members/{user_id}", status_code=status.HTTP_204_NO_CONTENT)
async def remove_team_member(
    team_id: UUID,
    user_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a member from the team.

    Requires authentication. User must be admin/owner, or removing self.
    """
    # TODO: Verify permissions and remove member
    pass


@router.patch("/{team_id}/members/{user_id}/role")
async def update_member_role(
    team_id: UUID,
    user_id: UUID,
    role: str = Query(..., pattern=r"^(admin|member|viewer)$"),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, str]:
    """
    Update a team member's role.

    Requires authentication. Only owner can change roles.
    """
    # TODO: Verify ownership and update role
    return {"role": role, "updated": "true"}


# ============================================================
# Shared Insights Endpoints
# ============================================================


@router.post("/{team_id}/insights", status_code=status.HTTP_201_CREATED)
async def share_insight(
    team_id: UUID,
    request: ShareInsightRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    Share an insight with the team.

    Requires authentication. User must be team member with share permission.
    """
    result = await share_insight_with_team(
        team_id=team_id,
        insight_id=request.insight_id,
        shared_by_id=current_user.id,
        notes=request.notes,
    )

    return result


@router.get("/{team_id}/insights")
async def list_shared_insights(
    team_id: UUID,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict[str, Any]:
    """
    List insights shared with the team.

    Requires authentication. User must be team member.
    """
    # TODO: Query shared_insights table
    return {
        "insights": [],
        "total": 0,
        "limit": limit,
        "offset": offset,
    }


@router.delete("/{team_id}/insights/{insight_id}", status_code=status.HTTP_204_NO_CONTENT)
async def unshare_insight(
    team_id: UUID,
    insight_id: UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> None:
    """
    Remove a shared insight from the team.

    Requires authentication. User must be the one who shared it or an admin.
    """
    # TODO: Verify and delete shared insight
    pass
