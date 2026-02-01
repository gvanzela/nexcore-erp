"""add manufacturer_code to products

Revision ID: b1b2e7356cb6
Revises: ec08b148b5e1
Create Date: 2026-01-31 13:08:34.135197

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'b1b2e7356cb6'
down_revision: Union[str, Sequence[str], None] = 'ec08b148b5e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None

def upgrade() -> None:
    op.add_column(
        "products",
        sa.Column("manufacturer_code", sa.String(length=50), nullable=True)
    )


def downgrade() -> None:
    op.drop_column("products", "manufacturer_code")

