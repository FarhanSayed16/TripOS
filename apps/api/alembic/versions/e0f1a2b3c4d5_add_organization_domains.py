"""Add OrganizationDomain

Revision ID: e0f1a2b3c4d5
Revises: d9e0f1a2b3c4
Create Date: 2026-09-19 00:56:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'e0f1a2b3c4d5'
down_revision = 'd9e0f1a2b3c4'
branch_labels = None
depends_on = None

def upgrade():
    op.create_table('organization_domains',
        sa.Column('id', sa.Uuid(), nullable=False),
        sa.Column('organization_id', sa.Uuid(), nullable=False),
        sa.Column('domain', sa.String(length=255), nullable=False),
        sa.Column('is_verified', sa.Boolean(), nullable=False, server_default='false'),
        sa.Column('verification_token', sa.String(length=100), nullable=True),
        sa.Column('created_at', sa.DateTime(timezone=True), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), nullable=False),
        sa.ForeignKeyConstraint(['organization_id'], ['organizations.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_organization_domains_domain'), 'organization_domains', ['domain'], unique=True)
    op.create_index(op.f('ix_organization_domains_organization_id'), 'organization_domains', ['organization_id'], unique=False)

def downgrade():
    op.drop_index(op.f('ix_organization_domains_organization_id'), table_name='organization_domains')
    op.drop_index(op.f('ix_organization_domains_domain'), table_name='organization_domains')
    op.drop_table('organization_domains')
