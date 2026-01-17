"""merge staging heads

Revision ID: 4903c76e2835
Revises: 20260117_add_stg_clients, f4a90b8cc8de
Create Date: 2026-01-17 17:21:59.407209

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '4903c76e2835'
down_revision: Union[str, Sequence[str], None] = ('20260117_add_stg_clients', 'f4a90b8cc8de')
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    pass


def downgrade() -> None:
    """Downgrade schema."""
    pass
