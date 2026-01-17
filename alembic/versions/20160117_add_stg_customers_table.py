from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers, used by Alembic.
revision = "20260117_add_stg_customers"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stg_customers",
        sa.Column("id", sa.BigInteger, primary_key=True),

        # Source control
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("legacy_id", sa.String(50), nullable=False),

        # Raw legacy fields (no business rules)
        sa.Column("cd_empresa", sa.String(10)),
        sa.Column("document", sa.String(20)),
        sa.Column("name_razao_social", sa.String(100)),
        sa.Column("name_fantasia", sa.String(100)),
        sa.Column("email", sa.String(150)),
        sa.Column("phone", sa.String(50)),
        sa.Column("status_raw", sa.String(10)),

        # Full raw record
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
        "uq_stg_customers_source_legacy",
        "stg_customers",
        ["source_system", "legacy_id"],
    )

    op.create_index(
        "ix_stg_customers_document",
        "stg_customers",
        ["source_system", "document"],
    )


def downgrade():
    op.drop_index("ix_stg_customers_document", table_name="stg_customers")
    op.drop_constraint(
        "uq_stg_customers_source_legacy",
        "stg_customers",
        type_="unique",
    )
    op.drop_table("stg_customers")
