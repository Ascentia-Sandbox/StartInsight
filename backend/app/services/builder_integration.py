"""Builder Ecosystem Integration Service - OAuth and API integrations for Lovable, Replit, v0"""

import logging
from datetime import UTC, datetime
from typing import Any
from uuid import UUID

import httpx
from pydantic import BaseModel, Field
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.models.insight import Insight

logger = logging.getLogger(__name__)


# ============================================================================
# PYDANTIC SCHEMAS
# ============================================================================

class BuilderProject(BaseModel):
    """Builder project response"""

    platform: str = Field(..., description="Builder platform (lovable, replit, v0)")
    project_id: str | None = Field(None, description="Project ID from platform")
    project_url: str = Field(..., description="URL to access the project")
    status: str = Field(..., description="Project creation status (success, pending, failed)")
    error: str | None = Field(None, description="Error message if creation failed")
    created_at: str = Field(
        default_factory=lambda: datetime.now(UTC).isoformat(),
        description="Timestamp when project was created",
    )


class OAuthToken(BaseModel):
    """OAuth access token"""

    access_token: str
    token_type: str = "Bearer"
    expires_in: int | None = None
    refresh_token: str | None = None
    scope: str | None = None


# ============================================================================
# LOVABLE.DEV INTEGRATION
# ============================================================================

class LovableIntegration:
    """
    Lovable.dev API integration.

    Lovable is an AI-powered app builder that creates full-stack applications
    from natural language prompts.

    OAuth Flow:
    1. User clicks "Build with Lovable" → redirect to Lovable OAuth
    2. User authorizes → Lovable redirects back with auth code
    3. Exchange auth code for access token
    4. Use access token to create project via API

    API Endpoints (hypothetical - requires Lovable API documentation):
    - POST /api/v1/projects/create
    - GET /api/v1/projects/{project_id}
    """

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """
        Initialize Lovable integration.

        Args:
            client_id: Lovable OAuth client ID (from env: LOVABLE_CLIENT_ID)
            client_secret: Lovable OAuth client secret (from env: LOVABLE_CLIENT_SECRET)
        """
        self.client_id = client_id or getattr(settings, "lovable_client_id", None)
        self.client_secret = client_secret or getattr(settings, "lovable_client_secret", None)
        self.api_base_url = "https://api.lovable.dev"  # Hypothetical
        self.oauth_authorize_url = "https://lovable.dev/oauth/authorize"  # Hypothetical
        self.oauth_token_url = "https://lovable.dev/oauth/token"  # Hypothetical

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """
        Generate OAuth authorization URL.

        Args:
            redirect_uri: Callback URL after authorization
            state: CSRF protection state parameter

        Returns:
            OAuth authorization URL
        """
        return (
            f"{self.oauth_authorize_url}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"state={state}&"
            f"scope=projects:create projects:read"
        )

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> OAuthToken:
        """
        Exchange OAuth authorization code for access token.

        Args:
            code: Authorization code from OAuth callback
            redirect_uri: Same redirect URI used in authorization

        Returns:
            OAuthToken with access token

        Raises:
            httpx.HTTPStatusError: If token exchange fails
        """
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.oauth_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            return OAuthToken(**data)

    async def create_project(
        self,
        access_token: str,
        insight: Insight,
    ) -> BuilderProject:
        """
        Create Lovable project from insight.

        Args:
            access_token: User's OAuth access token
            insight: Insight to build project from

        Returns:
            BuilderProject with project URL

        Raises:
            httpx.HTTPStatusError: If project creation fails
        """
        # Generate prompt from insight
        prompt = self._generate_prompt(insight)

        async with httpx.AsyncClient() as client:
            response = await client.post(
                f"{self.api_base_url}/api/v1/projects/create",
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "name": f"StartInsight - {insight.problem_statement[:50]}",
                    "description": insight.problem_statement,
                    "prompt": prompt,
                    "framework": "react",  # or next, vue, etc.
                    "auto_deploy": True,
                },
                timeout=60.0,  # Project creation may take time
            )
            response.raise_for_status()
            data = response.json()

            return BuilderProject(
                platform="lovable",
                project_id=data.get("project_id"),
                project_url=data.get("project_url", "https://lovable.dev"),
                status="success",
            )

    def _generate_prompt(self, insight: Insight) -> str:
        """Generate Lovable prompt from insight"""
        return f"""Build an MVP for this startup idea:

**Problem:**
{insight.problem_statement}

**Solution:**
{insight.proposed_solution}

**Target Market:**
{insight.market_size}

**Key Features:**
- User authentication
- Dashboard with analytics
- Mobile-responsive design
- {insight.problem_statement.split('.')[0]}

**Tech Stack:**
- Frontend: React with Tailwind CSS
- Backend: Node.js with Express
- Database: PostgreSQL
- Deployment: Vercel

Please create a functional MVP with these core features implemented.
"""


# ============================================================================
# REPLIT INTEGRATION
# ============================================================================

