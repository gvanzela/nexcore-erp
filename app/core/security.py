# app/core/security.py

from passlib.context import CryptContext
from datetime import datetime, timedelta
from jose import jwt, JWTError

from app.core.config import settings

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
    return jwt.encode(payload, settings.SECRET_KEY, algorithm=ALGORITHM)


def verify_access_token(token: str) -> str:
    """
    Validate a JWT token and return its subject.

    - raises exception if token is invalid or expired
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[ALGORITHM])
        return payload.get("sub")
    except JWTError:
        raise ValueError("Invalid or expired token")
