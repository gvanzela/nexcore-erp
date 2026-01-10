from pydantic import BaseModel
from typing import Optional

# =========================
# Product Schemas
# =========================

class ProductCreate(BaseModel):
    """
    Schema used when creating a new product.

    - Required fields only
    - Used by POST /api/v1/products
    """
    code: str
    description: str


class ProductUpdate(BaseModel):
    """
    Schema used for partial updates (PATCH).

    - All fields are optional
    - Only provided fields will be updated
    """
    description: Optional[str] = None
    active: Optional[bool] = None


class ProductOut(BaseModel):
    """
    Schema used in API responses.

    - Represents how Product is exposed externally
    - Hides internal ORM details
    """
    id: int
    code: str
    description: str
    active: bool

    class Config:
        # Allows returning SQLAlchemy ORM objects directly
        from_attributes = True
