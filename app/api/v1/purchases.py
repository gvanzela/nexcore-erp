# app/api/v1/purchases.py

from fastapi import APIRouter, UploadFile, File, HTTPException
import tempfile
import os

# Reuse the XML parsing and matching logic already validated
from scripts.xml.read_nfe_xml import read_nfe_xml
from scripts.xml.match_items_by_ean import match_items_by_ean

# Imports for the confirm endpoint
from pydantic import BaseModel
from typing import List
from decimal import Decimal
from datetime import datetime, UTC
from sqlalchemy.orm import Session
from fastapi import Depends

from app.core.deps import get_db
from app.core.security import get_current_user
from app.models.inventory_movement import InventoryMovement
from app.models.product import Product
from app.models.user import User
from app.api.v1.schemas import (
                        PurchaseConfirmPayload, 
                        PurchaseResolveLinkPayload,
                        PurchaseResolveCreateProductPayload
)

from app.models.account_payable import AccountPayable

from app.models.customer import Customer

from app.core.audit import log_action

# Router for purchase-related endpoints
router = APIRouter(
    prefix="/api/v1/purchases", 
    tags=["purchases"]
    )

# Purchase XML preview endpoint
@router.post("/xml/preview")
async def preview_purchase_xml(file: UploadFile = File(...)):
    """
    Preview a supplier purchase XML (NF-e).

    - Read-only
    - No persistence
    - Returns purchase header + item preview
    """

    # ---------------------------------------------------------
    # 1) Basic validation
    # ---------------------------------------------------------
    if not file.filename.lower().endswith(".xml"):
        raise HTTPException(status_code=400, detail="Invalid file type. XML required.")

    # ---------------------------------------------------------
    # 2) Save uploaded XML to a temporary file
    # ---------------------------------------------------------
    # read_nfe_xml expects a file path
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        xml_bytes = await file.read()
        tmp.write(xml_bytes)
        tmp_path = tmp.name

    try:
        # -----------------------------------------------------
        # 3) Parse XML (purchase-level + items)
        # -----------------------------------------------------
        # parsed = {
        #   source_id, supplier_document, issue_date, total_amount, items
        # }
        parsed = read_nfe_xml(tmp_path)
        items = parsed["items"]

        # -----------------------------------------------------
        # 4) Match XML items with core products by EAN
        # -----------------------------------------------------
        matched, needs_review = match_items_by_ean(items)

        # -----------------------------------------------------
        # 5) Return preview response
        # -----------------------------------------------------
        return {
            "status": "ok",
            "data": {
                # Purchase header (used later in confirm)
                "purchase": {
                    "source_id": parsed["source_id"],
                    "supplier_document": parsed["supplier_document"],
                    "issue_date": parsed["issue_date"],
                    "total_amount": parsed["total_amount"],
                },
                # Item resolution
                "matched": matched,
                "needs_review": needs_review,
                # UX summary
                "summary": {
                    "total_items": len(items),
                    "matched": len(matched),
                    "needs_review": len(needs_review),
                },
            },
        }

    finally:
        # -----------------------------------------------------
        # 6) Cleanup temporary file
        # -----------------------------------------------------
        if os.path.exists(tmp_path):
            os.remove(tmp_path)


# Purchase XML confirm endpoint
@router.post("/xml/confirm")
def confirm_purchase_xml(
    payload: PurchaseConfirmPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Requires authentication
):
    """
    Confirm a purchase XML after preview.

    This endpoint:
    - Receives confirmed items from frontend
    - Generates IN inventory movements
    - Persists stock changes atomically
    - Creates ONE accounts payable entry (purchase-based)
    """

    # ---------------------------------------------------------
    # Basic validation
    # ---------------------------------------------------------
    if not payload.items:
        raise HTTPException(status_code=400, detail="No items to confirm")

    for item in payload.items:
        if item.quantity <= 0:
            raise HTTPException(status_code=400, detail="Quantity must be greater than zero")

        product = db.get(Product, item.product_id)
        if not product:
            raise HTTPException(
                status_code=400,
                detail=f"Invalid product_id: {item.product_id}",
            )

    # Check if this purchase XML has already been confirmed (idempotency)
    exists = (
        db.query(AccountPayable)
        .filter(
            AccountPayable.source_entity == "PURCHASE",
            AccountPayable.source_id == payload.source_id,
        )
        .first()
    )

    if exists:
        raise HTTPException(
            status_code=409,
            detail="This purchase XML has already been confirmed",
        )

    # Simple supplier validation (existence + type)
    supplier = db.get(Customer, payload.supplier_id)
    if not supplier:
        raise HTTPException(status_code=400, detail="Invalid supplier_id")
    # Allow linking to a Customer that is also a Supplier (type = "both")
    if supplier.type.lower() == "customer":
        supplier.type = "both"

    # ---------------------------------------------------------
    # Process each confirmed item (stock IN)
    # ---------------------------------------------------------
    for item in payload.items:
        movement = InventoryMovement(
            product_id=item.product_id,
            movement_type="IN",
            quantity=item.quantity,
            occurred_at=datetime.now(UTC),
            source_entity="purchase_xml",
            source_id=payload.source_id,  # NF-e key
        )
        db.add(movement)

    # ---------------------------------------------------------
    # Create Accounts Payable (1 purchase -> 1 payable)
    # ---------------------------------------------------------
    payable = AccountPayable(
        supplier_id=payload.supplier_id,
        source_entity="PURCHASE",
        source_id=payload.source_id,      # NF-e key
        amount=payload.total_amount,
        due_date=payload.issue_date,      # MVP: due date = issue/entry date
        status="OPEN",
    )
    db.add(payable)

    # ---------------------------------------------------------
    # Commit atomically
    # ---------------------------------------------------------
    db.commit()

    return {
        "status": "ok",
        "data": {
            "items_created": len(payload.items),
            "payable_created": True,
        },
    }



