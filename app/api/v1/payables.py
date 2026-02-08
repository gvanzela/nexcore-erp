from typing import List, Optional
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.models.account_payable import AccountPayable
from app.models.customer import Customer
from app.api.v1.schemas_payables import AccountPayableCreate, AccountPayableOut

router = APIRouter(prefix="/api/v1/payables", tags=["payables"])


# ---------------------------------------------------------------------------
# CREATE (minimal)
# ---------------------------------------------------------------------------
@router.post("", response_model=AccountPayableOut)
def create_payable(
    payload: AccountPayableCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a payable (purchase-based).

    Why:
    - Close the real flow: purchase -> stock -> finance.
    - Keep it simple: 1 purchase confirmed -> 1 payable OPEN.
    """

    # Ensure supplier exists and is of type Supplier (simple guard)
    supplier = db.query(Customer).filter(Customer.id == payload.supplier_id).first()
    if not supplier:
        raise HTTPException(status_code=404, detail="Supplier not found")

    if str(getattr(supplier, "type", "")).lower() != "supplier":
        raise HTTPException(status_code=400, detail="Customer is not a Supplier")

    payable = AccountPayable(
        supplier_id=payload.supplier_id,
        source_entity=payload.source_entity,
        source_id=payload.source_id,
        amount=payload.amount,
        due_date=payload.due_date,
        status="OPEN",
    )

    db.add(payable)
    db.commit()
    db.refresh(payable)
    return payable


# ---------------------------------------------------------------------------
# READ (LIST) with filters (minimal)
# ---------------------------------------------------------------------------
@router.get("", response_model=List[AccountPayableOut])
def list_payables(
    search: Optional[str] = Query(
        None,
        description="Free search by supplier name, document or purchase reference",
    ),
    status: Optional[str] = Query(None, description="OPEN or PAID"),
    supplier_id: Optional[int] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List accounts payable.

    Design:
    - UX-driven free search
    - Optional business filters
    - Pagination enforced
    """

    # Base query:
    # We select AccountPayable + supplier name for UX.
    query = (
        db.query(
            AccountPayable,
            Customer.name.label("supplier_name"),
        )
        .join(Customer, Customer.id == AccountPayable.supplier_id)
    )

    # ------------------------------------------------------------
    # Free text search (UX-first)
    # ------------------------------------------------------------
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Customer.name.ilike(like),
                Customer.document.ilike(like),
                AccountPayable.source_id.ilike(like),
            )
        )

    # ------------------------------------------------------------
    # Business filters
    # ------------------------------------------------------------
    if status is not None:
        query = query.filter(AccountPayable.status == status)

    if supplier_id is not None:
        query = query.filter(AccountPayable.supplier_id == supplier_id)

    # ------------------------------------------------------------
    # Pagination + deterministic ordering
    # ------------------------------------------------------------
    rows = (
        query
        .order_by(AccountPayable.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # ------------------------------------------------------------
    # Shape enriched response
    # ------------------------------------------------------------
    return [
        {
            **payable.__dict__,
            "supplier_name": supplier_name,
        }
        for payable, supplier_name in rows
    ]


# ---------------------------------------------------------------------------
# PAY Accounts Payable
# ---------------------------------------------------------------------------
@router.post("/{payable_id}/pay", response_model=AccountPayableOut)
def pay_payable(
    payable_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark an accounts payable as PAID.

    MVP:
    - Full payment only
    - No installments
    """

    payable = db.get(AccountPayable, payable_id)
    if not payable:
        raise HTTPException(status_code=404, detail="Payable not found")

    if payable.status == "PAID":
        raise HTTPException(status_code=400, detail="Payable already paid")

    payable.status = "PAID"
    payable.paid_at = datetime.now(timezone.utc)

    db.commit()
    db.refresh(payable)
    return payable