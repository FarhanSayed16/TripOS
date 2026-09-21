"""Add booking.organization_id + booking.supplier_code (Sprint R FIX-P36-02).

Revision ID: a2b3c4d5e6f7
Revises: f1a2b3c4d5e6
Create Date: 2026-09-19 16:10:00.000000
"""
from alembic import op
import sqlalchemy as sa

revision = "a2b3c4d5e6f7"
down_revision = "f1a2b3c4d5e6"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "bookings",
        sa.Column("organization_id", sa.UUID(), nullable=True),
    )
    op.add_column(
        "bookings",
        sa.Column("supplier_code", sa.String(length=50), nullable=True),
    )
    op.create_index("ix_bookings_organization_id", "bookings", ["organization_id"])
    op.create_index("ix_bookings_supplier_code", "bookings", ["supplier_code"])
    op.create_foreign_key(
        "fk_bookings_organization_id",
        "bookings",
        "organizations",
        ["organization_id"],
        ["id"],
    )
    # Backfill from quotes
    op.execute(
        """
        UPDATE bookings b
        SET organization_id = q.organization_id
        FROM quotes q
        WHERE b.quote_id = q.id AND b.organization_id IS NULL
        """
    )


def downgrade():
    op.drop_constraint("fk_bookings_organization_id", "bookings", type_="foreignkey")
    op.drop_index("ix_bookings_supplier_code", table_name="bookings")
    op.drop_index("ix_bookings_organization_id", table_name="bookings")
    op.drop_column("bookings", "supplier_code")
    op.drop_column("bookings", "organization_id")