# ---------------------------------------------------------
# Resolve a single XML item by linking it to an existing product
# ---------------------------------------------------------
@router.post("/xml/resolve/link")
def resolve_purchase_item_link(
    payload: PurchaseResolveLinkPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user), # Requires authentication
):
    """
    Links a single XML purchase item to an existing product.

    This endpoint is used ONLY for human-assisted resolution
    before final confirmation (/xml/confirm).
    """

    # -----------------------------------------------------
    # 1) Load target product
    # -----------------------------------------------------
    product = db.get(Product, payload.product_id)
    if not product:
        raise HTTPException(status_code=404, detail="Product not found")

    # -----------------------------------------------------
    # 2) Apply optional, non-destructive updates
    # - manufacturer_code: can be updated if provided
    # - barcode: only filled if product has none
    # -----------------------------------------------------
    should_commit = False

    if payload.manufacturer_code and product.manufacturer_code != payload.manufacturer_code:
        product.manufacturer_code = payload.manufacturer_code
        should_commit = True

    if payload.barcode and not product.barcode:
        product.barcode = payload.barcode
        should_commit = True


    # Persist only if something actually changed
    if should_commit:
        action = "UPDATE_PRODUCT_XML"
        log_action(
            db=db,
            user_id=current_user.id,
            action=action,
            resource="product",
            resource_id=product.id,
        )

        db.add(product)
        db.commit()
        db.refresh(product)

    # -----------------------------------------------------
    # 3) Return resolved/matched representation
    # (frontend assembles final confirmation payload)
    # -----------------------------------------------------
    return {
        "status": "ok",
        "data": {
            "product_id": product.id,
            "quantity": payload.quantity,
            "status": "matched"
        }
    }


# ---------------------------------------------------------
# Resolve a single XML item by creating a new product
# ---------------------------------------------------------
@router.post("/xml/resolve/create-product")
def resolve_purchase_item_create_product(
    payload: PurchaseResolveCreateProductPayload,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # Requires authentication
):
    """
    Creates a new product from an XML item and marks it as resolved.

    This endpoint:
    - Creates a Product using XML data
    - Does NOT create inventory movements
    - Returns the item as 'matched' for later confirmation
    """

    # Bootstrap fields
    name = payload.description
    short_name = payload.description[:50]
    code = f"XML-{datetime.now().strftime('%Y%m%d%H%M%S')}", # fallback code
    # -----------------------------------------------------
    # 1) Create product from XML data
    # -----------------------------------------------------
    product = Product(
        code=code,
        name=name,
        short_name=short_name,
        description=payload.description,
        unit=payload.unit,
        manufacturer_code=payload.manufacturer_code,
        barcode=payload.barcode,
        active=True,
    )

    db.add(product)
    db.commit()
    db.refresh(product)

    # -----------------------------------------------------
    # 2) Audit log
    # -----------------------------------------------------
    log_action(
        db=db,
        user_id=current_user.id,
        action="CREATE_PRODUCT_XML",
        resource="product",
        resource_id=product.id,
    )

    # -----------------------------------------------------
    # 3) Return resolved/matched representation
    # -----------------------------------------------------
    return {
        "status": "ok",
        "data": {
            "product_id": product.id,
            "code": product.code,
            "manufacturer_code": product.manufacturer_code,
            "status": "matched",
        }
    }