from pydantic import BaseModel, EmailStr
from typing import Optional
from datetime import datetime

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
    code: Optional[str] = None
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


class CustomerBase(BaseModel):
    """
    Base schema for Customer.

    Contains common fields shared across
    create, update and read operations.
    """
    name: str
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    type: str  # e.g. "customer" or "supplier"


class CustomerCreate(CustomerBase):
    """
    Schema used when creating a new customer.

    - Used by POST /api/v1/customers
    - Inherits all required fields from CustomerBase
    """


class CustomerUpdate(BaseModel):
    """
    Schema used when updating a customer.

    - Used by PATCH /api/v1/customers/{id}
    - All fields are optional
    - Designed for partial updates (exclude_unset=True)
    """
    name: Optional[str] = None
    document: Optional[str] = None
    email: Optional[EmailStr] = None
    phone: Optional[str] = None
    type: Optional[str] = None
    active: Optional[bool] = None


class CustomerOut(CustomerBase):
    """
    Schema used when returning customer data.

    - Used in response models
    - Mirrors database fields exposed to the API
    """
    id: int
    active: bool
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True