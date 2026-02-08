"""Teams API Routes - Phase 6.4.

Endpoints for team collaboration features.
"""

import logging
from datetime import UTC, datetime, timedelta
from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel, EmailStr, Field
from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from app.api.deps import get_current_user, get_db
from app.models import User
from app.models.team import SharedInsight, Team, TeamInvitation, TeamMember
from app.services.team_service import (
    check_permission,
    generate_invitation_token,
    generate_team_slug,
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
# Helpers
# ============================================================


def _team_to_response(team: Team, member_count: int) -> TeamResponse:
    """Convert a Team model to response."""
    return TeamResponse(
        id=str(team.id),
        name=team.name,
        slug=team.slug,
        description=team.description,
        owner_id=str(team.owner_id),
        member_count=member_count,
        created_at=team.created_at.isoformat(),
    )


async def _get_team_and_membership(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> tuple[Team, TeamMember | None]:
    """Get team and the user's membership. Raises 404 if team not found."""
    team_result = await db.execute(select(Team).where(Team.id == team_id))
    team = team_result.scalar_one_or_none()
    if not team:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Team not found",
        )

    member_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    membership = member_result.scalar_one_or_none()
    return team, membership


async def _require_membership(
    team_id: UUID,
    user_id: UUID,
    db: AsyncSession,
) -> tuple[Team, TeamMember]:
    """Get team and require user to be a member. Raises 403 if not."""
    team, membership = await _get_team_and_membership(team_id, user_id, db)
    if not membership:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You are not a member of this team",
        )
    return team, membership


async def _get_member_count(team_id: UUID, db: AsyncSession) -> int:
    """Get member count for a team."""
    count = await db.scalar(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team_id)
    )
    return count or 0


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
    slug = generate_team_slug(request.name)

    team = Team(
        name=request.name,
        slug=slug,
        description=request.description,
        owner_id=current_user.id,
        settings={
            "max_members": 10,
            "default_role": "member",
            "allow_member_invites": False,
        },
    )
    db.add(team)
    await db.flush()

    # Add owner as first member
    owner_member = TeamMember(
        team_id=team.id,
        user_id=current_user.id,
        role="owner",
        permissions={
            "can_manage_team": True,
            "can_invite": True,
            "can_remove_members": True,
            "can_share": True,
            "can_export": True,
            "can_delete_team": True,
        },
    )
    db.add(owner_member)
    await db.commit()
    await db.refresh(team)

    logger.info(f"Team created: {request.name} (slug: {slug}) by {current_user.id}")

    return _team_to_response(team, member_count=1)


@router.get("", response_model=list[TeamResponse])
async def list_user_teams(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[TeamResponse]:
    """
    List teams the current user belongs to.

    Requires authentication.
    """
    # Find all teams where user is a member
    query = (
        select(Team)
        .join(TeamMember, TeamMember.team_id == Team.id)
        .where(TeamMember.user_id == current_user.id)
        .order_by(Team.created_at.desc())
    )
    result = await db.execute(query)
    teams = result.scalars().all()

    # Get member counts
    responses = []
    for team in teams:
        count = await _get_member_count(team.id, db)
        responses.append(_team_to_response(team, count))

    return responses


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
    team, _ = await _require_membership(team_id, current_user.id, db)
    count = await _get_member_count(team_id, db)
    return _team_to_response(team, count)


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
    team, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_manage_team"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only owners and admins can update team settings",
        )

    if request.name is not None:
        team.name = request.name
    if request.description is not None:
        team.description = request.description
    if request.logo_url is not None:
        team.logo_url = request.logo_url
    if request.primary_color is not None:
        team.primary_color = request.primary_color

    await db.commit()
    await db.refresh(team)

    count = await _get_member_count(team_id, db)
    return _team_to_response(team, count)


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
    team, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_delete_team"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can delete the team",
        )

    await db.delete(team)
    await db.commit()

    logger.info(f"Team deleted: {team_id} by {current_user.id}")


# ============================================================
# Member Management Endpoints
# ============================================================


