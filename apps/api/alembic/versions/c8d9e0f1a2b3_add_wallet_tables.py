"""add_wallet_tables

Revision ID: c8d9e0f1a2b3
Revises: f6a7b8c9d0e1
Create Date: 2026-09-19 00:40:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'c8d9e0f1a2b3'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.create_table('commission_rules',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=True),
        sa.Column('product_type', sa.String(length=20), nullable=False),
        sa.Column('rule_type', sa.String(length=20), nullable=False),
        sa.Column('value', sa.Integer(), nullable=False),
        sa.Column('is_active', sa.Boolean(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )

    op.create_table('wallet_ledger',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('booking_id', sa.Uuid(), nullable=True),
        sa.Column('type', sa.String(length=30), nullable=False),
        sa.Column('amount_paise', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('settled_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['booking_id'], ['bookings.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_wallet_ledger_booking_id'), 'wallet_ledger', ['booking_id'], unique=False)
    op.create_index(op.f('ix_wallet_ledger_organization_id'), 'wallet_ledger', ['organization_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_wallet_ledger_organization_id'), table_name='wallet_ledger')
    op.drop_index(op.f('ix_wallet_ledger_booking_id'), table_name='wallet_ledger')
    op.drop_table('wallet_ledger')
    op.drop_table('commission_rules')
