from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql
import uuid

# revision identifiers
revision = "20260117_add_stg_clients"
down_revision = "20260117_add_stg_customers"
branch_labels = None
depends_on = None


def upgrade():
    op.create_table(
        "stg_clients",
        sa.Column("id", sa.BigInteger, primary_key=True),

        # Source control
        sa.Column("source_system", sa.String(50), nullable=False),
        sa.Column("legacy_empresa_id", sa.String(10), nullable=False),
        sa.Column("legacy_cliente_id", sa.String(20), nullable=False),
        sa.Column("legacy_pessoa_id", sa.String(20), nullable=False),

        # Flattened / useful fields (still raw)
        sa.Column("document", sa.String(20)),
        sa.Column("name", sa.String(120)),
        sa.Column("email", sa.String(150)),
        sa.Column("phone", sa.String(50)),
        sa.Column("status_raw", sa.String(10)),

        # Full legacy payload (CD_Cliente + CD_Pessoa)
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
        "uq_stg_clients_source_legacy",
        "stg_clients",
        ["source_system", "legacy_empresa_id", "legacy_cliente_id"],
    )

    op.create_index(
        "ix_stg_clients_document",
        "stg_clients",
        ["source_system", "document"],
    )


def downgrade():
    op.drop_index("ix_stg_clients_document", table_name="stg_clients")
    op.drop_constraint(
        "uq_stg_clients_source_legacy",
        "stg_clients",
        type_="unique",
    )
    op.drop_table("stg_clients")
