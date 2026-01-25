"""Add webhook_events table for Stripe webhook idempotency

Revision ID: b001
Revises: 68bc7f9b5a31
Create Date: 2026-01-25 14:30:00

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b001'
down_revision: Union[str, None] = '68bc7f9b5a31'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Create webhook_events table for idempotency protection."""
    op.create_table(
        'webhook_events',
        sa.Column('id', postgresql.UUID(as_uuid=True), nullable=False),
        sa.Column('stripe_event_id', sa.String(length=255), nullable=False),
        sa.Column('event_type', sa.String(length=100), nullable=False),
        sa.Column('status', sa.String(length=50), nullable=False),
        sa.Column('payload', postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column('result', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('error_message', sa.Text(), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('processed_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('stripe_event_id', name='uq_webhook_events_stripe_event_id')
    )

    # Indexes for performance
    op.create_index(op.f('ix_webhook_events_stripe_event_id'), 'webhook_events', ['stripe_event_id'], unique=True)
    op.create_index(op.f('ix_webhook_events_event_type'), 'webhook_events', ['event_type'], unique=False)
    op.create_index(op.f('ix_webhook_events_created_at'), 'webhook_events', ['created_at'], unique=False)


def downgrade() -> None:
    """Remove webhook_events table."""
    op.drop_index(op.f('ix_webhook_events_created_at'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_event_type'), table_name='webhook_events')
    op.drop_index(op.f('ix_webhook_events_stripe_event_id'), table_name='webhook_events')
    op.drop_table('webhook_events')
