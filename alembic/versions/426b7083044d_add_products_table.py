"""add products table

Revision ID: 426b7083044d
Revises: b0fb46e5a90c
Create Date: 2026-01-18 08:50:17.790492

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '426b7083044d'
down_revision: Union[str, Sequence[str], None] = 'b0fb46e5a90c'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
