"""FC Phase 4 — FX rates + org/quote display currency.

Revision ID: f7a8b9c0d1e2
Revises: e6f7a8b9c0d1
Create Date: 2026-09-28 23:15:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "f7a8b9c0d1e2"
down_revision = "e6f7a8b9c0d1"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "fx_rates",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("base_currency", sa.String(length=3), nullable=False),
        sa.Column("quote_currency", sa.String(length=3), nullable=False),
        sa.Column("rate", sa.Numeric(18, 8), nullable=False),
        sa.Column("as_of", sa.DateTime(timezone=True), nullable=False),
        sa.Column("source", sa.String(length=50), nullable=False, server_default="manual"),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.UniqueConstraint("base_currency", "quote_currency", name="uq_fx_rates_pair"),
    )
    op.create_index("ix_fx_rates_quote", "fx_rates", ["quote_currency"])

    op.add_column(
        "organizations",
        sa.Column("preferred_currency", sa.String(length=3), server_default="INR", nullable=False),
    )
    op.add_column(
        "users",
        sa.Column("preferred_currency", sa.String(length=3), nullable=True),
    )

    op.add_column(
        "quotes",
        sa.Column("charge_currency", sa.String(length=3), server_default="INR", nullable=False),
    )
    op.add_column(
        "quotes",
        sa.Column("display_currency", sa.String(length=3), server_default="INR", nullable=False),
    )
    op.add_column("quotes", sa.Column("fx_rate", sa.Numeric(18, 8), nullable=True))
    op.add_column(
        "quotes",
        sa.Column("fx_as_of", sa.DateTime(timezone=True), nullable=True),
    )
    op.add_column("quotes", sa.Column("fx_source", sa.String(length=50), nullable=True))


def downgrade():
    op.drop_column("quotes", "fx_source")
    op.drop_column("quotes", "fx_as_of")
    op.drop_column("quotes", "fx_rate")
    op.drop_column("quotes", "display_currency")
    op.drop_column("quotes", "charge_currency")
    op.drop_column("users", "preferred_currency")
    op.drop_column("organizations", "preferred_currency")
    op.drop_index("ix_fx_rates_quote", table_name="fx_rates")
    op.drop_table("fx_rates")
