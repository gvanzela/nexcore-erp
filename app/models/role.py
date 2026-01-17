from sqlalchemy import Column, Integer, String, Boolean
from app.core.database import Base


class Role(Base):
    """
    Role model for RBAC (Role-Based Access Control).

    A role represents the level of access a user has in the system.
    Access rules will be derived from this role.
    """

    __tablename__ = "roles"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # Human-readable role name (e.g. 'admin', 'manager', 'user')
    # Must be unique to avoid ambiguity
    name = Column(String(50), unique=True, nullable=False)

    # Hierarchy level:
    # Higher number = more privileges
    # Example: admin=100, manager=50, user=10
    level = Column(Integer, nullable=False)

    # Soft enable/disable role without deleting it
    active = Column(Boolean, default=True, nullable=False)
