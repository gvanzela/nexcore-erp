"""make user role_id not null

Revision ID: 39c41d9f095e
Revises: de06889fa625
Create Date: 2026-01-17 09:29:24.287765

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '39c41d9f095e'
down_revision: Union[str, Sequence[str], None] = 'de06889fa625'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.alter_column("users", "role_id", nullable=False)
    pass


def downgrade() -> None:
    """Downgrade schema."""
    op.alter_column("users", "role_id", nullable=True)
    pass
