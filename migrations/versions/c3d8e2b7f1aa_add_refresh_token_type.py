"""add refresh token type

Revision ID: c3d8e2b7f1aa
Revises: b2f6d9a4c8aa
Create Date: 2026-05-08 20:15:00.000000

"""
from typing import Sequence, Union

from alembic import op


# revision identifiers, used by Alembic.
revision: str = "c3d8e2b7f1aa"
down_revision: Union[str, Sequence[str], None] = "b2f6d9a4c8aa"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.execute("ALTER TYPE tokentype ADD VALUE IF NOT EXISTS 'REFRESH'")


def downgrade() -> None:
    """Downgrade schema."""
    # PostgreSQL does not support removing enum values safely in-place.
    pass
