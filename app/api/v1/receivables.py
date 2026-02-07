# app/api/v1/receivables.py
# Endpoints for Accounts Receivable (sales-based)

from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session

from app.core.deps import get_db
from app.models.account_receivable import AccountReceivable
from app.api.v1.schemas_receivables import ReceivableOut, ReceivablePayIn

router = APIRouter(
    prefix="/api/v1/receivables",
    tags=["receivables"],
)


@router.get("/", response_model=list[ReceivableOut])
def list_receivables(
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    db: Session = Depends(get_db),
):
    """
    List accounts receivable.

    Optional filters:
    - status (OPEN / PAID)
    - customer_id
    """

    query = db.query(AccountReceivable)

    if status:
        query = query.filter(AccountReceivable.status == status)

    if customer_id:
        query = query.filter(AccountReceivable.customer_id == customer_id)

    return query.order_by(AccountReceivable.created_at.desc()).all()


@router.post("/{receivable_id}/pay", response_model=ReceivableOut)
def pay_receivable(
    receivable_id: int,
    payload: ReceivablePayIn,
    db: Session = Depends(get_db),
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
