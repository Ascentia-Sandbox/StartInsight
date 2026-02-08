"""Add content_hash column to raw_signals for deduplication.

Revision ID: b011_content_hash
Revises: b010_add_production_indexes
Create Date: 2026-02-04

Phase: AI Agent Data Quality Improvement - Phase 3.2
Purpose: Enable content deduplication to prevent storing duplicate scraped content.
"""

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'b011_content_hash'
down_revision = 'b010_add_production_indexes'
branch_labels = None
depends_on = None


def upgrade() -> None:
    """Add content_hash column to raw_signals table."""
    # Add content_hash column (nullable for backward compatibility)
    op.add_column(
        'raw_signals',
        sa.Column(
            'content_hash',
            sa.String(64),
            nullable=True,
            comment='SHA-256 hash of content for deduplication'
        )
    )

    # Create index for fast hash lookups
    op.create_index(
        'ix_raw_signals_content_hash',
        'raw_signals',
        ['content_hash'],
        unique=True,
        postgresql_where=sa.text('content_hash IS NOT NULL')
    )

    # Backfill existing records with content hash
    # Note: This is done in a separate data migration for large tables
    # For now, we just add the column and index


def downgrade() -> None:
    """Remove content_hash column."""
    op.drop_index('ix_raw_signals_content_hash', table_name='raw_signals')
    op.drop_column('raw_signals', 'content_hash')
