# app/core/rate_limit_custom.py

"""
Custom rate-limiting logic for password reset requests.

This module provides utility functions that implement custom rate limits
for password reset operations, independent of the global SlowAPI limiter.

Two rate-limiting rules are enforced:
    - Limit password reset attempts per email.
    - Limit password reset attempts per IP address.

Each reset request is logged into the `PasswordResetLog` table.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm  import Session

from app.models import PasswordResetLog


# ----------------------------------------------------------------------
# Email-Based Rate Limiting
# ----------------------------------------------------------------------
def too_many_resets_email(db: Session, email: str, minutes: int = 10) -> bool:
    """
    Checks whether an email address has already triggered a password reset
    request within the defined time window.

    :param db: Active database session.
    :type db: Session

    :param email: The email address to check.
    :type email: str

    :param minutes: Time window in minutes to restrict repeated requests. Defaults to 10 minutes.
    :type minutes: int

    :return: True if a password reset was requested within the time window.
    :rtype: bool
    """

    limit_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    count = (
        db.query(PasswordResetLog)
        .filter(
            PasswordResetLog.email == email,
            PasswordResetLog.created_at >= limit_time
        )
        .count()
    )

    # Restriction: only 1 reset allowed per email per time window.
    return count >= 1


# ----------------------------------------------------------------------
# IP-Based Rate Limiting
# ----------------------------------------------------------------------
def too_many_resets_ip(db: Session, ip: str, minutes: int = 10, limit: int = 3) -> bool:
    """
    Checks whether an IP address has exceeded the allowed number of
    password reset requests within the defined time window.

    :param db:  Active database session.
    :type db: Session

    :param ip: The client IP address.
    :type ip: str

    :param minutes: Time window (in minutes) to apply the limit.
    :type minutes: int

    :param limit: Maximum allowed number of requests from the same IP. Defaults to 3.
    :type limit: int

    :return: (bool): True if the IP has exceeded the allowed number of requests.
    :rtype: bool
    """

    limit_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    count = (
        db.query(PasswordResetLog)
        .filter(
            PasswordResetLog.ip == ip,
            PasswordResetLog.created_at >= limit_time
        )
        .count()
    )

    return count >= limit


def log_reset_attempt(db: Session, email: str, ip: str) -> None:
    """
    Logs a password reset attempt in the database.

    :param db: Active database session.
    :type db: Session

    :param email: Email used for the reset request.
    :type email: str

    :param ip: Client IP address.
    :type ip: str

    :return: None
    """

    entry = PasswordResetLog(email=email, ip=ip)
    db.add(entry)
    db.commit()
