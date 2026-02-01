# app/api/v1/inventory.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

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
    db: Session = Depends(get_db)
):
    """
    Read-only stock balance.

    Stock is NOT stored as a column.
    Stock is computed as the sum of all inventory movements for a product.
    """

    balance = (
        db.query(func.coalesce(func.sum(InventoryMovement.quantity), 0))
        .filter(InventoryMovement.product_id == product_id)
        .scalar()
    )

    # Optional: if you prefer to error when product never had movements,
    # keep it simple for now and always return a number.
    return {"product_id": product_id, "balance": str(balance)}


# Inventory Stock Listing Endpoint
@router.get("/")
def list_stock(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100), 
    db: Session = Depends(get_db)   
):
    """
    List current stock balance for all products.

    Stock is computed, never stored.
    """

    rows = (
        db.query(
            InventoryMovement.product_id,
            func.coalesce(func.sum(InventoryMovement.quantity), 0).label("balance"),
        )
        .group_by(InventoryMovement.product_id)
        .offset(skip).limit(limit).all()
    )

    return [
        {"product_id": product_id, "balance": str(balance)}
        for product_id, balance in rows
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

