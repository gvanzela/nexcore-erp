"""add unique constraint to accounts_payable source

Revision ID: 5c568c1d4b76
Revises: 31f8800e8300
Create Date: 2026-02-07 13:06:39.129111

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '5c568c1d4b76'
down_revision: Union[str, Sequence[str], None] = '31f8800e8300'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_unique_constraint(
        "uq_accounts_payable_source",
        "accounts_payable",
        ["source_entity", "source_id"],
    )


def downgrade() -> None:
    op.drop_constraint(
        "uq_accounts_payable_source",
        "accounts_payable",
        type_="unique",
    )
