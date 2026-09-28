"""FC Phase 5 — org/user locale columns.

Revision ID: g8b9c0d1e2f3
Revises: f7a8b9c0d1e2
Create Date: 2026-09-28 23:30:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "g8b9c0d1e2f3"
down_revision = "f7a8b9c0d1e2"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "organizations",
        sa.Column("default_locale", sa.String(length=8), server_default="en", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("locale", sa.String(length=8), nullable=True),
    )


def downgrade():
    op.drop_column("users", "locale")
    op.drop_column("organizations", "default_locale")
