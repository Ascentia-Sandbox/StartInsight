"""add language support for APAC multi-language

Revision ID: b009_language_support
Revises: b008_market_insights
Create Date: 2026-01-30 10:00:00.000000

Phase 15.1: APAC Market Penetration - Multi-language foundation
Adds language support columns to users, insights, and public content tables
"""

from typing import Sequence, Union

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = "b009_language_support"
down_revision: Union[str, None] = "b008_market_insights"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Add language support columns for multi-language APAC content."""

    # 1. Add language column to users table
    op.add_column(
        "users",
        sa.Column(
            "language",
            sa.String(length=10),
            nullable=False,
            server_default=sa.text("'en'"),
            doc="User's preferred language (ISO 639-1 + region): en, zh-CN, id-ID, vi-VN, th-TH, tl-PH",
        ),
    )
    op.create_index("ix_users_language", "users", ["language"])

    # 2. Add language columns to insights table
    op.add_column(
        "insights",
        sa.Column(
            "language",
            sa.String(length=10),
            nullable=False,
            server_default=sa.text("'en'"),
            doc="Language of the insight content",
        ),
    )
    op.add_column(
        "insights",
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            doc="Translations in other languages: {zh-CN: {problem_statement: ..., proposed_solution: ...}}",
        ),
    )
    op.create_index("ix_insights_language", "insights", ["language"])

    # 3. Add translations column to tools table
    op.add_column(
        "tools",
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            doc="Translations: {zh-CN: {name: ..., tagline: ..., description: ...}}",
        ),
    )

    # 4. Add translations column to success_stories table
    op.add_column(
        "success_stories",
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            doc="Translations: {zh-CN: {company_name: ..., tagline: ..., journey_narrative: ...}}",
        ),
    )

    # 5. Add translations column to trends table
    op.add_column(
        "trends",
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            doc="Translations: {zh-CN: {keyword: ..., business_implications: ...}}",
        ),
    )

    # 6. Add translations column to market_insights table
    op.add_column(
        "market_insights",
        sa.Column(
            "translations",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
            server_default=sa.text("'{}'::jsonb"),
            doc="Translations: {zh-CN: {title: ..., summary: ..., content: ...}}",
        ),
    )

    # Add comment to insights table for translation structure documentation
    op.execute("""
        COMMENT ON COLUMN insights.translations IS
        'Translation structure: {
            "zh-CN": {
                "problem_statement": "问题描述...",
                "proposed_solution": "解决方案...",
                "market_gap_analysis": "市场差距分析...",
                "why_now_analysis": "时机分析..."
            },
            "id-ID": {...},
            "vi-VN": {...},
            "th-TH": {...},
            "tl-PH": {...}
        }'
    """)


def downgrade() -> None:
    """Remove language support columns."""

    # Remove columns from users table
    op.drop_index("ix_users_language", table_name="users")
    op.drop_column("users", "language")

    # Remove columns from insights table
    op.drop_index("ix_insights_language", table_name="insights")
    op.drop_column("insights", "translations")
    op.drop_column("insights", "language")

    # Remove translations columns from content tables
    op.drop_column("tools", "translations")
    op.drop_column("success_stories", "translations")
    op.drop_column("trends", "translations")
    op.drop_column("market_insights", "translations")
