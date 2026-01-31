# app/api/v1/inventory.py

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from sqlalchemy import func

from app.core.deps import get_db
from app.models.inventory_movement import InventoryMovement

router = APIRouter(
    prefix="/api/v1/inventory", 
    tags=["inventory"]
)

# Inventory Stock Balance Endpoint for a Product
@router.get("/{product_id}")
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



