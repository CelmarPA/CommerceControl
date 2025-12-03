# app/core/security_log.py

"""
Utility for creating detailed security audit logs.

This module provides a helper function (`log_security_event`) that stores
security-related events in the database, such as:
- Login attempts (successful or failed)
- Token creation
- Password reset events
- Suspicious requests
- Admin actions

The function may be called both from route handlers and background scripts.
"""

from sqlalchemy.orm import Session
from fastapi import Request
from typing import Optional
from datetime import datetime, timezone

from app.models import SecurityLog


def log_security_event(
    db: Session,
    action: str,
    status: str,
    detail: str = "",
    request: Optional[Request] = None,
    user_id: Optional[int] = None,
    email: Optional[str] = None,
) -> SecurityLog:
    """
    Create a detailed security event log and save it to the database.

    :param db: Active SQLAlchemy database session.
    :type db: Session

    :param action:High-level name of the action performed (e.g., "login_attempt", "token_created").
    :type action: str

    :param status: Result status of the action (e.g., "success", "failed", "blocked").
    :type status: str

    :param detail: Optional descriptive message with additional context.
    :type detail: Optional[str]

    :param request: HTTP request object. If provided, the log will include client IP,
                    HTTP method, and request path. If omitted, these fields are set to "internal", allowing
                    usage in background tasks or CLI scripts.
    :type request: Optional[Request]

    :param user_id: ID of the user involved in the event, if applicable.
    :type user_id: int

    :param email: Email associated with the event, useful for logging events before user authentication
                  (e.g., failed login attempts).
    :type email: Optional[str]

    :return: The created SecurityLog database object.
    :rtype: SecurityLog

    . note::
        - This function commits the database transaction immediately.
        - Timestamps are stored in UTC for consistency and audit accuracy.
    """

    # Fallback values for logs coming from internal or automated scripts
    ip: str = request.client.host if request else "internal"
    path: str = request.url.path if request else "internal"
    method: str = request.method if request else "internal"

    # Create and populate the security log entry
    log = SecurityLog(
        user_id=user_id,
        email=email,
        action=action,
        ip=ip,
        path=path,
        method=method,
        status_code=status,
        detail=detail,
        created_at=datetime.now(timezone.utc)
    )

    # Persist the log entry
    db.add(log)
    db.commit()
    db.refresh(log)

    return log
