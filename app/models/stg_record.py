from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    Text,
    UniqueConstraint,
    Index,
)
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func

from app.core.database import Base


class StgRecord(Base):
    """
    Universal staging record.

    This table is NOT a domain model.
    It is an ingestion buffer that isolates raw external data
    (legacy systems, client databases, files, APIs) from the core domain.

    Each row represents ONE external record, in its original shape.
    """

    __tablename__ = "stg_records"

    # ------------------------------------------------------------------
    # Technical primary key (internal only)
    # ------------------------------------------------------------------
    id = Column(
        BigInteger,
        primary_key=True,
        comment="Internal surrogate key for the staging record",
    )

    # ------------------------------------------------------------------
    # Source identification
    # These fields define WHERE the data came from
    # ------------------------------------------------------------------
    source_system = Column(
        String(50),
        nullable=False,
        comment="Identifier of the external system (e.g. cmsys, sap, oracle)",
    )

    source_entity = Column(
        String(50),
        nullable=False,
        comment="Logical entity name in the source system (e.g. product, client)",
    )

    source_pk = Column(
        String(100),
        nullable=False,
        comment="Primary key of the record in the source system (string for flexibility)",
    )

    # ------------------------------------------------------------------
    # Raw data payload
    # This is the FULL original record, unmodified
    # ------------------------------------------------------------------
    raw_payload = Column(
        JSONB,
        nullable=False,
        comment="Raw source record stored as JSONB, exactly as received",
    )

    # ------------------------------------------------------------------
    # Processing lifecycle
    # Controls promotion into the core domain
    # ------------------------------------------------------------------
    status = Column(
        String(20),
        nullable=False,
        default="NEW",
        comment="Processing state: NEW | VALID | PROMOTED | ERROR",
    )

    loaded_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the record was ingested into staging",
    )

    promoted_at = Column(
        DateTime(timezone=True),
        nullable=True,
        comment="Timestamp when the record was successfully promoted to core",
    )

    error_reason = Column(
        Text,
        nullable=True,
        comment="Error description if validation or promotion fails",
    )

    # ------------------------------------------------------------------
    # Constraints & indexes
    # ------------------------------------------------------------------
    __table_args__ = (
        # Idempotency guarantee:
        # the same external record cannot be ingested twice
        UniqueConstraint(
            "source_system",
            "source_entity",
            "source_pk",
            name="uq_stg_records_source",
        ),

        # Query helpers for ETL pipelines
        Index("ix_stg_records_status", "status"),
        Index("ix_stg_records_loaded_at", "loaded_at"),
    )
