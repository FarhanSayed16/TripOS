"""Add notifications table.

Revision ID: k2f3a4b5c6d7
Revises: j1e2f3a4b5c6
Create Date: 2026-10-02 16:00:00.000000
"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "k2f3a4b5c6d7"
down_revision = "j1e2f3a4b5c6"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "notifications",
        sa.Column("id", sa.Uuid(), nullable=False, default=sa.text("gen_random_uuid()")),
        sa.Column("organization_id", sa.Uuid(), sa.ForeignKey("organizations.id"), nullable=False),
        sa.Column("user_id", sa.Uuid(), sa.ForeignKey("users.id"), nullable=True),
        sa.Column("type", sa.String(50), nullable=False),
        sa.Column("title", sa.String(255), nullable=False),
        sa.Column("body", sa.Text(), nullable=True),
        sa.Column("icon", sa.String(30), nullable=False, server_default="bell"),
        sa.Column("severity", sa.String(20), nullable=False, server_default="info"),
        sa.Column("link", sa.String(255), nullable=True),
        sa.Column("is_read", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_notifications_org_id", "notifications", ["organization_id"])
    op.create_index("ix_notifications_user_id", "notifications", ["user_id"])
    op.create_index("ix_notifications_type", "notifications", ["type"])
    op.create_index("ix_notifications_is_read", "notifications", ["is_read"])
    op.create_index(
        "ix_notifications_org_unread",
        "notifications",
        ["organization_id", "is_read", "created_at"],
    )


def downgrade() -> None:
    op.drop_index("ix_notifications_org_unread")
    op.drop_index("ix_notifications_is_read")
    op.drop_index("ix_notifications_type")
    op.drop_index("ix_notifications_user_id")
    op.drop_index("ix_notifications_org_id")
    op.drop_table("notifications")
