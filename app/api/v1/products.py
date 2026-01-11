from fastapi import APIRouter, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional
from fastapi import Query

from app.core.database import SessionLocal
from app.models.product import Product
from app.api.v1.schemas import ProductCreate, ProductOut, ProductUpdate

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
def create_product(payload: ProductCreate):
    """
    Create a new product.

    - Validates input data using ProductCreate schema
    - Persists the product in the database
    - Returns the created product
    """
    db: Session = SessionLocal()

    # Create Product ORM object from request payload
    product = Product(**payload.dict())

    # Persist entity
    db.add(product)
    db.commit()
    db.refresh(product)

    db.close()
    return product


# ---------------------------------------------------------------------------
# READ (LIST)
# ---------------------------------------------------------------------------
# This endpoint retrieves products from the database.
# It supports optional filtering by the `active` flag via query parameters.
#
# Examples:
# - GET /api/v1/products            -> returns all products
# - GET /api/v1/products?active=true  -> returns only active products
# - GET /api/v1/products?active=false -> returns only inactive products
# ---------------------------------------------------------------------------
@router.get("", response_model=List[ProductOut])
def list_products(active: Optional[bool] = Query(None)):
    """
    Retrieve a list of products.

    - If `active` is not provided, all products are returned
    - If `active` is provided, results are filtered by active status
    """
    db: Session = SessionLocal()

    # Base query (no filters applied yet)
    query = db.query(Product)

    # Apply filter only if query parameter is provided
    if active is not None:
        query = query.filter(Product.active == active)

    products = query.all()

    db.close()
    return products




# ---------------------------------------------------------------------------
# READ (BY ID)
# ---------------------------------------------------------------------------
@router.get("/{product_id}", response_model=ProductOut)
def get_product(product_id: int):
    """
    Retrieve a single product by its ID.

    - Searches the database for a product with the given ID
    - Returns the product if found
    - Raises 404 if the product does not exist
    """
    db: Session = SessionLocal()

    # Query product by primary key
    product = db.query(Product).filter(Product.id == product_id).first()

    db.close()

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
def update_product(product_id: int, payload: ProductUpdate):
    """
    Partially update a product by its ID.

    - Updates only the fields provided in the request body
    - Preserves existing values for omitted fields
    - Raises 404 if the product does not exist
    """
    db: Session = SessionLocal()

    # Retrieve product by primary key
    product = db.query(Product).filter(Product.id == product_id).first()

    if not product:
        db.close()
        raise HTTPException(status_code=404, detail="Product not found")

    # Apply only provided fields (PATCH behavior)
    for field, value in payload.dict(exclude_unset=True).items():
        setattr(product, field, value)

    db.commit()
    db.refresh(product)
    db.close()

    return product

