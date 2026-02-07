from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AccountReceivable(Base):
    """
    Accounts Receivable (minimal, sales-based).

    Goal:
    - Represent a single receivable generated from a confirmed sales order.
    - Keep it simple: 1 order -> 1 receivable (no installments, no partial payments).

    Design principles:
    - Mirror Accounts Payable structure for symmetry and predictability.
    - Enforce idempotency via (source_entity, source_id) unique constraint at DB level.
    - Avoid business-specific logic inside the model.
    """

    __tablename__ = "accounts_receivable"

    id = Column(Integer, primary_key=True, index=True)

    # Customer linked to the sales order
    # A Customer record with type="customer" or type="both"
    customer_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    customer = relationship("Customer")

    # Source tracking (auditable and idempotent)
    # Example: source_entity="ORDER", source_id="<order_id>"
    source_entity = Column(String, nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)

    # Financial fields
    amount = Column(Numeric(18, 4), nullable=False)
    due_date = Column(Date, nullable=False)

    # Minimal lifecycle
    # OPEN -> PAID
    status = Column(String, nullable=False, default="OPEN", index=True)

    # Standard timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
