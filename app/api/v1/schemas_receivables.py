from datetime import date, datetime
from decimal import Decimal
from pydantic import BaseModel


class ReceivableOut(BaseModel):
    """
    Read-only schema for Accounts Receivable listings.

    Used to:
    - Display receivables in screens and reports
    - Expose financial status to the frontend
    """

    id: int
    customer_id: int
    customer_name: str
    source_entity: str
    source_id: str

    amount: Decimal
    due_date: date
    status: str

    created_at: datetime
    paid_at: datetime | None

    class Config:
        from_attributes = True


class ReceivablePayIn(BaseModel):
    """
    Input schema to mark a receivable as PAID.

    MVP rules:
    - No partial payments
    - No amount override
    - Payment date is set by backend (UTC now)
    """

    paid: bool
