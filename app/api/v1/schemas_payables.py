from datetime import date, datetime
from decimal import Decimal
from typing import Optional

from pydantic import BaseModel, Field


class AccountPayableCreate(BaseModel):
    """
    Minimal payload to create a payable.

    Note:
    - supplier_id must point to a Customer that is a Supplier.
    - source_entity/source_id keeps the payable traceable to the purchase.
    """
    supplier_id: int
    source_entity: str = Field(default="PURCHASE")
    source_id: str

    amount: Decimal
    due_date: date


class AccountPayableOut(BaseModel):
    id: int
    supplier_id: int
    source_entity: str
    source_id: str
    amount: Decimal
    due_date: date
    status: str
    created_at: datetime

    class Config:
        from_attributes = True
