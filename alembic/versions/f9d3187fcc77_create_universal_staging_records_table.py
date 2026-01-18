"""create universal staging records table

Revision ID: f9d3187fcc77
Revises: d54c3a068714
Create Date: 2026-01-18 14:06:43.326413

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = 'f9d3187fcc77'
down_revision: Union[str, Sequence[str], None] = 'd54c3a068714'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None




def upgrade():
    op.create_table(
        "stg_records",
        sa.Column("id", sa.BigInteger, primary_key=True),
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("source_entity", sa.String(50), nullable=False),
        sa.Column("source_pk", sa.String(100), nullable=False),
        sa.Column("raw_payload", postgresql.JSONB, nullable=False),
        sa.Column("status", sa.String(20), nullable=False, server_default="NEW"),
        sa.Column("loaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("promoted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("error_reason", sa.Text, nullable=True),
    )

    op.create_unique_constraint(
        "uq_stg_records_source",
        "stg_records",
        ["source_system", "source_entity", "source_pk"],
    )

    op.create_index("ix_stg_records_status", "stg_records", ["status"])
    op.create_index("ix_stg_records_loaded_at", "stg_records", ["loaded_at"])

def downgrade():
    op.drop_index("ix_stg_records_loaded_at", table_name="stg_records")
    op.drop_index("ix_stg_records_status", table_name="stg_records")
    op.drop_constraint("uq_stg_records_source", "stg_records", type_="unique")
    op.drop_table("stg_records")

