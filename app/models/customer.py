# app/models/customer.py

from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Customer(Base):
    """
    Generic party entity.

    Used for:
    - Customers
    - Suppliers

    Domain-agnostic.
    """

    __tablename__ = "customers"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Legal or display name
    name = Column(String(255), nullable=False)

    # CPF / CNPJ / any external identifier
    document = Column(String(50), unique=True, nullable=True)

    # Contact info
    email = Column(String(255), nullable=True)
    phone = Column(String(50), nullable=True)

    # Party type: 'customer' or 'supplier'
    type = Column(String(20), nullable=False)

    # Soft delete flag
    active = Column(Boolean, nullable=False, default=True)

    # Timestamps
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
