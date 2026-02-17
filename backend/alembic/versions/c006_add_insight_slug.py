"""add_insight_slug

Revision ID: c006
Revises: c005
Create Date: 2026-02-16 10:00:00.000000

"""
import re
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'c006'
down_revision: str | None = 'c005'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def generate_slug(title: str, max_length: int = 250) -> str:
    """Generate URL-friendly slug from title."""
    slug = title.lower()
    slug = re.sub(r"[^\w\s-]", "", slug)
    slug = re.sub(r"[\s_]+", "-", slug)
    slug = re.sub(r"-+", "-", slug).strip("-")
    return slug[:max_length]


def upgrade() -> None:
    # Add nullable slug column
    op.add_column('insights', sa.Column('slug', sa.String(250), nullable=True))

    # Populate slugs from proposed_solution
    conn = op.get_bind()
    rows = conn.execute(
        text("SELECT id, proposed_solution FROM insights WHERE slug IS NULL")
    ).fetchall()

    seen_slugs: set[str] = set()
    for row in rows:
        insight_id = row[0]
        proposed_solution = row[1] or ""
        base_slug = generate_slug(proposed_solution)
        if not base_slug:
            base_slug = str(insight_id)[:8]

        # Ensure uniqueness
        slug = base_slug
        counter = 2
        while slug in seen_slugs:
            suffix = f"-{counter}"
            slug = base_slug[:250 - len(suffix)] + suffix
            counter += 1
        seen_slugs.add(slug)

        conn.execute(
            text("UPDATE insights SET slug = :slug WHERE id = :id"),
            {"slug": slug, "id": insight_id},
        )

    # Add unique index
    op.create_index('ix_insights_slug', 'insights', ['slug'], unique=True)


def downgrade() -> None:
    op.drop_index('ix_insights_slug', table_name='insights')
    op.drop_column('insights', 'slug')
