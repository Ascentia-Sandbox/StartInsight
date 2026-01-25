"""Tests for team service - Phase 6.4."""

from datetime import datetime
from unittest.mock import AsyncMock, patch
from uuid import UUID, uuid4

import pytest

from app.services.team_service import (
    ROLE_PERMISSIONS,
    TeamCreate,
    TeamMemberAdd,
    accept_invitation,
    check_permission,
    create_team,
    invite_member,
    share_insight_with_team,
)


class TestRolePermissions:
    """Tests for role permissions configuration."""

    def test_role_permissions_exist(self):
        """Test that all roles have permissions defined."""
        assert "owner" in ROLE_PERMISSIONS
        assert "admin" in ROLE_PERMISSIONS
        assert "member" in ROLE_PERMISSIONS
        assert "viewer" in ROLE_PERMISSIONS

    def test_owner_permissions_is_dict(self):
        """Test owner permissions is a dict."""
        owner_perms = ROLE_PERMISSIONS["owner"]
        assert isinstance(owner_perms, dict)

    def test_viewer_permissions_is_dict(self):
        """Test viewer permissions is a dict."""
        viewer_perms = ROLE_PERMISSIONS["viewer"]
        assert isinstance(viewer_perms, dict)


class TestCheckPermission:
    """Tests for check_permission function."""

    def test_viewer_cannot_invite(self):
        """Test viewer cannot invite members."""
        assert check_permission("viewer", "invite_members") is False

    def test_invalid_role_returns_false(self):
        """Test invalid role returns False."""
        assert check_permission("invalid_role", "view_insights") is False


class TestTeamCreate:
    """Tests for TeamCreate model."""

    def test_valid_team_create(self):
        """Test valid team creation data."""
        team = TeamCreate(
            name="Test Team",
            description="A test team",
        )
        assert team.name == "Test Team"
        assert team.description == "A test team"

    def test_team_create_without_description(self):
        """Test team creation without description."""
        team = TeamCreate(name="Test Team")
        assert team.name == "Test Team"
        assert team.description is None


class TestCreateTeam:
    """Tests for create_team function."""

    @pytest.mark.asyncio
    async def test_create_team_returns_dict(self):
        """Test create_team returns team data dict."""
        owner_id = uuid4()
        result = await create_team(
            name="Test Team",
            owner_id=owner_id,
            description="A test team",
        )
        assert "name" in result
        assert "slug" in result
        assert "owner_id" in result
        assert "created_at" in result

    @pytest.mark.asyncio
    async def test_create_team_with_special_characters(self):
        """Test create_team handles special characters in name."""
        result = await create_team(
            name="Team & Co. (2024)",
            owner_id=uuid4(),
        )
        # Slug should exist
        assert "slug" in result


class TestInviteMember:
    """Tests for invite_member function."""

    @pytest.mark.asyncio
    async def test_invite_member_generates_token(self):
        """Test invite_member generates unique token."""
        result1 = await invite_member(
            team_id=uuid4(),
            team_name="Test Team",
            email="user1@example.com",
            role="member",
            inviter_id=uuid4(),
            inviter_name="John",
            base_url="https://app.example.com",
        )
        result2 = await invite_member(
            team_id=uuid4(),
            team_name="Test Team",
            email="user2@example.com",
            role="member",
            inviter_id=uuid4(),
            inviter_name="Jane",
            base_url="https://app.example.com",
        )
        assert result1["token"] != result2["token"]


class TestAcceptInvitation:
    """Tests for accept_invitation function."""

    @pytest.mark.asyncio
    async def test_accept_invitation_returns_dict(self):
        """Test accept_invitation returns result dict."""
        result = await accept_invitation(
            token="valid_token_123",
            user_id=uuid4(),
        )
        assert "status" in result
        assert "joined_at" in result

    @pytest.mark.asyncio
    async def test_accept_invitation_status_accepted(self):
        """Test accept_invitation sets status to accepted."""
        result = await accept_invitation(
            token="valid_token_123",
            user_id=uuid4(),
        )
        assert result["status"] == "accepted"


class TestShareInsightWithTeam:
    """Tests for share_insight_with_team function."""

    @pytest.mark.asyncio
    async def test_share_insight_returns_dict(self):
        """Test share_insight_with_team returns result dict."""
        result = await share_insight_with_team(
            team_id=uuid4(),
            insight_id=uuid4(),
            shared_by_id=uuid4(),
        )
        assert "team_id" in result
        assert "insight_id" in result
        assert "shared_by_id" in result
        assert "shared_at" in result

    @pytest.mark.asyncio
    async def test_share_insight_with_notes(self):
        """Test share_insight_with_team includes notes."""
        result = await share_insight_with_team(
            team_id=uuid4(),
            insight_id=uuid4(),
            shared_by_id=uuid4(),
            notes="Check out this insight!",
        )
        assert result["notes"] == "Check out this insight!"
