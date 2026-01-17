"""merge heads

Revision ID: c708b197548c
Revises: 20260117_add_legal_name_fix_pessoa, 4903c76e2835
Create Date: 2026-01-17 17:42:49.830651

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c708b197548c'
down_revision: Union[str, Sequence[str], None] = ('20260117_add_legal_name', '4903c76e2835')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