class ReplitIntegration:
    """
    Replit API integration.

    Replit is an online IDE and coding platform that supports collaborative
    development and instant deployment.

    OAuth Flow: Same as Lovable

    API Endpoints (based on Replit API docs):
    - POST /v0/repls (create Repl)
    - GET /v0/repls/{repl_id}
    """

    def __init__(self, client_id: str | None = None, client_secret: str | None = None):
        """
        Initialize Replit integration.

        Args:
            client_id: Replit OAuth client ID (from env: REPLIT_CLIENT_ID)
            client_secret: Replit OAuth client secret (from env: REPLIT_CLIENT_SECRET)
        """
        self.client_id = client_id or getattr(settings, "replit_client_id", None)
        self.client_secret = client_secret or getattr(settings, "replit_client_secret", None)
        self.api_base_url = "https://replit.com/graphql"  # Replit uses GraphQL
        self.oauth_authorize_url = "https://replit.com/auth/oauth2/authorize"
        self.oauth_token_url = "https://replit.com/auth/oauth2/token"

    def get_oauth_url(self, redirect_uri: str, state: str) -> str:
        """Generate OAuth authorization URL"""
        return (
            f"{self.oauth_authorize_url}?"
            f"client_id={self.client_id}&"
            f"redirect_uri={redirect_uri}&"
            f"response_type=code&"
            f"state={state}"
        )

    async def exchange_code_for_token(self, code: str, redirect_uri: str) -> OAuthToken:
        """Exchange OAuth code for access token"""
        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.oauth_token_url,
                data={
                    "grant_type": "authorization_code",
                    "code": code,
                    "redirect_uri": redirect_uri,
                    "client_id": self.client_id,
                    "client_secret": self.client_secret,
                },
            )
            response.raise_for_status()
            data = response.json()
            return OAuthToken(**data)

    async def create_repl(
        self,
        access_token: str,
        insight: Insight,
    ) -> BuilderProject:
        """
        Create Replit Repl from insight.

        Args:
            access_token: User's OAuth access token
            insight: Insight to build Repl from

        Returns:
            BuilderProject with Repl URL
        """
        # Replit uses GraphQL API
        mutation = """
        mutation CreateRepl($title: String!, $language: String!, $description: String!) {
          createRepl(input: {
            title: $title
            language: $language
            description: $description
          }) {
            id
            url
          }
        }
        """

        variables = {
            "title": f"StartInsight - {insight.problem_statement[:50]}",
            "language": "python",  # or nodejs, etc.
            "description": insight.problem_statement,
        }

        async with httpx.AsyncClient() as client:
            response = await client.post(
                self.api_base_url,
                headers={
                    "Authorization": f"Bearer {access_token}",
                    "Content-Type": "application/json",
                },
                json={
                    "query": mutation,
                    "variables": variables,
                },
                timeout=60.0,
            )
            response.raise_for_status()
            data = response.json()

            repl_data = data["data"]["createRepl"]

            return BuilderProject(
                platform="replit",
                project_id=repl_data["id"],
                project_url=repl_data["url"],
                status="success",
            )


# ============================================================================
# V0.DEV INTEGRATION (EXPERIMENTAL)
# ============================================================================

class V0DevIntegration:
    """
    v0.dev integration (experimental).

    v0 by Vercel is an AI-powered UI generator. As of 2026-01, there is no
    public API, so we use browser automation as a fallback.

    Approach:
    1. Use Playwright to automate v0.dev
    2. Submit prompt
    3. Wait for generation
    4. Capture generated code
    5. Store in insight.extra_metadata.v0_design
    """

    def __init__(self):
        """Initialize v0.dev integration (browser automation)"""
        self.v0_url = "https://v0.dev"

    async def generate_design(
        self,
        insight: Insight,
    ) -> BuilderProject:
        """
        Generate UI design using v0.dev (browser automation).

        NOTE: This is experimental and requires Playwright.

        Args:
            insight: Insight to generate design for

        Returns:
            BuilderProject with design code
        """
        # TODO: Implement Playwright automation
        # For now, return placeholder
        return BuilderProject(
            platform="v0",
            project_id=None,
            project_url=self.v0_url,
            status="pending",
            error="v0.dev integration requires browser automation (not yet implemented)",
        )


# ============================================================================
# UNIFIED BUILDER SERVICE
# ============================================================================

async def create_builder_project(
    platform: str,
    insight_id: UUID,
    access_token: str,
    session: AsyncSession,
) -> BuilderProject:
    """
    Create project on builder platform.

    Args:
        platform: Builder platform (lovable, replit, v0)
        insight_id: Insight ID to build from
        access_token: User's OAuth access token for platform
        session: Database session

    Returns:
        BuilderProject with project URL

    Raises:
        ValueError: If platform not supported
        httpx.HTTPStatusError: If API call fails
    """
    # Fetch insight
    stmt = select(Insight).where(Insight.id == insight_id)
    result = await session.execute(stmt)
    insight = result.scalar_one_or_none()

    if not insight:
        raise ValueError(f"Insight {insight_id} not found")

    # Route to appropriate platform
    if platform == "lovable":
        integration = LovableIntegration()
        return await integration.create_project(access_token, insight)
    elif platform == "replit":
        integration = ReplitIntegration()
        return await integration.create_repl(access_token, insight)
    elif platform == "v0":
        integration = V0DevIntegration()
        return await integration.generate_design(insight)
    else:
        raise ValueError(f"Unsupported platform: {platform}")
