"""Widen refunds table for FC Phase 2 lifecycle.

Revision ID: e6f7a8b9c0d1
Revises: d5e6f7a8b9c0
Create Date: 2026-09-28 23:00:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "e6f7a8b9c0d1"
down_revision = "d5e6f7a8b9c0"
branch_labels = None
depends_on = None


def upgrade():
    refundstatus = sa.Enum(
        "requested",
        "processing",
        "succeeded",
        "failed",
        name="refundstatus",
    )
    refundstatus.create(op.get_bind(), checkfirst=True)

    op.add_column(
        "refunds",
        sa.Column("organization_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "refunds",
        sa.Column(
            "status",
            refundstatus,
            server_default="requested",
            nullable=False,
        ),
    )
    op.add_column("refunds", sa.Column("reason", sa.String(length=100), nullable=True))
    op.add_column("refunds", sa.Column("notes", sa.Text(), nullable=True))
    op.add_column(
        "refunds",
        sa.Column("requested_by_user_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "refunds",
        sa.Column("processed_at", sa.DateTime(timezone=True), nullable=True),
    )
    op.create_foreign_key(
        "fk_refunds_organization_id",
        "refunds",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    op.create_foreign_key(
        "fk_refunds_requested_by_user_id",
        "refunds",
        "users",
        ["requested_by_user_id"],
        ["id"],
    )
    op.create_index("ix_refunds_organization_id", "refunds", ["organization_id"])
    op.create_index("ix_refunds_payment_id", "refunds", ["payment_id"])
    op.create_index("ix_refunds_status", "refunds", ["status"])


def downgrade():
    op.drop_index("ix_refunds_status", table_name="refunds")
    op.drop_index("ix_refunds_payment_id", table_name="refunds")
    op.drop_index("ix_refunds_organization_id", table_name="refunds")
    op.drop_constraint("fk_refunds_requested_by_user_id", "refunds", type_="foreignkey")
    op.drop_constraint("fk_refunds_organization_id", "refunds", type_="foreignkey")
    op.drop_column("refunds", "processed_at")
    op.drop_column("refunds", "requested_by_user_id")
    op.drop_column("refunds", "notes")
    op.drop_column("refunds", "reason")
    op.drop_column("refunds", "status")
    op.drop_column("refunds", "organization_id")
    sa.Enum(name="refundstatus").drop(op.get_bind(), checkfirst=True)
