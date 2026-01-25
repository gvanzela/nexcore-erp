# app/models/inventory_movement.py

from sqlalchemy import Column, Integer, String, DateTime, ForeignKey, Numeric
from sqlalchemy.sql import func
from app.core.database import Base

class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    # Internal identifier
    id = Column(Integer, primary_key=True)

    # Product affected by the movement
    product_id = Column(Integer, ForeignKey("products.id"), nullable=False)

    # Type of movement:
    # IN  = stock increase (purchase, return)
    # OUT = stock decrease (sale)
    # ADJUST = manual or inventory adjustment
    movement_type = Column(String, nullable=False)

    # Signed quantity:
    # positive = IN
    # negative = OUT
    quantity = Column(Numeric(14, 4), nullable=False)

    # Business datetime when the movement actually occurred
    occurred_at = Column(DateTime(timezone=True), nullable=False)

    # Where this movement comes from (order, purchase, adjustment, etc.)
    source_entity = Column(String, nullable=False)

    # Reference to the source record (order_id, external_id, etc.)
    source_id = Column(String, nullable=False)

    # Audit timestamp
    created_at = Column(DateTime(timezone=True), server_default=func.now())
