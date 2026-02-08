"""Phase 8.1: Content Quality Management

Create tables for:
- content_review_queue: AI content review with approval workflow
- content_similarity: Duplicate detection between insights

Revision ID: b012
Revises: b011_add_content_hash_to_raw_signals
Create Date: 2026-02-04
"""

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import UUID, JSONB

# revision identifiers, used by Alembic.
revision = "b012"
down_revision = "b011_content_hash"
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create content_review_queue table
    op.create_table(
        "content_review_queue",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("content_type", sa.String(50), nullable=False, comment="Type: insight, research, brand_package"),
        sa.Column("content_id", UUID(as_uuid=True), nullable=False),
        sa.Column("status", sa.String(20), server_default="pending", nullable=False, comment="pending, approved, rejected, flagged"),
        sa.Column("quality_score", sa.Numeric(3, 2), nullable=True, comment="AI-assigned score 0.00-1.00"),
        sa.Column("auto_approved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("reviewer_id", UUID(as_uuid=True), sa.ForeignKey("users.id", ondelete="SET NULL"), nullable=True),
        sa.Column("review_notes", sa.Text(), nullable=True),
        sa.Column("rejection_reason", sa.String(255), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("reviewed_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("content_type", "content_id", name="uq_content_review"),
        comment="AI content review queue with approval workflow",
    )

    # Create indexes for content_review_queue
    op.create_index("idx_review_queue_status", "content_review_queue", ["status"])
    op.create_index("idx_review_queue_type_status", "content_review_queue", ["content_type", "status"])
    op.create_index("idx_review_queue_created_at", "content_review_queue", ["created_at"])

    # Create content_similarity table
    op.create_table(
        "content_similarity",
        sa.Column("id", UUID(as_uuid=True), primary_key=True, server_default=sa.text("gen_random_uuid()")),
        sa.Column("source_insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similar_insight_id", UUID(as_uuid=True), sa.ForeignKey("insights.id", ondelete="CASCADE"), nullable=False),
        sa.Column("similarity_score", sa.Numeric(4, 3), nullable=False, comment="Cosine similarity 0.000-1.000"),
        sa.Column("similarity_type", sa.String(20), nullable=False, comment="exact, near, thematic"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("resolved", sa.Boolean(), server_default=sa.text("false"), nullable=False),
        sa.Column("resolution", sa.String(20), nullable=True, comment="keep_both, merge, delete_newer"),
        sa.UniqueConstraint("source_insight_id", "similar_insight_id", name="uq_similarity_pair"),
        comment="Tracks similar/duplicate insights for review",
    )

    # Create indexes for content_similarity
    op.create_index("idx_similarity_source", "content_similarity", ["source_insight_id"])
    op.create_index("idx_similarity_resolved", "content_similarity", ["resolved"])

    # Enable RLS on new tables
    op.execute("ALTER TABLE content_review_queue ENABLE ROW LEVEL SECURITY")
    op.execute("ALTER TABLE content_similarity ENABLE ROW LEVEL SECURITY")

    # RLS policies for content_review_queue (admin only)
    op.execute("""
        CREATE POLICY admin_content_review_policy ON content_review_queue
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM admin_users
                WHERE admin_users.user_id = auth.uid()
            )
        )
    """)

    # RLS policies for content_similarity (admin only)
    op.execute("""
        CREATE POLICY admin_content_similarity_policy ON content_similarity
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM admin_users
                WHERE admin_users.user_id = auth.uid()
            )
        )
    """)


def downgrade() -> None:
    # Drop RLS policies
    op.execute("DROP POLICY IF EXISTS admin_content_review_policy ON content_review_queue")
    op.execute("DROP POLICY IF EXISTS admin_content_similarity_policy ON content_similarity")

    # Drop tables
    op.drop_table("content_similarity")
    op.drop_table("content_review_queue")
