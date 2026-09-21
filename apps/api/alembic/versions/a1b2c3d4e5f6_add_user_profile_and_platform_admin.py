"""Add user profile fields and platform admin flag

Revision ID: a1b2c3d4e5f6
Revises: 6c66971123e5
Create Date: 2026-09-16 21:35:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "a1b2c3d4e5f6"
down_revision: Union[str, Sequence[str], None] = "6c66971123e5"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column("users", sa.Column("first_name", sa.String(length=100), nullable=False, server_default=""))
    op.add_column("users", sa.Column("last_name", sa.String(length=100), nullable=False, server_default=""))
    op.add_column(
        "users",
        sa.Column("is_platform_admin", sa.Boolean(), nullable=False, server_default=sa.text("false")),
    )


def downgrade() -> None:
    op.drop_column("users", "is_platform_admin")
    op.drop_column("users", "last_name")
    op.drop_column("users", "first_name")
