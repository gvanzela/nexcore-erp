"""add legal_name to customers

Revision ID: a3fc7008560d
Revises: c708b197548c
Create Date: 2026-01-17 18:33:24.894923

"""
from alembic import op
import sqlalchemy as sa

# revision identifiers
revision = "add_legal_name_customers"
down_revision = "c708b197548c"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "customers",
        sa.Column("legal_name", sa.String(255), nullable=True)
    )


def downgrade():
    op.drop_column("customers", "legal_name")

