from sqlalchemy.orm import Session
from app.models.audit_log import AuditLog


def log_action(
    *,
    db: Session,
    user_id: int,
    action: str,
    resource: str,
    resource_id: int | None = None,
):
    """
    Persist an audit log entry.

    - db: active DB session
    - user_id: actor
    - action: what happened (e.g. 'LOGIN', 'UPDATE_ROLE')
    - resource: target entity (e.g. 'user', 'product')
    - resource_id: target id (optional)
    """
    audit = AuditLog(
        user_id=user_id,
        action=action,
        resource=resource,
        resource_id=resource_id,
    )
    db.add(audit)
    db.commit()
