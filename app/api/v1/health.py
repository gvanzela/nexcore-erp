from fastapi import APIRouter, Depends
from sqlalchemy import text
from app.core.database import engine
from app.core.security import require_min_role


router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/db")
def db_check():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    return {"db": result}

# RBAC-protected endpoint example
@router.get("/admin-check")
def admin_check(current_user=Depends(require_min_role(100))):
    """
    Admin-only endpoint to validate RBAC.
    """
    return {"ok": True, "user_id": current_user.id}

