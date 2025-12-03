# app/models/login_attempt.py

"""
Database model for tracking login attempts.

This table is used by the brute-force protection system to:
- Record successful and failed login attempts.
- Rate-limit authentication attempts per IP and/or email.
- Mitigate credential-stuffing and password-guessing attacks.

Each record stores:
- Email (optional, may be None if unknown)
- Client IP address
- Whether the attempt succeeded
- Timestamp (UTC)

The retention policy should be handled separately (e.g., cron job or scheduled cleanup).
"""

from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime

from app.database import Base


class LoginAttempt(Base):
    """
    Represents a single login attempt, successful or failed.

    :param id: Primary key of the login attempt.
    :type id: int

    :param email: Email address associated with the login attempt. May be None if not provided.
    :type email: str | None

    :param ip: IP address from which the login attempt originated.
    :type ip: str

    :param success: Indicates whether authentication was successful.
    :type success: bool

    :param created_at: Timestamp (UTC) of when the login attempt was recorded.
    :type created_at: datetime
    """

    __tablename__ = "login_attempts"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String, index=True, nullable=True)
    ip = Column(String, index=True)
    success = Column(Boolean, default=False)
    created_at = Column(
        DateTime(timezone=True),
        default=lambda: datetime.now(timezone.utc),
        nullable=False
    )
