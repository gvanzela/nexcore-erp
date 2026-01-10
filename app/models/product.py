from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import declarative_base

# Base class for all SQLAlchemy models
# It stores metadata about tables and mappings
Base = declarative_base()

class Product(Base):
    """
    Product database model.

    Represents the core product entity of the system.
    Each instance maps directly to a row in the 'products' table.
    """
    __tablename__ = "products"

    # Primary key identifier
    id = Column(Integer, primary_key=True)

    # Business identifier (unique product code)
    code = Column(String, unique=True, nullable=False)

    # Human-readable product description
    description = Column(String, nullable=False)

    # Logical flag to enable/disable the product
    active = Column(Boolean, default=True)
