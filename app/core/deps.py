from typing import Generator
from sqlalchemy.orm import Session

from app.core.database import SessionLocal

# ---------------------------------------------------------------------------
# Database Dependency
# ---------------------------------------------------------------------------
# This file centralizes database session management.
# It uses FastAPI's Dependency Injection system to:
# - Create a database session per request
# - Automatically close the session after the request finishes
# ---------------------------------------------------------------------------

def get_db() -> Generator[Session, None, None]:
    """
    Provides a SQLAlchemy database session.

    How it works:
    - Creates a new DB session
    - Yields it to the endpoint
    - Ensures the session is closed after the request

    This prevents connection leaks and removes the need
    to manually call db.close() in every endpoint.
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        # Always close the session, even if an error happens
        db.close()
