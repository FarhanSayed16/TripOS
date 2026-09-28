"""Add booking ticket refs for FC Phase 1 live spine.

Revision ID: d5e6f7a8b9c0
Revises: c4d5e6f7a8b9
Create Date: 2026-09-28 22:50:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "d5e6f7a8b9c0"
down_revision = "c4d5e6f7a8b9"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bookings",
        sa.Column("supplier_booking_id", sa.String(length=100), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("ticket_numbers", postgresql.JSONB(astext_type=sa.Text()), nullable=True),
    )


def downgrade():
    op.drop_column("bookings", "ticket_numbers")
    op.drop_column("bookings", "supplier_booking_id")
