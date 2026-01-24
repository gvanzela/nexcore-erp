from sqlalchemy import (
    Column,
    BigInteger,
    String,
    DateTime,
    Numeric,
    Boolean,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class Order(Base):
    """
    Core Order entity.

    Represents a business transaction header.
    This model is domain-agnostic and does NOT contain
    fiscal, payment, or logistics details.
    """

    __tablename__ = "orders"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        BigInteger,
        primary_key=True,
        comment="Internal unique identifier of the order",
    )

    # ------------------------------------------------------------------
    # Business identifiers
    # ------------------------------------------------------------------
    external_id = Column(
        String(50),
        nullable=True,
        comment="External or legacy order identifier (optional)",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    customer_id = Column(
        BigInteger,
        ForeignKey("customers.id"),
        nullable=False,
        comment="Customer who placed the order",
    )

    created_by = Column(
        BigInteger,
        ForeignKey("users.id"),
        nullable=True,
        comment="User who created the order",
    )

    # ------------------------------------------------------------------
    # Lifecycle
    # ------------------------------------------------------------------
    issued_at = Column(
        DateTime(timezone=True),
        nullable=False,
        comment="Order issue/creation datetime",
    )

    status = Column(
        String(20),
        nullable=False,
        comment="Order lifecycle status (DRAFT, OPEN, CONFIRMED, CANCELED, CLOSED)",
    )

    active = Column(
        Boolean,
        nullable=False,
        default=True,
        comment="Logical deletion flag (soft delete)",
    )

    # ------------------------------------------------------------------
    # Monetary values
    # ------------------------------------------------------------------
    total_amount = Column(
        Numeric(14, 2),
        nullable=False,
        comment="Final total amount of the order",
    )

    discount_amount = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Total discount applied to the order",
    )

    # ------------------------------------------------------------------
    # Free text
    # ------------------------------------------------------------------
    notes = Column(
        Text,
        nullable=True,
        comment="General notes or comments about the order",
    )

    # ------------------------------------------------------------------
    # Audit timestamps
    # ------------------------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
        comment="Timestamp when the order was created",
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
        comment="Timestamp when the order was last updated",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    items = relationship(
        "OrderItem",
        back_populates="order",
        cascade="all, delete-orphan",
        #comment="Items belonging to this order",
    )
