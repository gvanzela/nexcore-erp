# app/api/v1/auth.py

from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from datetime import datetime

# Request / response schemas (API contracts)
from app.api.v1.schemas_auth import UserLogin, Token, UserCreate, AccessToken, LogoutRequest, LogoutResponse

# Database dependency (shared session)
from app.core.deps import get_db

# Security helpers (password + JWT)
from app.core.security import (
    verify_password,
    create_access_token,
    generate_refresh_token,
    get_refresh_token_expiration,
    create_refresh_token,
    get_password_hash,
    get_current_user,
)

# User database model
from app.models.user import User

# RefreshToken database model
from app.models.refresh_token import RefreshToken

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

    # 5) Create refresh token (RAW value for client)
    raw_refresh_token = generate_refresh_token()

    # 6) Hash refresh token before storing
    refresh_token_hash = get_password_hash(raw_refresh_token)

    # 7) Build refresh token ORM object
    refresh_token = create_refresh_token(
        user_id=user.id,
        token_hash=refresh_token_hash,
        expires_at=get_refresh_token_expiration(),
    )

    # 8) Persist refresh token in database
    db.add(refresh_token)
    db.commit()

    # 9) Return tokens to client
    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
    }


# Create new user endpoint
@router.post("/signup", status_code=status.HTTP_201_CREATED)
def signup(
    payload: UserCreate,
    db: Session = Depends(get_db),
):
    """
    Create a new user account.

    - Receives email + raw password
    - Hashes the password
    - Persists the user in the database
    """

    # Check if email is already registered
    existing_user = db.query(User).filter(User.email == payload.email).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered",
        )

    # Hash the raw password before storing
    hashed_password = get_password_hash(payload.password)

    # Create User entity
    user = User(
        email=payload.email,
        password_hash=hashed_password,
        is_active=True,
    )

    # Persist user
    db.add(user)
    db.commit()
    db.refresh(user)

    return {"message": "User created successfully"}


# Create refresh token endpoint
@router.post("/refresh", response_model=Token)
def refresh_token(
    refresh_token: str,
    db: Session = Depends(get_db),
):
    """
    Exchange a valid refresh token for a new access token.
    """

    # 1) Load active refresh tokens from DB
    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.is_active.is_(True),
            RefreshToken.expires_at > datetime.utcnow(),
        )
        .all()
    )

    # 2) Find matching token by comparing hashes
    stored_token = next(
        (t for t in tokens if verify_password(refresh_token, t.token_hash)),
        None,
    )

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired refresh token",
        )
    
    # 3) Invalidate the used refresh token
    # Refresh tokens must be single-use to prevent replay attacks
    stored_token.is_active = False

    # Persist the change
    db.commit()

    # 4) Generate RAW refresh token (to return to client)
    raw_refresh_token = generate_refresh_token()

    # 5) Hash and expiration (what goes to DB)
    token_hash = get_password_hash(raw_refresh_token)
    expires_at = get_refresh_token_expiration()

    # 6) Create refresh token DB record
    new_refresh_token = create_refresh_token(
        user_id=stored_token.user_id,
        token_hash=token_hash,
        expires_at=expires_at,
    )

    db.add(new_refresh_token)
    db.commit()

    # 7) Generate new access token
    access_token = create_access_token(subject=str(stored_token.user_id))

    return {
        "access_token": access_token,
        "refresh_token": raw_refresh_token,
        "token_type": "bearer",
    }


# Logout endpoint
@router.post("/logout", response_model=LogoutResponse)
def logout(
    data: LogoutRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    """
    Revoke a refresh token (logout).
    """
    # 1) Load active refresh tokens for current user
    tokens = (
        db.query(RefreshToken)
        .filter(
            RefreshToken.user_id == current_user.id,
            RefreshToken.is_active.is_(True),
        )
        .all()
    )

    # 2) Find matching token by comparing hashes
    stored_token = next(
        (t for t in tokens if verify_password(data.refresh_token, t.token_hash)),
        None,
    )

    if not stored_token:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token",
        )

    # 3) Revoke token
    stored_token.is_active = False
    db.commit()

    return {"message": "Logged out successfully"}

