"""Email Service - Phase 6.2 Resend Integration.

Handles transactional emails for:
- Welcome/onboarding
- Daily insight digest
- Research analysis ready
- Payment confirmations
- Team invitations
- Password reset
"""

import logging
import re
from datetime import datetime
from typing import Any

from pydantic import BaseModel

from app.core.config import settings

logger = logging.getLogger(__name__)


# ============================================================
# Email Templates
# ============================================================


class EmailTemplate(BaseModel):
    """Email template configuration."""

    subject: str
    template_id: str | None = None  # For Resend templates
    html_template: str


TEMPLATES: dict[str, EmailTemplate] = {
    "welcome": EmailTemplate(
        subject="Welcome to StartInsight! 🚀",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Welcome to StartInsight!</h1>
            <p>Hi {{name}},</p>
            <p>Thanks for joining StartInsight! You now have access to AI-powered startup insights.</p>
            <h3>Getting Started:</h3>
            <ul>
                <li>Browse today's top insights</li>
                <li>Save ideas to your workspace</li>
                <li>Run deep research on your favorites</li>
            </ul>
            <a href="{{dashboard_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                Go to Dashboard
            </a>
            <p style="margin-top: 24px; color: #6B7280;">
                Questions? Reply to this email or check our <a href="{{help_url}}">help docs</a>.
            </p>
        </div>
        """,
    ),
    "daily_digest": EmailTemplate(
        subject="Your Daily Startup Insights 📊",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Today's Top Insights</h1>
            <p>Hi {{name}}, here are today's best startup opportunities:</p>

            {{#insights}}
            <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <h3 style="margin: 0 0 8px 0;">{{title}}</h3>
                <p style="color: #6B7280; margin: 0 0 8px 0;">{{problem_statement}}</p>
                <div style="display: flex; gap: 8px;">
                    <span style="background: #DBEAFE; color: #1E40AF; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        Score: {{relevance_score}}
                    </span>
                    <span style="background: #D1FAE5; color: #065F46; padding: 4px 8px; border-radius: 4px; font-size: 12px;">
                        {{market_size}}
                    </span>
                </div>
            </div>
            {{/insights}}

            <a href="{{dashboard_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                View All Insights
            </a>

            <p style="margin-top: 24px; color: #6B7280; font-size: 12px;">
                <a href="{{unsubscribe_url}}">Unsubscribe from daily digest</a>
            </p>
        </div>
        """,
    ),
    "analysis_ready": EmailTemplate(
        subject="Your Research Analysis is Ready! 🎯",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Research Analysis Complete</h1>
            <p>Hi {{name}},</p>
            <p>Your deep analysis for <strong>"{{idea_title}}"</strong> is ready!</p>

            <div style="background: #F3F4F6; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin: 0 0 12px 0;">Summary Scores</h3>
                <p style="margin: 4px 0;">🎯 Opportunity Score: <strong>{{opportunity_score}}%</strong></p>
                <p style="margin: 4px 0;">📈 Market Fit: <strong>{{market_fit_score}}%</strong></p>
                <p style="margin: 4px 0;">⚡ Execution Ready: <strong>{{execution_readiness}}%</strong></p>
            </div>

            <a href="{{analysis_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                View Full Analysis
            </a>
        </div>
        """,
    ),
    "payment_success": EmailTemplate(
        subject="Payment Confirmed - StartInsight {{tier}}",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #10B981;">Payment Successful! ✓</h1>
            <p>Hi {{name}},</p>
            <p>Your payment has been processed successfully.</p>

            <div style="background: #F3F4F6; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <p style="margin: 4px 0;"><strong>Plan:</strong> {{tier}}</p>
                <p style="margin: 4px 0;"><strong>Amount:</strong> {{amount}}</p>
                <p style="margin: 4px 0;"><strong>Date:</strong> {{date}}</p>
            </div>

            <p>You now have access to all {{tier}} features. Thanks for your support!</p>

            <a href="{{dashboard_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                Go to Dashboard
            </a>
        </div>
        """,
    ),
    "team_invitation": EmailTemplate(
        subject="You've been invited to join {{team_name}} on StartInsight",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Team Invitation</h1>
            <p>Hi there,</p>
            <p><strong>{{inviter_name}}</strong> has invited you to join <strong>{{team_name}}</strong> on StartInsight.</p>

            <p>You'll be able to:</p>
            <ul>
                <li>View shared insights</li>
                <li>Collaborate on research</li>
                <li>Share your findings with the team</li>
            </ul>

            <a href="{{invitation_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                Accept Invitation
            </a>

            <p style="margin-top: 24px; color: #6B7280; font-size: 12px;">
                This invitation expires in 7 days. If you didn't expect this email, you can safely ignore it.
            </p>
        </div>
        """,
    ),
    "weekly_digest": EmailTemplate(
        subject="Your Weekly Startup Briefing - Top 10 Insights",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Weekly Startup Briefing</h1>
            <p>Hi {{name}}, here are the top 10 startup opportunities from this week:</p>

            {{#insights}}
            <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; margin-bottom: 12px;">
                <h3 style="margin: 0 0 6px 0; font-size: 15px;">{{title}}</h3>
                <p style="color: #6B7280; margin: 0 0 8px 0; font-size: 13px;">{{problem_statement}}</p>
                <div style="display: flex; gap: 8px;">
                    <span style="background: #DBEAFE; color: #1E40AF; padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                        Score: {{relevance_score}}
                    </span>
                    <span style="background: #D1FAE5; color: #065F46; padding: 3px 8px; border-radius: 4px; font-size: 11px;">
                        {{market_size}}
                    </span>
                </div>
            </div>
            {{/insights}}

            <a href="{{dashboard_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px; margin-top: 8px;">
                Explore All Insights
            </a>

            <p style="margin-top: 24px; color: #6B7280; font-size: 12px;">
                <a href="{{unsubscribe_url}}">Unsubscribe from weekly digest</a>
            </p>
        </div>
        """,
    ),
    "contact_form": EmailTemplate(
        subject="New Contact Form: {{subject}}",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">New Contact Form Submission</h1>

            <div style="background: #F3F4F6; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <p style="margin: 4px 0;"><strong>From:</strong> {{name}} ({{email}})</p>
                <p style="margin: 4px 0;"><strong>Subject:</strong> {{subject}}</p>
                <p style="margin: 4px 0;"><strong>Time:</strong> {{timestamp}}</p>
            </div>

            <div style="border: 1px solid #E5E7EB; border-radius: 8px; padding: 16px; margin: 16px 0;">
                <h3 style="margin: 0 0 8px 0;">Message</h3>
                <p style="color: #374151; white-space: pre-wrap;">{{message}}</p>
            </div>

            <p style="margin-top: 24px; color: #6B7280; font-size: 12px;">
                Reply directly to <a href="mailto:{{email}}">{{email}}</a> to respond.
            </p>
        </div>
        """,
    ),
    "password_reset": EmailTemplate(
        subject="Reset Your StartInsight Password",
        html_template="""
        <div style="font-family: 'Inter', sans-serif; max-width: 600px; margin: 0 auto;">
            <h1 style="color: #3B82F6;">Password Reset</h1>
            <p>Hi {{name}},</p>
            <p>We received a request to reset your password. Click the button below to create a new password:</p>

            <a href="{{reset_url}}" style="display: inline-block; background: #3B82F6; color: white; padding: 12px 24px; text-decoration: none; border-radius: 6px;">
                Reset Password
            </a>

            <p style="margin-top: 24px; color: #6B7280; font-size: 12px;">
                This link expires in 1 hour. If you didn't request this, you can safely ignore this email.
            </p>
        </div>
        """,
    ),
}


# ============================================================
# Email Service Functions
# ============================================================


def get_resend_client():
    """Get Resend client instance."""
    try:
        import resend
        resend.api_key = settings.resend_api_key
        return resend
    except ImportError:
        logger.warning("Resend not installed")
        return None


async def send_email(
    to: str | list[str],
    template: str,
    variables: dict[str, Any],
    cc: list[str] | None = None,
    bcc: list[str] | None = None,
) -> dict[str, Any]:
    """
    Send an email using a template.

    Args:
        to: Recipient email(s)
        template: Template name from TEMPLATES
        variables: Variables to substitute in template
        cc: Optional CC recipients
        bcc: Optional BCC recipients

    Returns:
        Send result with message ID or error
    """
    if template not in TEMPLATES:
        logger.error(f"Unknown email template: {template}")
        return {"status": "error", "error": f"Unknown template: {template}"}

    email_template = TEMPLATES[template]

    # Render template with variables
    html_content = _render_template(email_template.html_template, variables)
    subject = _render_template(email_template.subject, variables)

    resend_client = get_resend_client()
    if not resend_client or not settings.resend_api_key:
        logger.warning(f"Email not sent (Resend not configured): {template} to {to}")
        return {
            "status": "skipped",
            "reason": "not_configured",
            "template": template,
            "to": to,
        }

    try:
        # Normalize to list
        if isinstance(to, str):
            to = [to]

        params = {
            "from": f"{settings.email_from_name} <{settings.email_from_address}>",
            "to": to,
            "subject": subject,
            "html": html_content,
        }

        if cc:
            params["cc"] = cc
        if bcc:
            params["bcc"] = bcc

        import asyncio
        response = await asyncio.to_thread(resend_client.Emails.send, params)

        logger.info(f"Email sent: {template} to {to}, id={response.get('id')}")
        return {
            "status": "sent",
            "id": response.get("id"),
            "template": template,
            "to": to,
        }

    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return {"status": "error", "error": str(e)}


# ============================================================
# Convenience Functions
# ============================================================


async def send_welcome_email(email: str, name: str, dashboard_url: str) -> dict:
    """Send welcome email to new user."""
    return await send_email(
        to=email,
        template="welcome",
        variables={
            "name": name or "there",
            "dashboard_url": dashboard_url,
            "help_url": f"{dashboard_url}/help",
        },
    )


async def send_daily_digest(
    email: str,
    name: str,
    insights: list[dict],
    dashboard_url: str,
    unsubscribe_url: str,
) -> dict:
    """
    Send daily insight digest.

    PMF Optimization: Disabled by default to save email quota.
    Set ENABLE_DAILY_DIGEST=true to enable.
    """
    # PMF optimization: skip daily digest to stay in Resend Free tier (3K/mo)
    if not settings.enable_daily_digest:
        logger.info(f"Daily digest disabled for PMF mode (recipient: {email})")
        return {"status": "skipped", "reason": "feature_disabled_pmf"}

    return await send_email(
        to=email,
        template="daily_digest",
        variables={
            "name": name or "there",
            "insights": insights[:5],  # Top 5
            "dashboard_url": dashboard_url,
            "unsubscribe_url": unsubscribe_url,
        },
    )


async def send_analysis_ready_email(
    email: str,
    name: str,
    idea_title: str,
    scores: dict[str, float],
    analysis_url: str,
) -> dict:
    """Send notification when research analysis is complete."""
    return await send_email(
        to=email,
        template="analysis_ready",
        variables={
            "name": name or "there",
            "idea_title": idea_title[:100],
            "opportunity_score": f"{scores.get('opportunity_score', 0) * 100:.0f}",
            "market_fit_score": f"{scores.get('market_fit_score', 0) * 100:.0f}",
            "execution_readiness": f"{scores.get('execution_readiness', 0) * 100:.0f}",
            "analysis_url": analysis_url,
        },
    )


async def send_payment_confirmation(
    email: str,
    name: str,
    tier: str,
    amount: str,
    dashboard_url: str,
) -> dict:
    """Send payment confirmation email."""
    return await send_email(
        to=email,
        template="payment_success",
        variables={
            "name": name or "there",
            "tier": tier.capitalize(),
            "amount": amount,
            "date": datetime.now().strftime("%B %d, %Y"),
            "dashboard_url": dashboard_url,
        },
    )


async def send_team_invitation(
    email: str,
    team_name: str,
    inviter_name: str,
    invitation_url: str,
) -> dict:
    """Send team invitation email."""
    return await send_email(
        to=email,
        template="team_invitation",
        variables={
            "team_name": team_name,
            "inviter_name": inviter_name,
            "invitation_url": invitation_url,
        },
    )


async def send_weekly_digest(
    email: str,
    name: str,
    insights: list[dict],
    dashboard_url: str,
    unsubscribe_url: str,
) -> dict:
    """Send weekly digest of top insights."""
    return await send_email(
        to=email,
        template="weekly_digest",
        variables={
            "name": name or "there",
            "insights": insights[:10],
            "dashboard_url": dashboard_url,
            "unsubscribe_url": unsubscribe_url,
        },
    )


async def send_password_reset(email: str, name: str, reset_url: str) -> dict:
    """Send password reset email."""
    return await send_email(
        to=email,
        template="password_reset",
        variables={
            "name": name or "there",
            "reset_url": reset_url,
        },
    )


# ============================================================
# Helper Functions
# ============================================================


def _render_template(template: str, variables: dict[str, Any]) -> str:
    """Simple template rendering with {{variable}} and {{#list}}...{{/list}} syntax."""

    result = template

    # Handle list sections first: {{#key}}...{{/key}}
    for key, value in variables.items():
        if not isinstance(value, list):
            continue
        pattern = re.compile(
            r"\{\{#" + re.escape(key) + r"\}\}(.*?)\{\{/" + re.escape(key) + r"\}\}",
            re.DOTALL,
        )
        match = pattern.search(result)
        if match:
            inner_template = match.group(1)
            rendered_items = []
            for item in value:
                rendered_item = inner_template
                if isinstance(item, dict):
                    for k, v in item.items():
                        rendered_item = rendered_item.replace(
                            "{{" + k + "}}", str(v) if v else ""
                        )
                rendered_items.append(rendered_item)
            result = result[: match.start()] + "".join(rendered_items) + result[match.end() :]

    # Handle scalar variables: {{key}}
    for key, value in variables.items():
        if isinstance(value, list):
            continue
        result = result.replace("{{" + key + "}}", str(value) if value else "")

    return result
