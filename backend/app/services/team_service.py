"""Team Service - Phase 6.4 Team Collaboration.

Handles team creation, membership, invitations, and shared insights.
"""

import logging
import secrets
from datetime import datetime, timedelta
from typing import Any
from uuid import UUID

from pydantic import BaseModel, EmailStr, Field

from app.core.config import settings
from app.services.email_service import send_team_invitation

logger = logging.getLogger(__name__)


# ============================================================
# Team Schemas
# ============================================================


class TeamCreate(BaseModel):
    """Schema for team creation."""

    name: str = Field(..., min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)


class TeamUpdate(BaseModel):
    """Schema for team update."""

    name: str | None = Field(None, min_length=2, max_length=100)
    description: str | None = Field(None, max_length=500)
    logo_url: str | None = None
    primary_color: str | None = Field(None, pattern=r"^#[0-9A-Fa-f]{6}$")


class TeamMemberAdd(BaseModel):
    """Schema for adding team member."""

    email: EmailStr
    role: str = Field(default="member", pattern=r"^(admin|member|viewer)$")


class TeamInviteResponse(BaseModel):
    """Response for team invitation."""

    invitation_id: str
    email: str
    role: str
    expires_at: str
    status: str


# ============================================================
# Team Service Functions
# ============================================================


def generate_team_slug(name: str) -> str:
    """Generate a unique slug from team name."""
    import re

    # Convert to lowercase, replace spaces with hyphens
    slug = name.lower().strip()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug)
    slug = slug.strip("-")

    # Add random suffix for uniqueness
    suffix = secrets.token_hex(3)
    return f"{slug}-{suffix}"


def generate_invitation_token() -> str:
    """Generate a secure invitation token."""
    return secrets.token_urlsafe(32)


async def create_team(
    name: str,
    owner_id: UUID,
    description: str | None = None,
) -> dict[str, Any]:
    """
    Create a new team.

    Args:
        name: Team name
        owner_id: User ID of the team creator
        description: Optional team description

    Returns:
        dict with team data
    """
    slug = generate_team_slug(name)

    team_data = {
        "name": name,
        "slug": slug,
        "description": description,
        "owner_id": str(owner_id),
        "settings": {
            "max_members": 10,
            "default_role": "member",
            "allow_member_invites": False,
        },
        "created_at": datetime.now().isoformat(),
    }

    logger.info(f"Team created: {name} (slug: {slug}) by {owner_id}")
    return team_data


async def invite_member(
    team_id: UUID,
    team_name: str,
    email: str,
    role: str,
    inviter_id: UUID,
    inviter_name: str,
    base_url: str,
) -> dict[str, Any]:
    """
    Create and send team invitation.

    Args:
        team_id: Team UUID
        team_name: Team name for email
        email: Invitee email
        role: Role to assign (admin, member, viewer)
        inviter_id: ID of user sending invitation
        inviter_name: Name of inviter for email
        base_url: Base URL for invitation link

    Returns:
        Invitation details
    """
    token = generate_invitation_token()
    expires_at = datetime.now() + timedelta(days=7)

    invitation_data = {
        "team_id": str(team_id),
        "email": email,
        "role": role,
        "token": token,
        "invited_by_id": str(inviter_id),
        "status": "pending",
        "expires_at": expires_at.isoformat(),
        "created_at": datetime.now().isoformat(),
    }

    # Send invitation email
    invitation_url = f"{base_url}/invite/{token}"
    email_result = await send_team_invitation(
        email=email,
        team_name=team_name,
        inviter_name=inviter_name,
        invitation_url=invitation_url,
    )

    logger.info(f"Team invitation sent: {email} to {team_name} as {role}")

    return {
        **invitation_data,
        "email_sent": email_result.get("status") == "sent",
    }


async def accept_invitation(
    token: str,
    user_id: UUID,
) -> dict[str, Any]:
    """
    Accept a team invitation.

    Args:
        token: Invitation token
        user_id: User accepting the invitation

    Returns:
        Membership details or error
    """
    # In production, this would verify the token from database
    # and create the team membership

    membership_data = {
        "user_id": str(user_id),
        "joined_at": datetime.now().isoformat(),
        "status": "accepted",
    }

    logger.info(f"Invitation accepted: user {user_id} joined team via token")
    return membership_data


async def share_insight_with_team(
    team_id: UUID,
    insight_id: UUID,
    shared_by_id: UUID,
    notes: str | None = None,
) -> dict[str, Any]:
    """
    Share an insight with a team.

    Args:
        team_id: Team to share with
        insight_id: Insight to share
        shared_by_id: User sharing the insight
        notes: Optional notes about the share

    Returns:
        Share details
    """
    share_data = {
        "team_id": str(team_id),
        "insight_id": str(insight_id),
        "shared_by_id": str(shared_by_id),
        "notes": notes,
        "permissions": {
            "can_edit": False,
            "can_comment": True,
            "can_reshare": False,
        },
        "shared_at": datetime.now().isoformat(),
    }

    logger.info(f"Insight {insight_id} shared with team {team_id}")
    return share_data


# ============================================================
# Permission Helpers
# ============================================================


ROLE_PERMISSIONS = {
    "owner": {
        "can_manage_team": True,
        "can_invite": True,
        "can_remove_members": True,
        "can_share": True,
        "can_export": True,
        "can_delete_team": True,
    },
    "admin": {
        "can_manage_team": True,
        "can_invite": True,
        "can_remove_members": True,
        "can_share": True,
        "can_export": True,
        "can_delete_team": False,
    },
    "member": {
        "can_manage_team": False,
        "can_invite": False,
        "can_remove_members": False,
        "can_share": True,
        "can_export": True,
        "can_delete_team": False,
    },
    "viewer": {
        "can_manage_team": False,
        "can_invite": False,
        "can_remove_members": False,
        "can_share": False,
        "can_export": False,
        "can_delete_team": False,
    },
}


def get_role_permissions(role: str) -> dict[str, bool]:
    """Get permissions for a role."""
    return ROLE_PERMISSIONS.get(role, ROLE_PERMISSIONS["viewer"])


def check_permission(role: str, permission: str) -> bool:
    """Check if a role has a specific permission."""
    permissions = get_role_permissions(role)
    return permissions.get(permission, False)
