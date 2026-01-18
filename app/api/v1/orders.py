from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError

from app.core.deps import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.api.v1.schemas import OrderCreate, OrderResponse

# router = APIRouter(prefix="/orders", tags=["Orders"])


# ============================================================================
# Orders Router
# ============================================================================
# This router exposes CRUD endpoints for the Product entity.
# It represents the first core domain of the system.
# All routes are versioned under /api/v1/orders
# ============================================================================

router = APIRouter(
    prefix="/api/v1/orders",
    tags=["Orders"]
)


@router.post("/", response_model=OrderResponse, status_code=status.HTTP_201_CREATED)
def create_order(payload: OrderCreate, db: Session = Depends(get_db)):
    """
    Create an Order + its OrderItems atomically.

    Why this matters:
    - Orders and items are a single aggregate: saving one without the other is invalid.
    - We must guarantee consistency: either everything is persisted, or nothing is.

    Notes:
    - This endpoint is CORE-only: no legacy fields, no staging awareness.
    - Validation is assumed to be handled by Pydantic schemas + DB constraints.
    """

    try:
        # ------------------------------------------------------------
        # 1) Create the order header (aggregate root)
        # ------------------------------------------------------------
        order = Order(
            external_id=payload.external_id,
            customer_id=payload.customer_id,
            issued_at=payload.issued_at,
            status=payload.status,
            total_amount=payload.total_amount,
            discount_amount=payload.discount_amount,
            notes=payload.notes,
        )

        # Add to session but do NOT commit yet (we want atomic behavior)
        db.add(order)

        # Flush sends pending INSERTs to the DB so we get order.id
        # without ending the transaction.
        db.flush()

        # ------------------------------------------------------------
        # 2) Create all items referencing the new order.id
        # ------------------------------------------------------------
        for item in payload.items:
            order_item = OrderItem(
                order_id=order.id,               # link item -> order
                product_id=item.product_id,      # product being sold
                quantity=item.quantity,          # quantity
                unit_price=item.unit_price,      # unit price
                discount_amount=item.discount_amount,
                total_price=item.total_price,    # final line total
                notes=item.notes,                # contextual sale notes (optional)
            )
            db.add(order_item)

        # ------------------------------------------------------------
        # 3) Commit once: atomic persistence (order + items)
        # ------------------------------------------------------------
        db.commit()

        # Refresh ensures the returned object has DB-populated fields
        # such as created_at/updated_at (server defaults).
        db.refresh(order)

        # Returning the ORM object works because OrderResponse uses from_attributes=True
        return order

    except SQLAlchemyError:
        # Any DB error must roll back the entire transaction.
        db.rollback()

        # Generic 500: we don't leak internals to API clients.
        raise HTTPException(
            status_code=500,
            detail="Failed to create order",
        )
