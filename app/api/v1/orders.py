from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session, joinedload
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy import or_
from datetime import datetime

from app.core.deps import get_db
from app.models.order import Order
from app.models.order_item import OrderItem
from app.models.inventory_movement import InventoryMovement
from app.api.v1.schemas import OrderCreate, OrderResponse, OrderUpdate
from app.core.security import require_min_role
from app.models.user import User
from app.core.audit import log_action
from app.models.customer import Customer
from app.models.account_receivable import AccountReceivable

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


# Order Listing Endpoint with Filters
# imports necessários
from fastapi import Query, Depends
from sqlalchemy.orm import Session, joinedload
from sqlalchemy import or_
from datetime import datetime

from app.core.deps import get_db
from app.core.security import require_min_role
from app.models.order import Order
from app.models.customer import Customer
from app.models.user import User

# Order Listing Endpoint with Flexible Filters
@router.get("/", response_model=list[OrderResponse])
def list_orders(
    # Pagination
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),

    # Optional filters (mantidos)
    status: str | None = Query(None),
    customer_id: int | None = Query(None),
    date_from: datetime | None = Query(None),
    date_to: datetime | None = Query(None),

    # NEW: flexible customer search (UX)
    customer_search: str | None = Query(None),

    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(10)),
):
    """
    List orders with optional filters.

    - customer_id: exact (technical / internal)
    - customer_search: free text (customer name / document)
    - status: exact
    - date_from / date_to: range
    """

    # -----------------------------------------------------
    # Base query
    # - items: eager load (avoid N+1 on response)
    # - customer: eager load (needed for customer_name in response)
    # -----------------------------------------------------
    query = (
        db.query(Order)
        .options(
            joinedload(Order.items),
            joinedload(Order.customer),  # NEW
        )
    )

    # -----------------------------------------------------
    # Exact filters
    # -----------------------------------------------------
    if status is not None:
        query = query.filter(Order.status == status)

    if customer_id is not None:
        query = query.filter(Order.customer_id == customer_id)

    if date_from is not None:
        query = query.filter(Order.created_at >= date_from)

    if date_to is not None:
        query = query.filter(Order.created_at <= date_to)

    # -----------------------------------------------------
    # NEW: customer free-text search
    # - Join ONLY for filtering
    # -----------------------------------------------------
    if customer_search:
        ilike = f"%{customer_search}%"
        query = (
            query
            .join(Customer, Order.customer_id == Customer.id)
            .filter(
                or_(
                    Customer.name.ilike(ilike),
                    Customer.document.ilike(ilike),
                )
            )
        )

    # -----------------------------------------------------
    # Pagination + ordering
    # -----------------------------------------------------
    orders = (
        query
        .order_by(Order.created_at.desc())
        .offset(skip)
        .limit(limit)
        .all()
    )

    # -----------------------------------------------------
    # Inject derived field for frontend convenience
    # -----------------------------------------------------
    for order in orders:
        order.customer_name = order.customer.name if order.customer else None

    return orders





# Order Creation Endpoint
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
        # 2.1) Register stock OUT for each sold item
        # ------------------------------------------------------------
        # Business rule:
        # - Each order item generates exactly ONE inventory movement
        # - We do not calculate stock here
        # - We only register the physical event (stock leaving)

        for item in payload.items:
            movement = InventoryMovement(
                product_id=item.product_id,
                movement_type="OUT",
                # Negative quantity because stock is leaving
                quantity=-item.quantity,
                occurred_at=order.issued_at,
                # Traceability: this movement came from an order
                source_entity="order",
                source_id=str(order.id),
            )
            db.add(movement)

        # ------------------------------------------------------------
        # 2.2) Create Accounts Receivable (1 order -> 1 receivable)
        # ------------------------------------------------------------
        receivable = AccountReceivable(
            customer_id=order.customer_id,
            source_entity="ORDER",
            source_id=str(order.id),
            amount=order.total_amount,
            due_date=order.issued_at.date(),  # MVP: same day (can evolve later)
            status="OPEN",
        )
        db.add(receivable)

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


# Get Order by ID Endpoint
@router.get("/{order_id}", response_model=OrderResponse)
def get_order(
    order_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(10))
    # ROLE_USER = 10
    # ROLE_MANAGER = 50
    # ROLE_ADMIN = 100
,
):
    """
    Retrieve a single order by its ID.

    This endpoint returns:
    - order header
    - all related order items

    Used by the frontend to display order details.
    """

    # --------------------------------------------------
    # 1) Fetch order with items
    # --------------------------------------------------
    order = (
        db.query(Order)
        .options(joinedload(Order.items))
        .filter(Order.id == order_id)
        .first()
    )

    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    return order


# Order Update Endpoint
@router.patch("/{order_id}", response_model=OrderResponse)
def update_order(
    order_id: int,
    payload: OrderUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(require_min_role(10)),
    # ROLE_USER = 10
    # ROLE_MANAGER = 50
    # ROLE_ADMIN = 100

):
    """
    Partially update an existing order.

    This endpoint allows updating only specific fields
    (status, notes, active) without overwriting the entire record.
    """

    # --------------------------------------------------
    # 1) Fetch order
    # --------------------------------------------------
    order = db.query(Order).filter(Order.id == order_id).first()
    if not order:
        raise HTTPException(status_code=404, detail="Order not found")

    # --------------------------------------------------
    # 2) Extract only provided fields (PATCH semantics)
    # --------------------------------------------------
    update_data = payload.dict(exclude_unset=True)

    # --------------------------------------------------
    # 3) Apply changes dynamically
    # --------------------------------------------------
    for field, value in update_data.items():
        setattr(order, field, value)

    # --------------------------------------------------
    # 4) Persist changes
    # --------------------------------------------------
    db.commit()
    db.refresh(order)

    # --------------------------------------------------
    # 5) Audit log
    # --------------------------------------------------
    log_action(
        db=db,
        user_id=current_user.id,
        action="UPDATE_ORDER",
        resource="orders",
        resource_id=order.id,
    )

    return order
