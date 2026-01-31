from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List
from datetime import datetime
from decimal import Decimal

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
    manufacturer_code: Optional[str] = None


class ProductUpdate(BaseModel):
    """
    Schema used for partial updates (PATCH).

    - All fields are optional
    - Only provided fields will be updated
    """
    code: Optional[str] = None
    description: Optional[str] = None
    manufacturer_code: Optional[str] = None
    active: Optional[bool] = None


class ProductOut(BaseModel):
    """
    Schema used in API responses.

    - Represents how Product is exposed externally
    - Hides internal ORM details
    """
    id: int
    code: str
    manufacturer_code: Optional[str] = None
    name: str
    short_name: str
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


# ============================================================
# Order Items
# ============================================================

class OrderItemCreate(BaseModel):
    product_id: int = Field(..., description="Product identifier")
    quantity: Decimal = Field(..., gt=0, description="Quantity sold")
    unit_price: Decimal = Field(..., ge=0, description="Unit sale price")
    discount_amount: Optional[Decimal] = Field(None, description="Discount applied to this item")
    total_price: Decimal = Field(..., ge=0, description="Final total price for this item")
    notes: Optional[str] = Field(None, description="Contextual sale notes (vehicle, plate, km, etc.)")


class OrderItemResponse(OrderItemCreate):
    id: int

    class Config:
        from_attributes = True


# ============================================================
# Orders
# ============================================================

class OrderCreate(BaseModel):
    external_id: Optional[str] = Field(None, description="External or legacy order identifier")
    customer_id: int = Field(..., description="Customer who placed the order")
    issued_at: datetime = Field(..., description="Order issue datetime")
    status: str = Field(..., description="Order status (DRAFT, OPEN, CONFIRMED, CANCELED, CLOSED)")
    total_amount: Decimal = Field(..., ge=0, description="Final total amount of the order")
    discount_amount: Optional[Decimal] = Field(None, ge=0, description="Total discount applied to the order")
    notes: Optional[str] = Field(None, description="General order notes")
    items: List[OrderItemCreate] = Field(..., min_items=1, description="Order items")


class OrderUpdate(BaseModel):
    status: Optional[str] = Field(None, description="Updated order status")
    notes: Optional[str] = Field(None, description="Updated order notes")
    active: Optional[bool] = Field(None, description="Logical deletion flag")


class OrderResponse(BaseModel):
    id: int
    external_id: Optional[str]
    customer_id: int
    issued_at: datetime
    status: str
    total_amount: Decimal
    discount_amount: Optional[Decimal]
    notes: Optional[str]
    active: bool
    created_at: datetime
    updated_at: datetime
    items: List[OrderItemResponse]

    class Config:
        from_attributes = True
