from sqlalchemy import Column, Integer, String, DateTime, ForeignKey
from sqlalchemy.sql import func
from app.core.database import Base


class AuditLog(Base):
    """
    Audit log for tracking sensitive actions in the system.

    Stores who performed an action, what was done, and when it happened.
    """

    __tablename__ = "audit_logs"

    # Primary key
    id = Column(Integer, primary_key=True, index=True)

    # User who performed the action
    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)

    # Action identifier (e.g. 'CREATE_PRODUCT', 'UPDATE_ROLE')
    action = Column(String(100), nullable=False)

    # Target resource name (e.g. 'product', 'user', 'role')
    resource = Column(String(50), nullable=False)

    # ID of the affected resource (if applicable)
    resource_id = Column(Integer, nullable=True)

    # Timestamp of when the action occurred (UTC)
    created_at = Column(DateTime(timezone=True), server_default=func.now(), nullable=False)
