"""align products schema

Revision ID: d54c3a068714
Revises: 426b7083044d
Create Date: 2026-01-18 09:04:55.678777

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd54c3a068714'
down_revision: Union[str, Sequence[str], None] = '426b7083044d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade():
    # 1) Add columns as NULLABLE (table already has data)
    op.add_column("products", sa.Column("name", sa.String(255), nullable=True))
    op.add_column("products", sa.Column("short_name", sa.String(255)))
    op.add_column("products", sa.Column("barcode", sa.String(50)))
    op.add_column("products", sa.Column("unit", sa.String(10)))

    # 2) Backfill name from existing description
    op.execute("""
        UPDATE products
        SET name = description
        WHERE name IS NULL
    """)

    # 3) Enforce NOT NULL after data is safe
    op.alter_column("products", "name", nullable=False)


def downgrade():
    # Minimal safe rollback
    op.drop_column("products", "unit")
    op.drop_column("products", "barcode")
    op.drop_column("products", "short_name")
    op.drop_column("products", "name")