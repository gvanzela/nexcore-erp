# app/models/user.py

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.sql import func
from sqlalchemy.types import DateTime

from app.core.database import Base


class User(Base):
    """
    User entity.
    Represents an authenticated system user.
    """

    __tablename__ = "users"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Login identifier (must be unique)
    email = Column(String, unique=True, index=True, nullable=False)

    # Hashed password (never store raw passwords)
    password_hash = Column(String, nullable=False)

    # Soft delete / account status
    is_active = Column(Boolean, default=True, nullable=False)

    # Audit fields
    created_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    updated_at = Column(
        DateTime(timezone=True),
        server_default=func.now(),
        onupdate=func.now(),
        nullable=False,
    )
