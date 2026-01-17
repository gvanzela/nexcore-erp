# app/core/security.py

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError
import secrets
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session

from app.core.config import settings
from app.core.deps import get_db
from app.models.user import User
from app.models.refresh_token import RefreshToken


# app/core/security.py

# Password hashing configuration
# bcrypt is slow by design → protects against brute-force attacks
pwd_context = CryptContext(
    schemes=["bcrypt"],
    deprecated="auto",
)


def get_password_hash(password: str) -> str:
    """
    Hash a plain-text password.

    - Receives the raw password
    - Applies bcrypt + random salt
    - Returns the full hash string (algorithm + salt + hash)
    """
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify a password against a stored hash.

    - plain_password: password typed by the user
    - hashed_password: hash stored in the database
    - Returns True if they match, False otherwise
    """
    return pwd_context.verify(plain_password, hashed_password)


# ==============================================================
# JWT settings
# ==============================================================
ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = 30


def create_access_token(subject: str) -> str:
    """
    Create a signed JWT access token.

    - subject: unique user identifier (e.g., user id or email)
    - embeds expiration and subject in payload
    """
    expire = datetime.utcnow() + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    payload = {"sub": subject, "exp": expire}
    return jwt.encode(payload, settings.secret_key, algorithm=ALGORITHM)


def verify_access_token(token: str) -> str:
    """
    Validate a JWT token and return its subject.

    - raises exception if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.secret_key, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise ValueError("Invalid or expired token")


# OAuth2 scheme definition
# Reads the JWT from: Authorization: Bearer <token>
security = HTTPBearer()


def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db),
) -> User:
    """
    Authentication guard.

    This dependency:
    - extracts the JWT from the Authorization header
    - validates the token signature and expiration
    - loads the authenticated user from the database

    Any endpoint using this dependency
    automatically requires authentication.
    """

    # Extract rae JWT from Authorization header
    token = credentials.credentials

    # Decode and validate JWT
    try:
        user_id = verify_access_token(token)
    except Exception:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired token",
        )

    # Load user from database
    user = db.get(User, int(user_id))

    # Validate user existence and active status
    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Inactive or invalid user",
        )

    return user


# Refresh token expiration (days)
REFRESH_TOKEN_EXPIRE_DAYS = 7


def generate_refresh_token() -> str:
    """
    Generate a secure random refresh token.

    - Uses cryptographically secure randomness
    - Returned value is the RAW token (to send to client)
    """
    return secrets.token_urlsafe(64)


def get_refresh_token_expiration() -> datetime:
    """
    Calculate refresh token expiration datetime.
    """
    return datetime.utcnow() + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)


def create_refresh_token(
    *,
    user_id: int,
    token_hash: str,
    expires_at: datetime,
) -> RefreshToken:
    """
    Build a RefreshToken ORM object.

    - user_id: owner of the session
    - token_hash: hashed refresh token (never store raw)
    - expires_at: expiration timestamp
    """
    return RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires_at,
        is_active=True,
    )

