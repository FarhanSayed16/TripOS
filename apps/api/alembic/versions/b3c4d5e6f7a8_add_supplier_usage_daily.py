"""Add supplier_usage_daily for L2B metering (live-inventory Phase 1).

Revision ID: b3c4d5e6f7a8
Revises: a2b3c4d5e6f7
Create Date: 2026-09-25 16:20:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "b3c4d5e6f7a8"
down_revision = "a2b3c4d5e6f7"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_usage_daily",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("supplier_code", sa.String(length=50), nullable=False),
        sa.Column("searches", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revalidates", sa.Integer(), server_default="0", nullable=False),
        sa.Column("books", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "confirmed_bookings", sa.Integer(), server_default="0", nullable=False
        ),
        sa.PrimaryKeyConstraint("day", "supplier_code"),
    )
    op.create_index(
        "ix_supplier_usage_daily_day",
        "supplier_usage_daily",
        ["day"],
    )


def downgrade():
    op.drop_index("ix_supplier_usage_daily_day", table_name="supplier_usage_daily")
    op.drop_table("supplier_usage_daily")
