"""add paid_at to accounts_payable

Revision ID: 31f8800e8300
Revises: 119ef2e1c0f7
Create Date: 2026-02-07 11:35:17.207681

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '31f8800e8300'
down_revision: Union[str, Sequence[str], None] = '119ef2e1c0f7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        "accounts_payable",
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_column("accounts_payable", "paid_at")
