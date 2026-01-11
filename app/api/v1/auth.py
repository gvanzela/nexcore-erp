# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

# Request / response schemas (API contracts)
from app.api.v1.schemas_auth import UserLogin, Token

# Database dependency (shared session)
from app.core.deps import get_db

# Security helpers (password + JWT)
from app.core.security import verify_password, create_access_token

# User database model
from app.models.user import User


# Auth router
# - Prefix: /auth
# - Handles authentication-related endpoints only
router = APIRouter(prefix="/auth", tags=["auth"])


@router.post("/login", response_model=Token)
def login(payload: UserLogin, db: Session = Depends(get_db)):
    """
    Authenticate a user and return a JWT access token.
    """

    # 1) Fetch user from database using the email provided
    user = db.query(User).filter(User.email == payload.email).first()

    # 2) Validate user existence and active status
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 3) Validate password against stored hash
    if not verify_password(payload.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials",
        )

    # 4) Generate JWT token (user id as subject)
    access_token = create_access_token(subject=str(user.id))

    # 5) Return token using standard bearer format
    return Token(access_token=access_token)