@router.get("/{team_id}/members")
async def list_team_members(
    team_id: UUID,
    limit: int = Query(default=50, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """
    List team members.

    Requires authentication. User must be a team member.
    """
    await _require_membership(team_id, current_user.id, db)

    total = await db.scalar(
        select(func.count(TeamMember.id)).where(TeamMember.team_id == team_id)
    ) or 0

    query = (
        select(TeamMember)
        .options(selectinload(TeamMember.user))
        .where(TeamMember.team_id == team_id)
        .order_by(TeamMember.joined_at)
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    members = result.scalars().all()

    return {
        "members": [
            TeamMemberResponse(
                id=str(m.id),
                user_id=str(m.user_id),
                email=m.user.email if m.user else "",
                display_name=m.user.display_name if m.user else None,
                role=m.role,
                joined_at=m.joined_at.isoformat(),
            ).model_dump()
            for m in members
        ],
        "total": total,
        "limit": limit,
        "offset": offset,
    }


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
    team, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_invite"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to invite members",
        )

    # Check if already a member
    existing_member = await db.execute(
        select(TeamMember)
        .join(User, User.id == TeamMember.user_id)
        .where(TeamMember.team_id == team_id, User.email == request.email)
    )
    if existing_member.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User is already a team member",
        )

    # Check for existing pending invitation
    existing_invite = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.team_id == team_id,
            TeamInvitation.email == request.email,
            TeamInvitation.status == "pending",
        )
    )
    if existing_invite.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="An invitation is already pending for this email",
        )

    token = generate_invitation_token()
    expires_at = datetime.now(UTC) + timedelta(days=7)

    invitation = TeamInvitation(
        team_id=team_id,
        invited_by_id=current_user.id,
        email=request.email,
        role=request.role,
        token=token,
        status="pending",
        expires_at=expires_at,
    )
    db.add(invitation)
    await db.commit()
    await db.refresh(invitation)

    logger.info(f"Team invitation sent: {request.email} to team {team_id}")

    return InvitationResponse(
        id=str(invitation.id),
        email=invitation.email,
        role=invitation.role,
        status=invitation.status,
        expires_at=invitation.expires_at.isoformat(),
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
    _, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_invite"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to view invitations",
        )

    query = (
        select(TeamInvitation)
        .where(
            TeamInvitation.team_id == team_id,
            TeamInvitation.status == "pending",
        )
        .order_by(TeamInvitation.created_at.desc())
    )
    result = await db.execute(query)
    invitations = result.scalars().all()

    return [
        InvitationResponse(
            id=str(inv.id),
            email=inv.email,
            role=inv.role,
            status=inv.status,
            expires_at=inv.expires_at.isoformat(),
        )
        for inv in invitations
    ]


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
    _, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_invite"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to revoke invitations",
        )

    inv_result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.id == invitation_id,
            TeamInvitation.team_id == team_id,
            TeamInvitation.status == "pending",
        )
    )
    invitation = inv_result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found",
        )

    invitation.status = "revoked"
    await db.commit()

    logger.info(f"Invitation {invitation_id} revoked by {current_user.id}")


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
    inv_result = await db.execute(
        select(TeamInvitation).where(
            TeamInvitation.token == token,
            TeamInvitation.status == "pending",
        )
    )
    invitation = inv_result.scalar_one_or_none()

    if not invitation:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Invitation not found or already used",
        )

    # Check expiration
    if invitation.expires_at < datetime.now(UTC):
        invitation.status = "expired"
        await db.commit()
        raise HTTPException(
            status_code=status.HTTP_410_GONE,
            detail="Invitation has expired",
        )

    # Check if already a member
    existing = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == invitation.team_id,
            TeamMember.user_id == current_user.id,
        )
    )
    if existing.scalar_one_or_none():
        invitation.status = "accepted"
        await db.commit()
        return {"status": "already_member", "joined_at": datetime.now(UTC).isoformat()}

    # Create membership
    member = TeamMember(
        team_id=invitation.team_id,
        user_id=current_user.id,
        role=invitation.role,
        permissions={},
    )
    db.add(member)

    invitation.status = "accepted"
    invitation.accepted_at = datetime.now(UTC)
    await db.commit()

    logger.info(f"User {current_user.id} accepted invitation to team {invitation.team_id}")

    return {"status": "accepted", "joined_at": member.joined_at.isoformat()}


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
    team, membership = await _require_membership(team_id, current_user.id, db)

    is_self_remove = user_id == current_user.id

    if not is_self_remove and not check_permission(membership.role, "can_remove_members"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to remove members",
        )

    # Can't remove the owner
    if user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot remove the team owner. Transfer ownership first.",
        )

    target_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    target_member = target_result.scalar_one_or_none()

    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    await db.delete(target_member)
    await db.commit()

    logger.info(f"Member {user_id} removed from team {team_id} by {current_user.id}")


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
    team, membership = await _require_membership(team_id, current_user.id, db)

    # Only owner can change roles
    if team.owner_id != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Only the team owner can change member roles",
        )

    # Can't change owner's role
    if user_id == team.owner_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot change the owner's role",
        )

    target_result = await db.execute(
        select(TeamMember).where(
            TeamMember.team_id == team_id,
            TeamMember.user_id == user_id,
        )
    )
    target_member = target_result.scalar_one_or_none()

    if not target_member:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Member not found",
        )

    target_member.role = role
    await db.commit()

    logger.info(f"Member {user_id} role updated to {role} in team {team_id}")

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
    _, membership = await _require_membership(team_id, current_user.id, db)

    if not check_permission(membership.role, "can_share"):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have permission to share insights",
        )

    # Check if already shared
    existing = await db.execute(
        select(SharedInsight).where(
            SharedInsight.team_id == team_id,
            SharedInsight.insight_id == request.insight_id,
        )
    )
    if existing.scalar_one_or_none():
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="This insight is already shared with the team",
        )

    shared = SharedInsight(
        team_id=team_id,
        insight_id=request.insight_id,
        shared_by_id=current_user.id,
        notes=request.notes,
        permissions={
            "can_edit": False,
            "can_comment": True,
            "can_reshare": False,
        },
    )
    db.add(shared)
    await db.commit()
    await db.refresh(shared)

    logger.info(f"Insight {request.insight_id} shared with team {team_id}")

    return {
        "id": str(shared.id),
        "team_id": str(shared.team_id),
        "insight_id": str(shared.insight_id),
        "shared_by_id": str(shared.shared_by_id),
        "notes": shared.notes,
        "shared_at": shared.shared_at.isoformat(),
    }


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
    await _require_membership(team_id, current_user.id, db)

    # Count total
    total = await db.scalar(
        select(func.count(SharedInsight.id)).where(SharedInsight.team_id == team_id)
    ) or 0

    # Fetch paginated
    query = (
        select(SharedInsight)
        .options(selectinload(SharedInsight.shared_by))
        .where(SharedInsight.team_id == team_id)
        .order_by(SharedInsight.shared_at.desc())
        .limit(limit)
        .offset(offset)
    )
    result = await db.execute(query)
    shares = result.scalars().all()

    return {
        "insights": [
            {
                "id": str(s.id),
                "insight_id": str(s.insight_id),
                "shared_by_id": str(s.shared_by_id),
                "shared_by_name": s.shared_by.display_name if s.shared_by else None,
                "notes": s.notes,
                "shared_at": s.shared_at.isoformat(),
            }
            for s in shares
        ],
        "total": total,
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
    _, membership = await _require_membership(team_id, current_user.id, db)

    shared_result = await db.execute(
        select(SharedInsight).where(
            SharedInsight.team_id == team_id,
            SharedInsight.insight_id == insight_id,
        )
    )
    shared = shared_result.scalar_one_or_none()

    if not shared:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Shared insight not found",
        )

    # Must be the sharer or an admin/owner
    is_sharer = shared.shared_by_id == current_user.id
    can_manage = check_permission(membership.role, "can_manage_team")

    if not is_sharer and not can_manage:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You can only remove insights you shared, or be a team admin",
        )

    await db.delete(shared)
    await db.commit()

    logger.info(f"Insight {insight_id} unshared from team {team_id}")
