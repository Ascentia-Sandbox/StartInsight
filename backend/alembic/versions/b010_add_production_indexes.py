"""Add production performance indexes

Revision ID: b010_add_production_indexes
Revises: b009_language_support
Create Date: 2026-01-31

Critical indexes for production performance at scale (10K+ records).
Addresses N+1 queries and full table scans on filtering/sorting columns.
"""

from sqlalchemy import text

from alembic import op

# revision identifiers, used by Alembic.
revision = 'b010_add_production_indexes'
down_revision = 'b009_language_support'
branch_labels = None
depends_on = None


def _column_exists(connection, table, column):
    """Check if a column exists in a table."""
    result = connection.execute(text(f"""
        SELECT column_name
        FROM information_schema.columns
        WHERE table_name = '{table}' AND column_name = '{column}'
    """))
    return result.fetchone() is not None


def _index_exists(connection, index_name):
    """Check if an index exists."""
    result = connection.execute(text(f"""
        SELECT indexname
        FROM pg_indexes
        WHERE indexname = '{index_name}'
    """))
    return result.fetchone() is not None


def upgrade():
    """Add critical performance indexes for production."""
    connection = op.get_bind()

    # Users table indexes
    if not _index_exists(connection, 'idx_users_subscription_tier'):
        if _column_exists(connection, 'users', 'subscription_tier'):
            op.create_index('idx_users_subscription_tier', 'users', ['subscription_tier'])

    # Email index might already exist as unique constraint
    if not _index_exists(connection, 'idx_users_email'):
        if _column_exists(connection, 'users', 'email'):
            try:
                op.create_index('idx_users_email', 'users', ['email'], unique=True)
            except Exception:
                pass  # Index might already exist from unique constraint

    if not _index_exists(connection, 'idx_users_deleted_at'):
        if _column_exists(connection, 'users', 'deleted_at'):
            op.create_index('idx_users_deleted_at', 'users', ['deleted_at'])

    # Saved insights composite index (user dashboard queries)
    if not _index_exists(connection, 'idx_saved_insights_user_status'):
        if _column_exists(connection, 'saved_insights', 'user_id') and _column_exists(connection, 'saved_insights', 'status'):
            op.create_index(
                'idx_saved_insights_user_status',
                'saved_insights',
                ['user_id', 'status']
            )

    # Insight interactions (analytics queries)
    if not _index_exists(connection, 'idx_interactions_insight_id'):
        if _column_exists(connection, 'insight_interactions', 'insight_id'):
            op.create_index('idx_interactions_insight_id', 'insight_interactions', ['insight_id'])

    if not _index_exists(connection, 'idx_interactions_type'):
        if _column_exists(connection, 'insight_interactions', 'interaction_type'):
            op.create_index('idx_interactions_type', 'insight_interactions', ['interaction_type'])

    if not _index_exists(connection, 'idx_interactions_user_id'):
        if _column_exists(connection, 'insight_interactions', 'user_id'):
            op.create_index('idx_interactions_user_id', 'insight_interactions', ['user_id'])

    # Custom analyses (user workspace)
    if not _index_exists(connection, 'idx_custom_analyses_user_id'):
        if _column_exists(connection, 'custom_analyses', 'user_id'):
            op.create_index('idx_custom_analyses_user_id', 'custom_analyses', ['user_id'])

    if not _index_exists(connection, 'idx_custom_analyses_status'):
        if _column_exists(connection, 'custom_analyses', 'status'):
            op.create_index('idx_custom_analyses_status', 'custom_analyses', ['status'])

    # Research requests (admin queue)
    if not _index_exists(connection, 'idx_research_requests_user_status'):
        if _column_exists(connection, 'research_requests', 'user_id') and _column_exists(connection, 'research_requests', 'status'):
            op.create_index(
                'idx_research_requests_user_status',
                'research_requests',
                ['user_id', 'status']
            )

    if not _index_exists(connection, 'idx_research_requests_status'):
        if _column_exists(connection, 'research_requests', 'status'):
            op.create_index('idx_research_requests_status', 'research_requests', ['status'])

    # Insights table (public listing)
    if not _index_exists(connection, 'idx_insights_created_at'):
        if _column_exists(connection, 'insights', 'created_at'):
            op.create_index('idx_insights_created_at', 'insights', ['created_at'])

    # Note: insights.source column doesn't exist in current schema
    # Skip creating idx_insights_source


def downgrade():
    """Remove production indexes."""
    connection = op.get_bind()

    for index_name in [
        'idx_insights_created_at',
        'idx_research_requests_status',
        'idx_research_requests_user_status',
        'idx_custom_analyses_status',
        'idx_custom_analyses_user_id',
        'idx_interactions_user_id',
        'idx_interactions_type',
        'idx_interactions_insight_id',
        'idx_saved_insights_user_status',
        'idx_users_deleted_at',
        'idx_users_email',
        'idx_users_subscription_tier',
    ]:
        if _index_exists(connection, index_name):
            op.drop_index(index_name)
