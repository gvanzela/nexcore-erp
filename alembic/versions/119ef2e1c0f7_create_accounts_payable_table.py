"""create accounts_payable table

Revision ID: 119ef2e1c0f7
Revises: b1b2e7356cb6
Create Date: 2026-02-07 08:26:24.231529

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = '119ef2e1c0f7'
down_revision: Union[str, Sequence[str], None] = 'b1b2e7356cb6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.create_table(
        "accounts_payable",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("supplier_id", sa.Integer(), sa.ForeignKey("customers.id"), nullable=False),
        sa.Column("source_entity", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column("status", sa.String(), nullable=False, server_default="OPEN"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
    )
    op.create_index("ix_accounts_payable_supplier_id", "accounts_payable", ["supplier_id"])
    op.create_index("ix_accounts_payable_source", "accounts_payable", ["source_entity", "source_id"])
    op.create_index("ix_accounts_payable_status", "accounts_payable", ["status"])


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index("ix_accounts_payable_status", table_name="accounts_payable")
    op.drop_index("ix_accounts_payable_source", table_name="accounts_payable")
    op.drop_index("ix_accounts_payable_supplier_id", table_name="accounts_payable")
    op.drop_table("accounts_payable")
