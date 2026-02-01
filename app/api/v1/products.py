from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Query, Depends
from datetime import datetime

from app.core.database import SessionLocal
from app.models.product import Product
from app.api.v1.schemas import (
                ProductCreate, 
                ProductOut, 
                ProductUpdate, 
                PurchaseResolveCreateProductPayload
)
from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.user import User
from app.core.audit import log_action

# ============================================================================
# Products Router
# ============================================================================
# This router exposes CRUD endpoints for the Product entity.
# It represents the first core domain of the system.
# All routes are versioned under /api/v1/products
# ============================================================================

router = APIRouter(
    prefix="/api/v1/products",
    tags=["products"]
)

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@router.post("", response_model=ProductOut)
def create_product(
    payload: ProductCreate,
    db: Session = Depends(get_db),  # DB session injected here
    current_user: User = Depends(get_current_user), # Requires authentication
):
    """
    Create a new product.

    - Validates input data using ProductCreate schema
    - Persists the product in the database
    - Returns the created product
    """

    # Create Product ORM object from request payload
    data = payload.model_dump()

    # Ensure unique business code
    data["code"] = payload.code or f"PRD-{datetime.now().strftime('%Y%m%d%H%M%S%f')}"

    # Create Product instance
    product = Product(**data)

    # Persist entity
    db.add(product)
    db.commit()
    db.refresh(product)

    return product


# ---------------------------------------------------------------------------
# READ (LIST) with filters and pagination
# ---------------------------------------------------------------------------
# Supports:
# - Filtering by active status
# - Pagination using skip & limit
# - Backend-enforced max limit to prevent abuse
#
# Examples:
# - GET /api/v1/products
# - GET /api/v1/products?active=true
# - GET /api/v1/products?skip=0&limit=20
# ---------------------------------------------------------------------------
# Now the database session is injected by FastAPI.
# The endpoint no longer creates or closes the DB connection manually.
# ---------------------------------------------------------------------------

from sqlalchemy import or_
from fastapi import Query

@router.get("", response_model=List[ProductOut])
def list_products(
    active: Optional[bool] = Query(None),
    search: Optional[str] = Query(None),
    barcode: Optional[str] = Query(None),
    manufacturer_code: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    List products with optional filters.

    - search: free text (name / description)
    - barcode: exact match (EAN)
    - manufacturer_code: exact match
    """

    query = db.query(Product)

    # Filter by active flag
    if active is not None:
        query = query.filter(Product.active == active)

    # Free text search (case-insensitive)
    if search:
        ilike = f"%{search}%"
        query = query.filter(
            or_(
                Product.name.ilike(ilike),
                Product.description.ilike(ilike),
                Product.manufacturer_code.ilike(ilike),
            )
        )

    # Exact barcode match
    if barcode:
        query = query.filter(Product.barcode == barcode)

    # Exact manufacturer code match
    if manufacturer_code:
        query = query.filter(Product.manufacturer_code == manufacturer_code)

    # Pagination
    return query.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ (BY ID)
# ---------------------------------------------------------------------------
@router.get("/{product_id}", response_model=ProductOut)
def get_product(
    product_id: int,
    db: Session = Depends(get_db), # DB session injected here
    current_user: User = Depends(get_current_user), # Requires authentication
):
    """
    Retrieve a single product by its ID.

    - Searches the database for a product with the given ID
    - Returns the product if found
    - Raises 404 if the product does not exist
    """

    # Query product by primary key
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product


# ---------------------------------------------------------------------------
# READ (BY MANUFACTURER CODE)
# ---------------------------------------------------------------------------
@router.get("/by-manufacturer-code/{manufacturer_code}", response_model=ProductOut)
def get_product(
    manufacturer_code: str,
    db: Session = Depends(get_db), # DB session injected here
    current_user: User = Depends(get_current_user), # Requires authentication
):
    """
    Retrieve a single product by its Manufacturer Code.

    - Searches the database for a product with the given Code
    - Returns the product if found
    - Raises 404 if the product does not exist
    """

    # Query product by manufacturer code
    product = (
        db.query(Product)
        .filter(Product.manufacturer_code == manufacturer_code)
        .first()
    )

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    return product

# ---------------------------------------------------------------------------
# UPDATE (PARTIAL)
# ---------------------------------------------------------------------------
# This endpoint performs a partial update on a Product entity.
# It follows the PATCH semantics: only provided fields are updated.
# Common use cases:
# - Edit product description
# - Soft delete / reactivate product via `active` flag
# ---------------------------------------------------------------------------

@router.patch("/{product_id}", response_model=ProductOut)
def update_product(
    product_id: int, 
    payload: ProductUpdate,
    db: Session = Depends(get_db), # DB session injected here
    current_user: User = Depends(get_current_user), # Requires authentication
):
    """
    Partially update a product by its ID.

    - Updates only the fields provided in the request body
    - Preserves existing values for omitted fields
    - Raises 404 if the product does not exist
    """

    # Retrieve product by primary key
    product = db.get(Product, product_id)

    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # Apply only provided fields (PATCH behavior)
    updates = payload.dict(exclude_unset=True)
    for field, value in updates.items():
        setattr(product, field, value)

    # After applying updates
    if updates:
        action = "DEACTIVATE_PRODUCT" if updates.get("active") is False else "UPDATE_PRODUCT"
        log_action(
            db=db,
            user_id=current_user.id,
            action=action,
            resource="product",
            resource_id=product.id,
        )

    db.commit()
    db.refresh(product)

    return product

