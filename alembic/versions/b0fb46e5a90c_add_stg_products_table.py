"""add stg_products table

Revision ID: b0fb46e5a90c
Revises: add_legal_name_customers
Create Date: 2026-01-18 07:57:11.164106

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = "b0fb46e5a90c"
down_revision = "add_legal_name_customers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stg_products",
        sa.Column("id", sa.BigInteger, primary_key=True),

        # Source control
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("legacy_empresa_id", sa.String(10), nullable=False),
        sa.Column("legacy_product_code", sa.String(50), nullable=False),

        # Flattened useful fields
        sa.Column("code", sa.String(50)),
        sa.Column("name", sa.String(255)),
        sa.Column("short_name", sa.String(255)),
        sa.Column("description", sa.Text),
        sa.Column("barcode", sa.String(50)),
        sa.Column("unit_sale", sa.String(10)),
        sa.Column("unit_purchase", sa.String(10)),
        sa.Column("purchase_multiple", sa.Numeric(10, 2)),

        # Raw legacy payload
        sa.Column("raw_payload", postgresql.JSONB, nullable=False),

        # Import control
        sa.Column(
            "import_batch_id",
            postgresql.UUID(as_uuid=True),
            nullable=False,
            default=uuid.uuid4,
        ),
        sa.Column(
            "imported_at",
            sa.DateTime(timezone=True),
            server_default=sa.func.now(),
            nullable=False,
        ),
        sa.Column("processed_at", sa.DateTime(timezone=True)),
        sa.Column("error", sa.Text),
    )

    op.create_unique_constraint(
        "uq_stg_products_source_legacy",
        "stg_products",
        ["source_system", "legacy_empresa_id", "legacy_product_code"],
    )

    op.create_index(
        "ix_stg_products_barcode",
        "stg_products",
        ["barcode"],
    )


def downgrade():
    op.drop_index("ix_stg_products_barcode", table_name="stg_products")
    op.drop_constraint(
        "uq_stg_products_source_legacy",
        "stg_products",
        type_="unique",
    )
    op.drop_table("stg_products")
