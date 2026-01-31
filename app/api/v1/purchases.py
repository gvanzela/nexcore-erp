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
from app.models.inventory_movement import InventoryMovement




router = APIRouter(
    prefix="/api/v1/purchases", 
    tags=["purchases"]
    )

# Purchase XML preview endpoint
@router.post("/xml/preview")
async def preview_purchase_xml(file: UploadFile = File(...)):
    """
    Preview a supplier purchase XML (NF-e).

    This endpoint:
    - Receives an XML file from the frontend
    - Parses the XML (NF-e standard)
    - Tries to match items with core products using EAN
    - Returns a preview:
        - matched items (auto-resolved)
        - needs_review items (manual confirmation required)

    IMPORTANT:
    - This endpoint DOES NOT write anything to the database
    - It is read-only and side-effect free
    """

    # ---------------------------------------------------------
    # 1) Basic validation
    # ---------------------------------------------------------
    if not file.filename.lower().endswith(".xml"):
        raise HTTPException(
            status_code=400,
            detail="Invalid file type. XML required."
        )

    # ---------------------------------------------------------
    # 2) Save uploaded XML to a temporary file
    # ---------------------------------------------------------
    # Why:
    # - read_nfe_xml expects a file path
    # - using a temp file avoids polluting the project
    # - file is deleted automatically
    with tempfile.NamedTemporaryFile(delete=False, suffix=".xml") as tmp:
        xml_bytes = await file.read()
        tmp.write(xml_bytes)
        tmp_path = tmp.name

    try:
        # -----------------------------------------------------
        # 3) Parse XML and extract raw items
        # -----------------------------------------------------
        # Output example per item:
        # {
        #   ean, quantity, unit_price, description
        # }
        items = read_nfe_xml(tmp_path)

        # -----------------------------------------------------
        # 4) Match XML items with core products by EAN
        # -----------------------------------------------------
        # Result:
        # - matched: items resolved automatically
        # - needs_review: items that require user confirmation
        matched, needs_review = match_items_by_ean(items)

        # -----------------------------------------------------
        # 5) Return preview response to frontend
        # -----------------------------------------------------
        # Frontend will:
        # - show matched items directly
        # - ask user to resolve needs_review items
        return {
            "matched": matched,
            "needs_review": needs_review,
            "summary": {
                "total_items": len(items),
                "matched": len(matched),
                "needs_review": len(needs_review),
            }
        }

    finally:
        # -----------------------------------------------------
        # 6) Cleanup temporary file
        # -----------------------------------------------------
        if os.path.exists(tmp_path):
            os.remove(tmp_path)



# Purchase XML confirm endpoint
class PurchaseItemConfirm(BaseModel):
    product_id: int
    quantity: Decimal


class PurchaseConfirmPayload(BaseModel):
    source_id: str
    items: List[PurchaseItemConfirm]


@router.post("/xml/confirm")
def confirm_purchase_xml(
    payload: PurchaseConfirmPayload,
    db: Session = Depends(get_db),
):
    """
    Confirm a purchase XML after preview.

    This endpoint:
    - Receives confirmed items from frontend
    - Generates IN inventory movements
    - Persists stock changes atomically
    """

    for item in payload.items:
        movement = InventoryMovement(
            product_id=item.product_id,
            movement_type="IN",
            quantity=item.quantity,
            occurred_at=datetime.now(UTC),
            source_entity="purchase_xml",
            source_id=payload.source_id,
        )
        db.add(movement)

    db.commit()

    return {"status": "ok", "items_created": len(payload.items)}
