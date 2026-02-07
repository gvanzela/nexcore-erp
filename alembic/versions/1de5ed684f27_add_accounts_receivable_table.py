"""add accounts_receivable table

Revision ID: 1de5ed684f27
Revises: 5c568c1d4b76
Create Date: 2026-02-07 15:16:53.867166

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '1de5ed684f27'
down_revision: Union[str, Sequence[str], None] = '5c568c1d4b76'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "accounts_receivable",
        sa.Column("id", sa.Integer, primary_key=True),
        sa.Column(
            "customer_id",
            sa.Integer,
            sa.ForeignKey("customers.id"),
            nullable=False,
            index=True,  # index auto-created by SQLAlchemy
        ),
        sa.Column("source_entity", sa.String(), nullable=False),
        sa.Column("source_id", sa.String(), nullable=False),
        sa.Column("amount", sa.Numeric(18, 4), nullable=False),
        sa.Column("due_date", sa.Date(), nullable=False),
        sa.Column(
            "status",
            sa.String(),
            nullable=False,
            server_default="OPEN",
            index=True,  # index auto-created by SQLAlchemy
        ),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("paid_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint(
            "source_entity",
            "source_id",
            name="uq_accounts_receivable_source",
        ),
    )


def downgrade() -> None:
    op.drop_table("accounts_receivable")
