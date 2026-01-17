from alembic import op
import sqlalchemy as sa

revision = "20260117_add_legal_name"
down_revision = "20260117_add_stg_clients"
branch_labels = None
depends_on = None


def upgrade():
    op.add_column(
        "stg_clients",
        sa.Column("legal_name", sa.String(150))
    )

    op.alter_column(
        "stg_clients",
        "legacy_pessoa_id",
        nullable=True
    )


def downgrade():
    op.alter_column(
        "stg_clients",
        "legacy_pessoa_id",
        nullable=False
    )

    op.drop_column("stg_clients", "legal_name")
