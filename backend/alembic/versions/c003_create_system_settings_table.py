"""Create system_settings table with default values

Revision ID: c001
Revises: b010_add_production_indexes
Create Date: 2026-02-15

Phase G: System settings for admin portal configuration.
Stores key-value pairs grouped by category with JSONB values.
"""

import json
import uuid

import sqlalchemy as sa
from sqlalchemy import text
from sqlalchemy.dialects.postgresql import JSONB, UUID

from alembic import op

# revision identifiers, used by Alembic.
revision = 'c003'
down_revision = 'b010_add_production_indexes'
branch_labels = None
depends_on = None

# Default settings to seed
DEFAULT_SETTINGS = [
    # General
    {
        "key": "general.site_name",
        "value": "StartInsight",
        "category": "general",
        "description": "The public-facing name of the platform",
    },
    {
        "key": "general.tagline",
        "value": "AI-Powered Startup Intelligence",
        "category": "general",
        "description": "Tagline displayed on the site header and marketing pages",
    },
    # Email
    {
        "key": "email.from_address",
        "value": "noreply@startinsight.ai",
        "category": "email",
        "description": "Default sender email address for transactional emails",
    },
    {
        "key": "email.from_name",
        "value": "StartInsight",
        "category": "email",
        "description": "Display name for outgoing emails",
    },
    {
        "key": "email.digest_enabled",
        "value": True,
        "category": "email",
        "description": "Enable or disable weekly digest email sending",
    },
    # Features
    {
        "key": "features.community_voting",
        "value": True,
        "category": "features",
        "description": "Enable community voting on insights",
    },
    {
        "key": "features.gamification",
        "value": False,
        "category": "features",
        "description": "Enable gamification system (achievements, points, credits)",
    },
    {
        "key": "features.weekly_digest",
        "value": True,
        "category": "features",
        "description": "Enable weekly digest email feature for users",
    },
    # Pipeline
    {
        "key": "pipeline.scrape_interval_hours",
        "value": 6,
        "category": "pipeline",
        "description": "Hours between automated scraping runs",
    },
    {
        "key": "pipeline.analysis_batch_size",
        "value": 50,
        "category": "pipeline",
        "description": "Number of signals to process per analysis batch",
    },
    {
        "key": "pipeline.min_relevance_score",
        "value": 5.0,
        "category": "pipeline",
        "description": "Minimum relevance score (0-10) for insights to be published",
    },
    # AI
    {
        "key": "ai.default_model",
        "value": "gemini-2.0-flash",
        "category": "ai",
        "description": "Primary LLM model for AI agent tasks",
    },
    {
        "key": "ai.fallback_model",
        "value": "claude-3.5-sonnet",
        "category": "ai",
        "description": "Fallback LLM model when primary is unavailable",
    },
    {
        "key": "ai.temperature",
        "value": 0.7,
        "category": "ai",
        "description": "LLM temperature (0.0-1.0) controlling response randomness",
    },
    {
        "key": "ai.max_tokens",
        "value": 4096,
        "category": "ai",
        "description": "Maximum tokens per LLM response",
    },
]


def upgrade() -> None:
    # Create system_settings table
    op.create_table(
        'system_settings',
        sa.Column('id', UUID(as_uuid=True), primary_key=True, default=uuid.uuid4),
        sa.Column('key', sa.String(255), unique=True, index=True, nullable=False),
        sa.Column('value', JSONB, nullable=False),
        sa.Column('category', sa.String(100), index=True, nullable=False),
        sa.Column('description', sa.Text, nullable=True),
        sa.Column('updated_by', UUID(as_uuid=True), sa.ForeignKey('users.id', ondelete='SET NULL'), nullable=True),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
    )

    # Seed default settings
    conn = op.get_bind()
    for setting in DEFAULT_SETTINGS:
        conn.execute(
            text(
                """
                INSERT INTO system_settings (id, key, value, category, description, updated_at, created_at)
                VALUES (:id, :key, CAST(:value AS jsonb), :category, :description, now(), now())
                ON CONFLICT (key) DO NOTHING
                """
            ),
            {
                "id": str(uuid.uuid4()),
                "key": setting["key"],
                "value": json.dumps(setting["value"]),
                "category": setting["category"],
                "description": setting["description"],
            },
        )


def downgrade() -> None:
    op.drop_table('system_settings')
