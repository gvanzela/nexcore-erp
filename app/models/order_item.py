from sqlalchemy import (
    Column,
    BigInteger,
    Numeric,
    ForeignKey,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class OrderItem(Base):
    """
    Core Order Item entity.

    Represents a single line item within an order.
    Contextual information about the sale lives here,
    not product definition.
    """

    __tablename__ = "order_items"

    # ------------------------------------------------------------------
    # Primary key
    # ------------------------------------------------------------------
    id = Column(
        BigInteger,
        primary_key=True,
        comment="Internal unique identifier of the order item",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    order_id = Column(
        BigInteger,
        ForeignKey("orders.id", ondelete="CASCADE"),
        nullable=False,
        comment="Parent order identifier",
    )

    product_id = Column(
        BigInteger,
        ForeignKey("products.id"),
        nullable=False,
        comment="Product being sold",
    )

    # ------------------------------------------------------------------
    # Commercial data
    # ------------------------------------------------------------------
    quantity = Column(
        Numeric(14, 4),
        nullable=False,
        comment="Quantity sold",
    )

    unit_price = Column(
        Numeric(14, 2),
        nullable=False,
        comment="Unit sale price",
    )

    discount_amount = Column(
        Numeric(14, 2),
        nullable=True,
        comment="Discount applied to this item",
    )

    total_price = Column(
        Numeric(14, 2),
        nullable=False,
        comment="Final total price for this item",
    )

    # ------------------------------------------------------------------
    # Contextual notes
    # ------------------------------------------------------------------
    notes = Column(
        Text,
        nullable=True,
        comment="Sale context notes (vehicle, plate, km, etc.)",
    )

    # ------------------------------------------------------------------
    # Relationships
    # ------------------------------------------------------------------
    order = relationship(
        "Order",
        back_populates="items",
    )
