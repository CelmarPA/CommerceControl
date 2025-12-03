# app/model/security_log.py

"""
Database model for storing detailed security-related events.

This table helps track authentication, authorization, and other critical
security operations. It is useful for:
- Auditing user activity
- Detecting suspicious or malicious behavior
- Troubleshooting authentication issues
- Monitoring system access patterns

Each record represents a single security event such as login attempts,
permission violations, token usage, or system actions.
"""

from sqlalchemy import Column, Integer, String, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class SecurityLog(Base):
    """
    Represents a security-related audit log entry.

    :param id: Primary key of the log entry.
    :type id: int

    :param user_id: ID of the user who triggered the event, if applicable.
    :type user_id: int | None

    :param email: Email associated with the event, if available.
    :type email: str | None

    :param action: Name or identifier of the security action performed.
    :type action: str

    :param ip: IP address of the requester that triggered the event.
    :type ip: str | None

    :param path: API path (endpoint) where the event occurred.
    :type path: str

    :param method: HTTP method used for the request (e.g., GET, POST).
    :type method: str

    :param status_code: Indicates whether the event was a success or failure.
    :type status_code: str

    :param detail: Additional contextual information about the event.
    :type detail: str

    :param created_at: Timestamp (UTC) indicating when the log entry was created.
    :type created_at: datetime
    """

    __tablename__ = "security_logs"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    email = Column(String, index=True, nullable=True)
    action = Column(String, nullable=False)
    ip = Column(String, index=True, nullable=True)
    path = Column(String, nullable=False)
    method = Column(String, nullable=False)
    status_code = Column(String, nullable=False)  # success / fail
    detail = Column(String, nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), index=True)

    user = relationship("User", lazy="joined")
