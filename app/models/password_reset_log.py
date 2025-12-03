# app/models/password_reset_log.py

"""
Database model for tracking password reset requests.

This table is used primarily for security purposes:
- Preventing abuse of the "forgot password" endpoint
- Enforcing cooldowns based on IP or email
- Detecting suspicious activity patterns
- Optional integration with audit systems

Each entry represents a single password reset request.
"""
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, DateTime

from app.database import Base


class PasswordResetLog(Base):
    """
    Represents a log entry for a password reset request.

    :param id: Primary key of the log entry.
    :type id: int

    :param email: Email address associated with the password reset request.
    :type email: str

    :param ip: IP address from which the request originated.
    :type ip: str

    :param created_at: Timestamp (UTC) of when the request was made.
    :type created_at: datetime
    """

    __tablename__ = "password_reset_logs"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True)
    ip = Column(String, index=True)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
