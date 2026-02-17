"""Add soft delete fields and fix CASCADE delete relationships

Revision ID: b002
Revises: b001
Create Date: 2026-01-25 18:00:00

Security Fixes:
- Add soft delete fields to users (deleted_at, deleted_by, deletion_reason)
- Change insight_id CASCADE to SET NULL in saved_insights, user_ratings, insight_interactions
- Change user_id CASCADE to SET NULL in subscriptions (preserve payment history)
- Change user_id CASCADE to RESTRICT in custom_analyses (prevent data loss)
- Add snapshot fields for deleted insights (insight_title_snapshot, etc.)
- Add FK indexes to team invitations/sharing (invited_by_id, shared_by_id)
"""
from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

from alembic import op

# revision identifiers, used by Alembic.
revision: str = 'b002'
down_revision: str | None = 'b001'
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    """Add soft delete support and fix CASCADE relationships."""

    # ============================================================
    # PART 1: Add soft delete fields to users table
    # ============================================================

    op.add_column('users', sa.Column(
        'deleted_at',
        sa.DateTime(timezone=True),
        nullable=True,
        comment='Soft delete timestamp (NULL = active, non-NULL = deleted)'
    ))
    op.add_column('users', sa.Column(
        'deleted_by',
        postgresql.UUID(as_uuid=True),
        nullable=True,
        comment='Admin who deleted this user (audit trail)'
    ))
    op.add_column('users', sa.Column(
        'deletion_reason',
        sa.Text(),
        nullable=True,
        comment='Reason for deletion (GDPR request, ban, abuse, etc.)'
    ))

    # Add index on deleted_at for fast filtering of active users
    op.create_index(
        op.f('ix_users_deleted_at'),
        'users',
        ['deleted_at'],
        unique=False
    )

    # ============================================================
    # PART 2: Fix saved_insights CASCADE relationships
    # ============================================================

    # Drop existing foreign key constraint on insight_id
    op.drop_constraint(
        'saved_insights_insight_id_fkey',
        'saved_insights',
        type_='foreignkey'
    )

    # Make insight_id nullable
    op.alter_column(
        'saved_insights',
        'insight_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )

    # Recreate foreign key with SET NULL instead of CASCADE
    op.create_foreign_key(
        'saved_insights_insight_id_fkey',
        'saved_insights',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add snapshot fields for deleted insights
    op.add_column('saved_insights', sa.Column(
        'insight_title_snapshot',
        sa.Text(),
        nullable=True,
        comment='Snapshot of insight title (preserved after insight deletion)'
    ))
    op.add_column('saved_insights', sa.Column(
        'insight_problem_snapshot',
        sa.Text(),
        nullable=True,
        comment='Snapshot of problem statement (preserved after insight deletion)'
    ))

    # ============================================================
    # PART 3: Fix user_ratings CASCADE relationships
    # ============================================================

    # Drop existing foreign key constraint on insight_id
    op.drop_constraint(
        'user_ratings_insight_id_fkey',
        'user_ratings',
        type_='foreignkey'
    )

    # Make insight_id nullable
    op.alter_column(
        'user_ratings',
        'insight_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )

    # Recreate foreign key with SET NULL
    op.create_foreign_key(
        'user_ratings_insight_id_fkey',
        'user_ratings',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # ============================================================
    # PART 4: Fix insight_interactions CASCADE relationships
    # ============================================================

    # Drop existing foreign key constraint on insight_id
    op.drop_constraint(
        'insight_interactions_insight_id_fkey',
        'insight_interactions',
        type_='foreignkey'
    )

    # Make insight_id nullable
    op.alter_column(
        'insight_interactions',
        'insight_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )

    # Recreate foreign key with SET NULL
    op.create_foreign_key(
        'insight_interactions_insight_id_fkey',
        'insight_interactions',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # ============================================================
    # PART 5: Fix custom_analyses CASCADE to RESTRICT
    # ============================================================

    # Drop existing foreign key constraint on user_id
    op.drop_constraint(
        'custom_analyses_user_id_fkey',
        'custom_analyses',
        type_='foreignkey'
    )

    # Recreate foreign key with RESTRICT (prevent user deletion if analyses exist)
    op.create_foreign_key(
        'custom_analyses_user_id_fkey',
        'custom_analyses',
        'users',
        ['user_id'],
        ['id'],
        ondelete='RESTRICT'
    )

    # ============================================================
    # PART 6: Fix subscriptions CASCADE to SET NULL
    # ============================================================

    # Drop existing foreign key constraint on user_id
    op.drop_constraint(
        'subscriptions_user_id_fkey',
        'subscriptions',
        type_='foreignkey'
    )

    # Make user_id nullable (preserve subscription for deleted users)
    op.alter_column(
        'subscriptions',
        'user_id',
        existing_type=postgresql.UUID(),
        nullable=True
    )

    # Recreate foreign key with SET NULL (preserve payment history)
    op.create_foreign_key(
        'subscriptions_user_id_fkey',
        'subscriptions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='SET NULL'
    )

    # Add user_email_snapshot for compliance (7-10 year retention)
    op.add_column('subscriptions', sa.Column(
        'user_email_snapshot',
        sa.String(length=255),
        nullable=True,
        comment='Email snapshot for deleted users (7-10 year retention for tax/legal)'
    ))

    # ============================================================
    # PART 7: Add missing FK indexes to team tables
    # ============================================================

    # Add index to team_invitations.invited_by_id
    op.create_index(
        op.f('ix_team_invitations_invited_by_id'),
        'team_invitations',
        ['invited_by_id'],
        unique=False
    )

    # Note: team_shared_insights was a legacy table, renamed to shared_insights
    # Skip this index — table no longer exists in the schema


def downgrade() -> None:
    """Revert soft delete and CASCADE fixes."""

    # PART 7: Remove FK indexes
    op.drop_index(op.f('ix_team_invitations_invited_by_id'), table_name='team_invitations')
    # Note: ix_team_shared_insights_shared_by_id was never created (legacy table removed)

    # PART 6: Revert subscriptions changes
    op.drop_column('subscriptions', 'user_email_snapshot')

    op.drop_constraint('subscriptions_user_id_fkey', 'subscriptions', type_='foreignkey')
    op.alter_column('subscriptions', 'user_id', existing_type=postgresql.UUID(), nullable=False)
    op.create_foreign_key(
        'subscriptions_user_id_fkey',
        'subscriptions',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # PART 5: Revert custom_analyses changes
    op.drop_constraint('custom_analyses_user_id_fkey', 'custom_analyses', type_='foreignkey')
    op.create_foreign_key(
        'custom_analyses_user_id_fkey',
        'custom_analyses',
        'users',
        ['user_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # PART 4: Revert insight_interactions changes
    op.drop_constraint('insight_interactions_insight_id_fkey', 'insight_interactions', type_='foreignkey')
    op.alter_column('insight_interactions', 'insight_id', existing_type=postgresql.UUID(), nullable=False)
    op.create_foreign_key(
        'insight_interactions_insight_id_fkey',
        'insight_interactions',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # PART 3: Revert user_ratings changes
    op.drop_constraint('user_ratings_insight_id_fkey', 'user_ratings', type_='foreignkey')
    op.alter_column('user_ratings', 'insight_id', existing_type=postgresql.UUID(), nullable=False)
    op.create_foreign_key(
        'user_ratings_insight_id_fkey',
        'user_ratings',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # PART 2: Revert saved_insights changes
    op.drop_column('saved_insights', 'insight_problem_snapshot')
    op.drop_column('saved_insights', 'insight_title_snapshot')

    op.drop_constraint('saved_insights_insight_id_fkey', 'saved_insights', type_='foreignkey')
    op.alter_column('saved_insights', 'insight_id', existing_type=postgresql.UUID(), nullable=False)
    op.create_foreign_key(
        'saved_insights_insight_id_fkey',
        'saved_insights',
        'insights',
        ['insight_id'],
        ['id'],
        ondelete='CASCADE'
    )

    # PART 1: Revert users table changes
    op.drop_index(op.f('ix_users_deleted_at'), table_name='users')
    op.drop_column('users', 'deletion_reason')
    op.drop_column('users', 'deleted_by')
    op.drop_column('users', 'deleted_at')
