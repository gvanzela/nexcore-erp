from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.sql import func
from app.core.database import Base


class Product(Base):
    """
    Product database model.

    Represents the core product entity of the system.
    Domain-agnostic and ready for ERP / e-commerce usage.
    """

    __tablename__ = "products"

    # -----------------------------------------------------
    # Primary key
    # -----------------------------------------------------
    id = Column(Integer, primary_key=True)

    # -----------------------------------------------------
    # Business identifier (unique product code)
    # Comes from legacy Cd_Produto
    # -----------------------------------------------------
    code = Column(String(50), unique=True, nullable=False)

    # -----------------------------------------------------
    # Main display name
    # Example: "ABRACADEIRA"
    # -----------------------------------------------------
    name = Column(String(255), nullable=False)

    # -----------------------------------------------------
    # Optional short name / reduced label
    # Example: shortened product description
    # -----------------------------------------------------
    short_name = Column(String(255), nullable=True)

    # -----------------------------------------------------
    # Long descriptive text
    # Comes from Ds_Texto_Explicativo (legacy)
    # Used for e-commerce, details, SEO, etc.
    # -----------------------------------------------------
    description = Column(String, nullable=False)

    # -----------------------------------------------------
    # Barcode (EAN / GTIN)
    # -----------------------------------------------------
    barcode = Column(String(50), nullable=True)

    # -----------------------------------------------------
    # Unit of measure (PC, CX, LT, etc.)
    # -----------------------------------------------------
    unit = Column(String(10), nullable=True)

    # -----------------------------------------------------
    # Soft delete flag
    # -----------------------------------------------------
    active = Column(Boolean, nullable=False, default=True)

    # -----------------------------------------------------
    # Audit fields
    # -----------------------------------------------------
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
