"""Add composite indexes

Revision ID: f1a2b3c4d5e6
Revises: e0f1a2b3c4d5
Create Date: 2026-09-19 01:00:00.000000

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision = 'f1a2b3c4d5e6'
down_revision = 'e0f1a2b3c4d5'
branch_labels = None
depends_on = None

def upgrade():
    # quotes(organization_id, status, created_at DESC)
    op.execute('CREATE INDEX IF NOT EXISTS ix_quotes_org_status_created ON quotes (organization_id, status, created_at DESC)')
    
    # jobs_outbox(status, run_at)
    op.execute('CREATE INDEX IF NOT EXISTS ix_jobs_outbox_status_run_at ON jobs_outbox (status, run_at)')
    
    # audit_events(entity_type, entity_id, created_at DESC)
    op.execute('CREATE INDEX IF NOT EXISTS ix_audit_events_entity_created ON audit_events (entity_type, entity_id, created_at DESC)')

def downgrade():
    op.execute('DROP INDEX IF EXISTS ix_quotes_org_status_created')
    op.execute('DROP INDEX IF EXISTS ix_jobs_outbox_status_run_at')
    op.execute('DROP INDEX IF EXISTS ix_audit_events_entity_created')
