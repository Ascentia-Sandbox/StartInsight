"""System Settings API endpoints - Admin portal configuration.

Endpoints:
- GET  /api/admin/settings/     - List all settings grouped by category
- PUT  /api/admin/settings/{key} - Update a setting value
- POST /api/admin/settings/reset - Reset all settings to defaults

All endpoints require admin authentication.
"""

import logging
import uuid
from datetime import datetime
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel
from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.deps import AdminUser
from app.db.session import get_db
from app.models.agent_control import AuditLog
from app.models.system_setting import SystemSetting

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/api/admin/settings", tags=["System Settings"])


# --------------------------------------------------------------------------
# Pydantic schemas
# --------------------------------------------------------------------------

class SettingItem(BaseModel):
    """Single setting response."""
    key: str
    value: Any
    description: str | None = None
    updated_at: datetime | None = None


class SettingsListResponse(BaseModel):
    """All settings grouped by category."""
    settings: dict[str, list[SettingItem]]


class SettingUpdateRequest(BaseModel):
    """Request body for updating a setting."""
    value: Any


class SettingUpdateResponse(BaseModel):
    """Response after updating a setting."""
    key: str
    value: Any
    updated_at: datetime


# --------------------------------------------------------------------------
# Default settings (shared with migration for reset endpoint)
# --------------------------------------------------------------------------

DEFAULT_SETTINGS: list[dict[str, Any]] = [
    {"key": "general.site_name", "value": "StartInsight", "category": "general", "description": "The public-facing name of the platform"},
    {"key": "general.tagline", "value": "AI-Powered Startup Intelligence", "category": "general", "description": "Tagline displayed on the site header and marketing pages"},
    {"key": "email.from_address", "value": "noreply@startinsight.co", "category": "email", "description": "Default sender email address for transactional emails"},
    {"key": "email.from_name", "value": "StartInsight", "category": "email", "description": "Display name for outgoing emails"},
    {"key": "email.digest_enabled", "value": True, "category": "email", "description": "Enable or disable weekly digest email sending"},
    {"key": "features.community_voting", "value": True, "category": "features", "description": "Enable community voting on insights"},
    {"key": "features.gamification", "value": False, "category": "features", "description": "Enable gamification system (achievements, points, credits)"},
    {"key": "features.weekly_digest", "value": True, "category": "features", "description": "Enable weekly digest email feature for users"},
    {"key": "pipeline.scrape_interval_hours", "value": 6, "category": "pipeline", "description": "Hours between automated scraping runs"},
    {"key": "pipeline.analysis_batch_size", "value": 50, "category": "pipeline", "description": "Number of signals to process per analysis batch"},
    {"key": "pipeline.min_relevance_score", "value": 5.0, "category": "pipeline", "description": "Minimum relevance score (0-10) for insights to be published"},
    {"key": "ai.default_model", "value": "gemini-2.0-flash", "category": "ai", "description": "Primary LLM model for AI agent tasks"},
    {"key": "ai.fallback_model", "value": "claude-3.5-sonnet", "category": "ai", "description": "Fallback LLM model when primary is unavailable"},
    {"key": "ai.temperature", "value": 0.7, "category": "ai", "description": "LLM temperature (0.0-1.0) controlling response randomness"},
    {"key": "ai.max_tokens", "value": 4096, "category": "ai", "description": "Maximum tokens per LLM response"},
    # Scraper source configuration
    {"key": "scraper.reddit.subreddits", "value": ["startups", "SaaS", "Entrepreneur", "smallbusiness", "indiehackers"], "category": "scraper", "description": "Reddit subreddits to scrape for startup signals"},
    {"key": "scraper.reddit.posts_per_sub", "value": 25, "category": "scraper", "description": "Max posts to fetch per subreddit per run"},
    {"key": "scraper.reddit.min_upvotes", "value": 10, "category": "scraper", "description": "Minimum upvotes to include a Reddit post"},
    {"key": "scraper.producthunt.categories", "value": ["Tech", "SaaS", "Artificial Intelligence", "Developer Tools", "Productivity"], "category": "scraper", "description": "Product Hunt categories to monitor"},
    {"key": "scraper.producthunt.items_per_run", "value": 30, "category": "scraper", "description": "Max products to fetch per run"},
    {"key": "scraper.hackernews.min_score", "value": 50, "category": "scraper", "description": "Minimum HN score to include a story"},
    {"key": "scraper.hackernews.max_results", "value": 30, "category": "scraper", "description": "Max stories to fetch per run"},
    {"key": "scraper.hackernews.story_types", "value": ["top", "best", "show"], "category": "scraper", "description": "HN story types to fetch (top, best, new, ask, show, job)"},
    {"key": "scraper.twitter.search_queries", "value": ["startup launch", "new SaaS", "AI startup", "indie maker"], "category": "scraper", "description": "Twitter/X search queries for startup signals"},
    {"key": "scraper.google_trends.regions", "value": ["US", "GB", "DE"], "category": "scraper", "description": "Google Trends regions to monitor"},
    {"key": "scraper.google_trends.keywords", "value": ["AI startup", "SaaS tool", "no-code", "automation"], "category": "scraper", "description": "Google Trends keywords to track"},
]


