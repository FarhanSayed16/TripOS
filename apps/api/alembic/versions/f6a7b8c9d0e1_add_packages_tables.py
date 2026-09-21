"""add_packages_tables

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-09-19 00:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    # Add PackageStatus to QuoteStatus Enum (it's actually independent, wait, it's a new enum)
    # But usually Alembic doesn't auto-create ENUM if we don't define it explicitly. We'll just use VARCHAR in the table to be safe and match the other tables if they aren't using Postgres ENUMs.
    
    op.create_table('packages',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('created_by_user_id', sa.Uuid(), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('destination', sa.String(length=100), nullable=False),
        sa.Column('duration_days', sa.Integer(), nullable=False),
        sa.Column('base_price_paise', sa.Integer(), nullable=False),
        sa.Column('status', sa.String(length=20), nullable=False),
        sa.Column('cover_image_url', sa.String(), nullable=True),
        sa.Column('metadata_payload', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.Column('deleted_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['created_by_user_id'], ['users.id'], ),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_packages_organization_id'), 'packages', ['organization_id'], unique=False)

    op.create_table('package_items',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('package_id', sa.Uuid(), nullable=False),
        sa.Column('type', sa.String(length=20), nullable=False),
        sa.Column('title', sa.String(length=255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('estimated_cost_paise', sa.Integer(), nullable=False),
        sa.Column('supplier_code', sa.String(length=50), nullable=True),
        sa.Column('search_params', postgresql.JSONB(astext_type=sa.Text()), nullable=True),
        sa.Column('sort_order', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['package_id'], ['packages.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_package_items_package_id'), 'package_items', ['package_id'], unique=False)

def downgrade() -> None:
    op.drop_index(op.f('ix_package_items_package_id'), table_name='package_items')
    op.drop_table('package_items')
    op.drop_index(op.f('ix_packages_organization_id'), table_name='packages')
    op.drop_table('packages')
