# app/api/v1/receivables.py
# Endpoints for Accounts Receivable (sales-based)

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import or_

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.audit import log_action
from app.models.account_receivable import AccountReceivable
from app.models.customer import Customer
from app.models.user import User
from app.api.v1.schemas_receivables import ReceivableOut, ReceivablePayIn

router = APIRouter(
    prefix="/api/v1/receivables",
    tags=["receivables"],
)


# ---------------------------------------------------------------------------
# READ (LIST) Accounts Receivable with search, filters and pagination
# ---------------------------------------------------------------------------
@router.get("", response_model=list[ReceivableOut])
def list_receivables(
    search: str | None = Query(
        None,
        description="Free search by customer name, document or order reference",
    ),
    status: str | None = Query(None, description="OPEN or PAID"),
    customer_id: int | None = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve accounts receivable.

    - UX-driven search (customer name, document, order ref)
    - Optional business filters
    - Pagination enforced
    """

    # Base query:
    # We select the main entity (AccountReceivable)
    # plus an extra labeled field for UX (customer_name).
    query = (
        db.query(
            AccountReceivable,
            Customer.name.label("customer_name"),
        )
        .join(Customer, Customer.id == AccountReceivable.customer_id)
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
                AccountReceivable.source_id.ilike(like),
            )
        )

    # ------------------------------------------------------------
    # Business filters
    # ------------------------------------------------------------
    if status is not None:
        query = query.filter(AccountReceivable.status == status)

    if customer_id is not None:
        query = query.filter(AccountReceivable.customer_id == customer_id)

    # ------------------------------------------------------------
    # Pagination + deterministic ordering
    # ------------------------------------------------------------
    rows = (
        query
        .order_by(AccountReceivable.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # ------------------------------------------------------------
    # Shape response for Pydantic (enriched read-model)
    # ------------------------------------------------------------
    return [
        {
            **receivable.__dict__,
            "customer_name": customer_name,
        }
        for receivable, customer_name in rows
    ]



# Pay receivable endpoint
@router.post("/{receivable_id}/pay", response_model=ReceivableOut)
def pay_receivable(
    receivable_id: int,
    payload: ReceivablePayIn,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Mark a receivable as PAID.

    Rules:
    - Only OPEN receivables can be paid
    - paid_at is set by backend (UTC now)
    """

    receivable = (
        db.query(AccountReceivable)
        .filter(AccountReceivable.id == receivable_id)
        .first()
    )

    if not receivable:
        raise HTTPException(status_code=404, detail="Receivable not found")

    if receivable.status == "PAID":
        raise HTTPException(status_code=400, detail="Receivable already paid")

    if payload.paid:
        receivable.status = "PAID"
        receivable.paid_at = datetime.now(timezone.utc)

        db.commit()
        db.refresh(receivable)

    return receivable
