"""FC Phase 8 — partner apps + webhook delivery log.

Revision ID: j1e2f3a4b5c6
Revises: i0d1e2f3a4b5
Create Date: 2026-09-28 23:59:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "j1e2f3a4b5c6"
down_revision = "i0d1e2f3a4b5"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "partner_apps",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "organization_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("organizations.id"),
            nullable=False,
            index=True,
        ),
        sa.Column(
            "service_user_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("users.id"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=120), nullable=False),
        sa.Column("key_prefix", sa.String(length=16), nullable=False, unique=True, index=True),
        sa.Column("key_hash", sa.String(length=64), nullable=False),
        sa.Column("env", sa.String(length=16), server_default="test", nullable=False),
        sa.Column("webhook_url", sa.String(length=500), nullable=True),
        sa.Column("webhook_secret", sa.String(length=128), nullable=True),
        sa.Column(
            "scopes",
            postgresql.JSONB(astext_type=sa.Text()),
            server_default=sa.text("'[\"search\",\"quote\",\"pay\",\"booking\"]'::jsonb"),
            nullable=False,
        ),
        sa.Column("rate_limit_per_minute", sa.Integer(), server_default="60", nullable=False),
        sa.Column(
            "ip_allowlist",
            postgresql.JSONB(astext_type=sa.Text()),
            nullable=True,
        ),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true"), nullable=False),
        sa.Column("last_used_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("rotated_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("deleted_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "partner_webhook_deliveries",
        sa.Column("id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column(
            "partner_app_id",
            postgresql.UUID(as_uuid=True),
            sa.ForeignKey("partner_apps.id"),
            nullable=False,
            index=True,
        ),
        sa.Column("event_type", sa.String(length=64), nullable=False, index=True),
        sa.Column("payload", postgresql.JSONB(astext_type=sa.Text()), nullable=False),
        sa.Column("status", sa.String(length=24), server_default="pending", nullable=False),
        sa.Column("attempts", sa.Integer(), server_default="0", nullable=False),
        sa.Column("http_status", sa.Integer(), nullable=True),
        sa.Column("last_error", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
    )


def downgrade():
    op.drop_table("partner_webhook_deliveries")
    op.drop_table("partner_apps")
