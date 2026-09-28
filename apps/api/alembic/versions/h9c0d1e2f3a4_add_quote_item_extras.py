"""FC Phase 6 — quote_items.extras for ancillaries/seats.

Revision ID: h9c0d1e2f3a4
Revises: g8b9c0d1e2f3
Create Date: 2026-09-28 23:45:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "h9c0d1e2f3a4"
down_revision = "g8b9c0d1e2f3"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "quote_items",
        sa.Column(
            "extras",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[]'::jsonb"),
            nullable=False,
        ),
    )
    op.add_column(
        "quote_items",
        sa.Column("extras_total", sa.Integer(), server_default="0", nullable=False),
    )


def downgrade():
    op.drop_column("quote_items", "extras_total")
    op.drop_column("quote_items", "extras")
