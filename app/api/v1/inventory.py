# app/api/v1/inventory.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func
from datetime import datetime, timezone

from app.core.deps import get_db
from app.models.inventory_movement import InventoryMovement

from datetime import date
from typing import Optional
from sqlalchemy import or_
from app.models.product import Product

# Router for inventory-related endpoints
router = APIRouter(
    prefix="/api/v1/inventory", 
    tags=["inventory"]
)

# Inventory Stock Balance Endpoint for a Product
@router.get("/product/{product_id}")
def get_stock_balance(
    product_id: int,
    db: Session = Depends(get_db),
):
    """
    Read-only stock balance for a single product.

    Stock is computed as the sum of inventory movements.
    """

    balance = (
        db.query(func.coalesce(func.sum(InventoryMovement.quantity), 0))
        .filter(InventoryMovement.product_id == product_id)
        .scalar()
    )

    product = db.query(Product).get(product_id)

    return {
        "product_id": product_id,
        "product_name": product.name if product else None,
        "manufacturer_code": product.manufacturer_code if product else None,
        "balance": balance,
    }



# Inventory Stock Listing Endpoint
@router.get("/")
def list_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List current stock balance for all products.

    Stock is computed, never stored.
    """

    rows = (
        db.query(
            Product.id,
            Product.name,
            Product.manufacturer_code,
            func.coalesce(func.sum(InventoryMovement.quantity), 0).label("balance"),
        )
        .join(InventoryMovement, InventoryMovement.product_id == Product.id)
        .group_by(Product.id, Product.name, Product.manufacturer_code)
        .order_by(Product.name)
        .offset(skip)
        .limit(limit)
        .all()
    )

    return [
        {
            "product_id": product_id,
            "product_name": name,
            "manufacturer_code": manufacturer_code,
            "balance": balance,
        }
        for product_id, name, manufacturer_code, balance in rows
    ]



# ---------------------------------------------------------------------------
# READ (LIST) Inventory Movements with filters and search
# ---------------------------------------------------------------------------
@router.get("/movements")
def list_inventory_movements(
    search: Optional[str] = Query(
        None, description="Search by product name, code or barcode"
    ),
    product_id: Optional[int] = Query(None),
    movement_type: Optional[str] = Query(
        None, description="IN, OUT or ADJUST"
    ),
    date_from: Optional[date] = Query(None),
    date_to: Optional[date] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """
    List inventory movements (audit view).

    This endpoint returns raw inventory movements.
    It does NOT calculate stock balances.
    """

    # Explicitly select both entities (no ORM relationship required)
    query = (
        db.query(InventoryMovement, Product)
        .join(Product, Product.id == InventoryMovement.product_id)
    )

    # Free text search on product fields (UX-driven)
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(like),
                Product.code.ilike(like),
                Product.barcode.ilike(like),
                Product.manufacturer_code.ilike(like),
            )
        )

    # Filter by product
    if product_id is not None:
        query = query.filter(InventoryMovement.product_id == product_id)

    # Filter by movement type (IN / OUT / ADJUST)
    if movement_type is not None:
        query = query.filter(InventoryMovement.movement_type == movement_type)

    # Date range filters
    if date_from is not None:
        query = query.filter(InventoryMovement.created_at >= date_from)

    if date_to is not None:
        query = query.filter(InventoryMovement.created_at <= date_to)

    # Order by most recent movements first
    query = query.order_by(InventoryMovement.created_at.desc())

    rows = query.offset(skip).limit(limit).all()

    # Shape response explicitly for frontend consumption
    return [
        {
            "id": m.id,
            "date": m.created_at,
            "movement_type": m.movement_type,
            "quantity": m.quantity,
            "product": {
                "id": p.id,
                "name": p.name,
                "manufacturer_code": p.manufacturer_code,
            },
            "reference": m.source_entity,  # order / purchase / manual
        }
        for m, p in rows
    ]


# ---------------------------------------------------------------------------
# CREATE Inventory Manual Adjustment
# ---------------------------------------------------------------------------
@router.post("/adjustments")
def create_inventory_adjustment(
    product_id: int,
    counted_quantity: int,
    db: Session = Depends(get_db),
):
    """
    Create a manual inventory adjustment.

    The user provides the REAL counted stock.
    The backend calculates the delta and stores it
    as an ADJUST inventory movement.
    """

    # 1. Calculate current stock (source of truth)
    current_stock = (
        db.query(func.coalesce(func.sum(InventoryMovement.quantity), 0))
        .filter(InventoryMovement.product_id == product_id)
        .scalar()
    )

    # 2. Calculate delta (difference between counted and current)
    delta = counted_quantity - current_stock

    # 3. Create adjustment movement (no direct stock update)
    movement = InventoryMovement(
        product_id=product_id,
        quantity=delta,
        movement_type="ADJUST",
        occurred_at=datetime.now(timezone.utc),
        source_entity="MANUAL_ADJUSTMENT",
        source_id=f"MANUAL_{datetime.now(timezone.utc).isoformat()}",
    )

    db.add(movement)
    db.commit()
    db.refresh(movement)

    # 4. Return clear result for UI
    return {
        "product_id": product_id,
        "previous_stock": current_stock,
        "counted_stock": counted_quantity,
        "adjustment": delta,
        "movement_id": movement.id,
    }

