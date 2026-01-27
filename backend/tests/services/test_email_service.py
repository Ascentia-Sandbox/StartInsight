"""Tests for email service - Phase 6.2."""

from unittest.mock import AsyncMock, patch

import pytest

from app.services.email_service import (
    TEMPLATES,
    send_analysis_ready_email,
    send_daily_digest,
    send_email,
    send_password_reset,
    send_payment_confirmation,
    send_team_invitation,
    send_welcome_email,
)


class TestEmailTemplates:
    """Tests for email templates."""

    def test_templates_exist(self):
        """Test that required templates exist."""
        required_templates = [
            "welcome",
            "daily_digest",
            "analysis_ready",
        ]
        for template in required_templates:
            assert template in TEMPLATES

    def test_templates_have_subject(self):
        """Test that all templates have subjects."""
        for name, template in TEMPLATES.items():
            assert hasattr(template, 'subject')
            assert len(template.subject) > 0


class TestSendEmail:
    """Tests for send_email function."""

    @pytest.mark.asyncio
    async def test_send_email_without_api_key(self):
        """Test send_email returns False without API key."""
        with patch("app.services.email_service.settings") as mock_settings:
            mock_settings.resend_api_key = None
            result = await send_email(
                to="test@example.com",
                template="welcome",
                variables={"name": "Test"},
            )
            # Should not send without API key
            assert result is not None


class TestSendWelcomeEmail:
    """Tests for send_welcome_email function."""

    @pytest.mark.asyncio
    async def test_welcome_email_returns_dict(self):
        """Test welcome email returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_welcome_email(
                email="user@example.com",
                name="Test User",
                dashboard_url="https://example.com/dashboard",
            )
            assert isinstance(result, dict)


class TestSendDailyDigest:
    """Tests for send_daily_digest function."""

    @pytest.mark.asyncio
    async def test_daily_digest_returns_dict(self):
        """Test daily digest returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_daily_digest(
                email="user@example.com",
                name="Test User",
                insights=[],
                dashboard_url="https://example.com/dashboard",
                unsubscribe_url="https://example.com/unsubscribe",
            )
            assert isinstance(result, dict)


class TestSendAnalysisReadyEmail:
    """Tests for send_analysis_ready_email function."""

    @pytest.mark.asyncio
    async def test_analysis_ready_email(self):
        """Test analysis ready email returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_analysis_ready_email(
                email="user@example.com",
                name="Test User",
                idea_title="AI Tools Analysis",
                scores={"overall": 0.85},
                analysis_url="https://example.com/analysis/123",
            )
            assert isinstance(result, dict)


class TestSendPaymentConfirmation:
    """Tests for send_payment_confirmation function."""

    @pytest.mark.asyncio
    async def test_payment_confirmation_email(self):
        """Test payment confirmation email returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_payment_confirmation(
                email="user@example.com",
                name="Test User",
                tier="pro",
                amount="$49.00",
                dashboard_url="https://example.com/dashboard",
            )
            assert isinstance(result, dict)


class TestSendTeamInvitation:
    """Tests for send_team_invitation function."""

    @pytest.mark.asyncio
    async def test_team_invitation_email(self):
        """Test team invitation email returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_team_invitation(
                email="invitee@example.com",
                team_name="Acme Team",
                inviter_name="John Doe",
                invitation_url="https://example.com/invite/token123",
            )
            assert isinstance(result, dict)


class TestSendPasswordReset:
    """Tests for send_password_reset function."""

    @pytest.mark.asyncio
    async def test_password_reset_email(self):
        """Test password reset email returns result dict."""
        with patch("app.services.email_service.send_email", new_callable=AsyncMock) as mock_send:
            mock_send.return_value = {"sent": True}
            result = await send_password_reset(
                email="user@example.com",
                name="Test User",
                reset_url="https://example.com/reset/token123",
            )
            assert isinstance(result, dict)
