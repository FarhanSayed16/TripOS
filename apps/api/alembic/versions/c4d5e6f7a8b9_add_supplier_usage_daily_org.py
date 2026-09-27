"""Add supplier_usage_daily_org for per-org L2B brakes (Phase 4).

Revision ID: c4d5e6f7a8b9
Revises: b3c4d5e6f7a8
Create Date: 2026-09-25 16:35:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "c4d5e6f7a8b9"
down_revision = "b3c4d5e6f7a8"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "supplier_usage_daily_org",
        sa.Column("day", sa.Date(), nullable=False),
        sa.Column("organization_id", sa.UUID(), nullable=False),
        sa.Column("supplier_code", sa.String(length=50), nullable=False),
        sa.Column("searches", sa.Integer(), server_default="0", nullable=False),
        sa.Column("revalidates", sa.Integer(), server_default="0", nullable=False),
        sa.Column("books", sa.Integer(), server_default="0", nullable=False),
        sa.Column(
            "confirmed_bookings", sa.Integer(), server_default="0", nullable=False
        ),
        sa.ForeignKeyConstraint(
            ["organization_id"],
            ["organizations.id"],
        ),
        sa.PrimaryKeyConstraint("day", "organization_id", "supplier_code"),
    )
    op.create_index(
        "ix_supplier_usage_daily_org_day",
        "supplier_usage_daily_org",
        ["day"],
    )
    op.create_index(
        "ix_supplier_usage_daily_org_org",
        "supplier_usage_daily_org",
        ["organization_id"],
    )


def downgrade():
    op.drop_index("ix_supplier_usage_daily_org_org", table_name="supplier_usage_daily_org")
    op.drop_index("ix_supplier_usage_daily_org_day", table_name="supplier_usage_daily_org")
    op.drop_table("supplier_usage_daily_org")
