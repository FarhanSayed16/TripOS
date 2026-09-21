"""add_follow_ups_documents

Revision ID: d9e0f1a2b3c4
Revises: c8d9e0f1a2b3
Create Date: 2026-09-19 00:45:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = 'd9e0f1a2b3c4'
down_revision: Union[str, None] = 'c8d9e0f1a2b3'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('follow_ups',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('quote_id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('message', sa.Text(), nullable=True),
        sa.Column('snoozed_until', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['quote_id'], ['quotes.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_follow_ups_organization_id'), 'follow_ups', ['organization_id'], unique=False)
    op.create_index(op.f('ix_follow_ups_quote_id'), 'follow_ups', ['quote_id'], unique=False)

    op.create_table('booking_documents',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('booking_id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('filename', sa.String(length=255), nullable=False),
        sa.Column('storage_url', sa.String(), nullable=False),
        sa.Column('mime_type', sa.String(length=100), nullable=False),
        sa.Column('uploaded_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['uploaded_by_user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_booking_documents_booking_id'), 'booking_documents', ['booking_id'], unique=False)
    op.create_index(op.f('ix_booking_documents_organization_id'), 'booking_documents', ['organization_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_booking_documents_organization_id'), table_name='booking_documents')
    op.drop_index(op.f('ix_booking_documents_booking_id'), table_name='booking_documents')
    op.drop_table('booking_documents')
    op.drop_index(op.f('ix_follow_ups_quote_id'), table_name='follow_ups')
    op.drop_index(op.f('ix_follow_ups_organization_id'), table_name='follow_ups')
    op.drop_table('follow_ups')
