from fastapi import APIRouter
from sqlalchemy import text
from app.core.database import engine

router = APIRouter(prefix="/api/v1")

@router.get("/health")
def health():
    return {"status": "ok"}

@router.get("/db")
def db_check():
    with engine.connect() as conn:
        result = conn.execute(text("SELECT 1")).scalar()
    return {"db": result}
