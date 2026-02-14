"""API endpoints for builder ecosystem integrations (Lovable, Replit, v0)"""

import json
import logging
import secrets
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query
from fastapi.responses import RedirectResponse
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import CurrentUser
from app.core.cache import get_redis
from app.db.session import get_db
from app.models.insight import Insight
from app.services.builder_integration import (
    BuilderProject,
    LovableIntegration,
    ReplitIntegration,
    V0DevIntegration,
    create_builder_project,
)

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/build", tags=["builder-integration"])


# ============================================================================
# OAUTH STATE MANAGEMENT (Redis-backed)
# ============================================================================

OAUTH_STATE_TTL = 600  # 10 minutes


async def _store_oauth_state(state: str, data: dict) -> None:
    r = await get_redis()
    await r.setex(f"oauth_state:{state}", OAUTH_STATE_TTL, json.dumps(data))


async def _get_oauth_state(state: str) -> dict | None:
    r = await get_redis()
    data = await r.get(f"oauth_state:{state}")
    if data:
        await r.delete(f"oauth_state:{state}")
        return json.loads(data)
    return None


class DirectBuildRequest(BaseModel):
    access_token: str


# ============================================================================
# LOVABLE.DEV ENDPOINTS
# ============================================================================

@router.get("/lovable/auth")
async def lovable_oauth_start(
    insight_id: UUID,
    current_user: CurrentUser,
    redirect_uri: str = Query(..., description="OAuth callback URL"),
) -> RedirectResponse:
    """
    Start Lovable OAuth flow.

    Redirects user to Lovable for authorization.
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    await _store_oauth_state(state, {
        "platform": "lovable",
        "insight_id": str(insight_id),
        "redirect_uri": redirect_uri,
    })

    # Generate OAuth URL
    lovable = LovableIntegration()
    if not lovable.client_id:
        raise HTTPException(
            status_code=503,
            detail="Lovable OAuth not configured. Set LOVABLE_CLIENT_ID and LOVABLE_CLIENT_SECRET env vars.",
        )

    oauth_url = lovable.get_oauth_url(redirect_uri=redirect_uri, state=state)

    logger.info(f"Starting Lovable OAuth for insight {insight_id}")

    return RedirectResponse(url=oauth_url)


@router.get("/lovable/callback")
async def lovable_oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="CSRF state token"),
    db: AsyncSession = Depends(get_db),
) -> BuilderProject:
    """
    Handle Lovable OAuth callback.

    Exchanges authorization code for access token and creates project.
    """
    # Verify state (CSRF protection)
    oauth_data = await _get_oauth_state(state)
    if not oauth_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Please try again.")

    insight_id = UUID(oauth_data["insight_id"])
    redirect_uri = oauth_data["redirect_uri"]

    # Exchange code for access token
    lovable = LovableIntegration()
    try:
        token = await lovable.exchange_code_for_token(code=code, redirect_uri=redirect_uri)
    except Exception as e:
        logger.error(f"Lovable OAuth token exchange failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="OAuth token exchange failed. Please try again.")

    # Create Lovable project
    try:
        project = await create_builder_project(
            platform="lovable",
            insight_id=insight_id,
            access_token=token.access_token,
            session=db,
        )

        logger.info(f"Created Lovable project for insight {insight_id}: {project.project_url}")

        return project

    except Exception as e:
        logger.error(f"Lovable project creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/lovable")
async def create_lovable_project_direct(
    insight_id: UUID,
    body: DirectBuildRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BuilderProject:
    """
    Create Lovable project directly (for users who already have access token).
    """
    access_token = body.access_token
    try:
        project = await create_builder_project(
            platform="lovable",
            insight_id=insight_id,
            access_token=access_token,
            session=db,
        )

        logger.info(f"Created Lovable project for insight {insight_id}: {project.project_url}")

        return project

    except Exception as e:
        logger.error(f"Lovable project creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# ============================================================================
# REPLIT ENDPOINTS
# ============================================================================

@router.get("/replit/auth")
async def replit_oauth_start(
    insight_id: UUID,
    current_user: CurrentUser,
    redirect_uri: str = Query(..., description="OAuth callback URL"),
) -> RedirectResponse:
    """
    Start Replit OAuth flow.

    Redirects user to Replit for authorization.
    """
    # Generate CSRF state token
    state = secrets.token_urlsafe(32)
    await _store_oauth_state(state, {
        "platform": "replit",
        "insight_id": str(insight_id),
        "redirect_uri": redirect_uri,
    })

    # Generate OAuth URL
    replit = ReplitIntegration()
    if not replit.client_id:
        raise HTTPException(
            status_code=503,
            detail="Replit OAuth not configured. Set REPLIT_CLIENT_ID and REPLIT_CLIENT_SECRET env vars.",
        )

    oauth_url = replit.get_oauth_url(redirect_uri=redirect_uri, state=state)

    logger.info(f"Starting Replit OAuth for insight {insight_id}")

    return RedirectResponse(url=oauth_url)


@router.get("/replit/callback")
async def replit_oauth_callback(
    code: str = Query(..., description="OAuth authorization code"),
    state: str = Query(..., description="CSRF state token"),
    db: AsyncSession = Depends(get_db),
) -> BuilderProject:
    """
    Handle Replit OAuth callback.

    Exchanges authorization code for access token and creates Repl.
    """
    # Verify state (CSRF protection)
    oauth_data = await _get_oauth_state(state)
    if not oauth_data:
        raise HTTPException(status_code=400, detail="Invalid OAuth state. Please try again.")

    insight_id = UUID(oauth_data["insight_id"])
    redirect_uri = oauth_data["redirect_uri"]

    # Exchange code for access token
    replit = ReplitIntegration()
    try:
        token = await replit.exchange_code_for_token(code=code, redirect_uri=redirect_uri)
    except Exception as e:
        logger.error(f"Replit OAuth token exchange failed: {e}", exc_info=True)
        raise HTTPException(status_code=400, detail="OAuth token exchange failed. Please try again.")

    # Create Replit Repl
    try:
        project = await create_builder_project(
            platform="replit",
            insight_id=insight_id,
            access_token=token.access_token,
            session=db,
        )

        logger.info(f"Created Replit Repl for insight {insight_id}: {project.project_url}")

        return project

    except Exception as e:
        logger.error(f"Replit Repl creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


@router.post("/replit")
async def create_replit_project_direct(
    insight_id: UUID,
    body: DirectBuildRequest,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BuilderProject:
    """
    Create Replit Repl directly (for users who already have access token).
    """
    access_token = body.access_token
    try:
        project = await create_builder_project(
            platform="replit",
            insight_id=insight_id,
            access_token=access_token,
            session=db,
        )

        logger.info(f"Created Replit Repl for insight {insight_id}: {project.project_url}")

        return project

    except Exception as e:
        logger.error(f"Replit Repl creation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# ============================================================================
# V0.DEV ENDPOINTS
# ============================================================================

@router.post("/v0")
async def create_v0_design(
    insight_id: UUID,
    current_user: CurrentUser,
    db: AsyncSession = Depends(get_db),
) -> BuilderProject:
    """
    Generate UI design using v0.dev (experimental).

    NOTE: v0.dev has no public API, so this uses browser automation (Playwright).
    This is experimental and may not work reliably.

    Args:
        insight_id: Insight ID to generate design for
        db: Database session

    Returns:
        BuilderProject with v0.dev URL
    """
    try:
        project = await create_builder_project(
            platform="v0",
            insight_id=insight_id,
            access_token="",  # v0 doesn't require OAuth
            session=db,
        )

        logger.info(f"Generated v0 design for insight {insight_id}")

        return project

    except Exception as e:
        logger.error(f"v0 design generation failed: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail="An internal error occurred. Please try again.")


# ============================================================================
# UNIFIED ENDPOINT (FOR FRONTEND)
# ============================================================================

@router.get("/platforms")
async def list_builder_platforms() -> dict:
    """
    List available builder platforms and their OAuth status.

    Returns:
        Dictionary of platforms with configuration status
    """
    lovable = LovableIntegration()
    replit = ReplitIntegration()

    return {
        "platforms": [
            {
                "id": "lovable",
                "name": "Lovable",
                "description": "AI-powered full-stack app builder",
                "oauth_configured": bool(lovable.client_id and lovable.client_secret),
                "features": ["Full-stack apps", "React/Next.js", "Auto-deploy"],
            },
            {
                "id": "replit",
                "name": "Replit",
                "description": "Online IDE with collaborative coding",
                "oauth_configured": bool(replit.client_id and replit.client_secret),
                "features": ["Online IDE", "Collaborative", "Instant deploy"],
            },
            {
                "id": "v0",
                "name": "v0 by Vercel",
                "description": "AI-powered UI generator (experimental)",
                "oauth_configured": False,  # No OAuth for v0
                "features": ["UI generation", "React components", "Tailwind CSS"],
            },
        ]
    }
