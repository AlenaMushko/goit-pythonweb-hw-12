"""add password reset token type

Revision ID: b2f6d9a4c8aa
Revises: a1c4f4be92d1
Create Date: 2026-05-08 19:58:00.000000

"""
from typing import Sequence, Union

from alembic import op


revision: str = "b2f6d9a4c8aa"
down_revision: Union[str, Sequence[str], None] = "a1c4f4be92d1"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'PASSWORD_RESET'")


def downgrade() -> None:
    """Downgrade schema."""
    pass