# --------------------------------------------------------------------------
# Endpoints
# --------------------------------------------------------------------------

@router.get(
    "/",
    response_model=SettingsListResponse,
    summary="List all system settings",
    description="Returns all system settings grouped by category. Requires admin role.",
)
async def list_settings(
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SettingsListResponse:
    """List all system settings grouped by category."""
    result = await db.execute(
        select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
    )
    settings = result.scalars().all()

    # Group by category
    grouped: dict[str, list[SettingItem]] = {}
    for s in settings:
        item = SettingItem(
            key=s.key,
            value=s.value,
            description=s.description,
            updated_at=s.updated_at,
        )
        grouped.setdefault(s.category, []).append(item)

    return SettingsListResponse(settings=grouped)


@router.put(
    "/{key:path}",
    response_model=SettingUpdateResponse,
    summary="Update a system setting",
    description="Update the value of a system setting by key. Logs change to audit trail. Requires admin role.",
)
async def update_setting(
    key: str,
    body: SettingUpdateRequest,
    request: Request,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SettingUpdateResponse:
    """Update a single system setting by key."""
    # Find the setting (or create if it doesn't exist)
    result = await db.execute(
        select(SystemSetting).where(SystemSetting.key == key)
    )
    setting = result.scalar_one_or_none()

    if not setting:
        # Create new setting - derive category from key prefix
        category = key.split(".")[0] if "." in key else "general"
        setting = SystemSetting(
            id=uuid.uuid4(),
            key=key,
            value=body.value,
            category=category,
            description=None,
            updated_by=admin.id,
        )
        db.add(setting)
        old_value = None
    else:
        # Capture old value for audit log
        old_value = setting.value
        setting.value = body.value
        setting.updated_by = admin.id

    # Explicit updated_at since onupdate may not fire in all drivers
    from sqlalchemy import func as sa_func
    setting.updated_at = sa_func.now()

    # Create audit log entry
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        user_id=admin.id,
        action=AuditLog.ACTION_CONFIG_CHANGE,
        resource_type="system_setting",
        resource_id=setting.id,
        details={
            "key": key,
            "old_value": old_value,
            "new_value": body.value,
        },
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(audit_entry)

    # Flush to get the updated timestamp
    await db.flush()
    await db.refresh(setting)

    logger.info(f"Admin {admin.email} updated setting '{key}': {old_value!r} -> {body.value!r}")

    return SettingUpdateResponse(
        key=setting.key,
        value=setting.value,
        updated_at=setting.updated_at,
    )


@router.post(
    "/reset",
    response_model=SettingsListResponse,
    summary="Reset all settings to defaults",
    description="Deletes all current settings and re-seeds with default values. Requires admin role.",
)
async def reset_settings(
    request: Request,
    admin: AdminUser,
    db: AsyncSession = Depends(get_db),
) -> SettingsListResponse:
    """Reset all system settings to default values."""
    # Delete all existing settings
    await db.execute(delete(SystemSetting))

    # Re-seed defaults
    for s in DEFAULT_SETTINGS:
        setting = SystemSetting(
            id=uuid.uuid4(),
            key=s["key"],
            value=s["value"],
            category=s["category"],
            description=s["description"],
            updated_by=admin.id,
        )
        db.add(setting)

    # Audit log for reset
    audit_entry = AuditLog(
        id=uuid.uuid4(),
        user_id=admin.id,
        action=AuditLog.ACTION_CONFIG_CHANGE,
        resource_type="system_setting",
        resource_id=None,
        details={"action": "reset_all_to_defaults", "setting_count": len(DEFAULT_SETTINGS)},
        ip_address=request.client.host if request.client else None,
        user_agent=request.headers.get("user-agent", "")[:500],
    )
    db.add(audit_entry)

    await db.flush()

    logger.info(f"Admin {admin.email} reset all system settings to defaults")

    # Return fresh settings grouped by category
    result = await db.execute(
        select(SystemSetting).order_by(SystemSetting.category, SystemSetting.key)
    )
    settings = result.scalars().all()

    grouped: dict[str, list[SettingItem]] = {}
    for s in settings:
        item = SettingItem(
            key=s.key,
            value=s.value,
            description=s.description,
            updated_at=s.updated_at,
        )
        grouped.setdefault(s.category, []).append(item)

    return SettingsListResponse(settings=grouped)
