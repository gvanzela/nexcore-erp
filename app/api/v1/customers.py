from fastapi import APIRouter, HTTPException, Query, Depends
from sqlalchemy.orm import Session
from typing import List, Optional
from sqlalchemy.exc import IntegrityError

from app.core.deps import get_db
from app.core.security import get_current_user
from app.core.audit import log_action

from app.models.customer import Customer
from app.models.user import User
from app.api.v1.schemas import (
    CustomerCreate,
    CustomerUpdate,
    CustomerOut,
)

# ============================================================================
# Customers Router
# ============================================================================
# This router exposes CRUD endpoints for the Customer entity.
#
# Customer is a generic party abstraction:
# - Can represent customers, suppliers, partners, etc.
# - Domain-specific meaning comes from configuration/data, not code
#
# All routes are versioned under /api/v1/customers
# ============================================================================

router = APIRouter(
    prefix="/api/v1/customers",
    tags=["customers"]
)

# ---------------------------------------------------------------------------
# CREATE
# ---------------------------------------------------------------------------
@router.post("", response_model=CustomerOut)
def create_customer(
    payload: CustomerCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Create a new customer.

    - Uses flush() to validate DB constraints before commit
    - Ensures atomicity per request
    """

    customer = Customer(**payload.dict())

    try:
        db.add(customer)
        db.flush()        # send to DB, but do NOT commit yet
        db.refresh(customer)

        db.commit()       # persist only after everything is safe

    except IntegrityError:
        db.rollback()
        raise HTTPException(
            status_code=409,
            detail="Customer with this document already exists"
        )

    log_action(
        db=db,
        user_id=current_user.id,
        action="CREATE_CUSTOMER",
        resource="customer",
        resource_id=customer.id,
    )

    return customer



# ---------------------------------------------------------------------------
# READ (LIST) with pagination and filters
# ---------------------------------------------------------------------------
@router.get("", response_model=List[CustomerOut])
def list_customers(
    active: Optional[bool] = Query(None),
    type: Optional[str] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a list of customers.

    - Supports filtering by:
        - active status
        - customer type (e.g. customer / supplier)
    - Uses pagination (skip & limit)
    """

    query = db.query(Customer)

    if active is not None:
        query = query.filter(Customer.active == active)

    if type is not None:
        query = query.filter(Customer.type == type)

    return query.offset(skip).limit(limit).all()


# ---------------------------------------------------------------------------
# READ (BY ID)
# ---------------------------------------------------------------------------
@router.get("/{customer_id}", response_model=CustomerOut)
def get_customer(
    customer_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Retrieve a single customer by ID.

    - Raises 404 if not found
    """

    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    return customer


# ---------------------------------------------------------------------------
# UPDATE (PARTIAL)
# ---------------------------------------------------------------------------
@router.patch("/{customer_id}", response_model=CustomerOut)
def update_customer(
    customer_id: int,
    payload: CustomerUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    Partially update a customer.

    - PATCH semantics (only provided fields are updated)
    - Uses exclude_unset=True
    """

    customer = db.get(Customer, customer_id)

    if not customer:
        raise HTTPException(status_code=404, detail="Customer not found")

    updates = payload.dict(exclude_unset=True)

    for field, value in updates.items():
        setattr(customer, field, value)

    if updates:
        action = (
            "DEACTIVATE_CUSTOMER"
            if updates.get("active") is False
            else "UPDATE_CUSTOMER"
        )

        log_action(
            db=db,
            user_id=current_user.id,
            action=action,
            resource="customer",
            resource_id=customer.id,
        )

    db.commit()
    db.refresh(customer)

    return customer
