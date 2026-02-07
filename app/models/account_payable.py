from sqlalchemy import Column, Integer, String, Date, Numeric, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func

from app.core.database import Base


class AccountPayable(Base):
    """
    Accounts Payable (minimal, purchase-based).

    Goal:
    - Represent a single payable generated from a confirmed purchase (XML).
    - Keep it simple: 1 purchase -> 1 payable (no installments yet).
    """

    __tablename__ = "accounts_payable"

    id = Column(Integer, primary_key=True, index=True)

    # Supplier is a Customer record with type="Supplier" (enforced at service layer)
    supplier_id = Column(Integer, ForeignKey("customers.id"), nullable=False, index=True)
    supplier = relationship("Customer")

    # Source tracking (auditable and scalable)
    # Example: source_entity="PURCHASE", source_id="<purchase_id or xml_key>"
    source_entity = Column(String, nullable=False, index=True)
    source_id = Column(String, nullable=False, index=True)

    # Financial fields
    amount = Column(Numeric(18, 4), nullable=False)
    due_date = Column(Date, nullable=False)

    # Minimal status lifecycle
    # OPEN -> PAID (later we can add CANCELLED, PARTIAL, etc.)
    status = Column(String, nullable=False, default="OPEN", index=True)

    # Standard timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    paid_at = Column(DateTime(timezone=True), nullable=True)
