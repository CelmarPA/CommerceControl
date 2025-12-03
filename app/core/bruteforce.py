# app/core/bruteforce.py

"""
Brute-force protection utility functions.

This module provides helper functions for tracking login attempts
and detecting potential brute-force attacks based on IP address
or email. It uses the LoginAttempt model to record and query recent
failed authentication attempts.
"""

from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import LoginAttempt


# ----------------------------------------------------------------------
# Record Login Attempt
# ----------------------------------------------------------------------
def record_login_attempts(db: Session, email: str, ip: str, success: bool) -> None:
    """
    Records a login attempt in the database.

    :param db: Active SQLAlchemy session.
    :type db: Session

    :param email: Email used in the login attempt.
    :type email: str

    :param ip: IP address of the client.
    :type ip: str

    :param success: Whether the login attempt was successful.
    :type success: bool

    :return: None
    """

    db.add(LoginAttempt(email=email, ip=ip, success=success))
    db.commit()


# ----------------------------------------------------------------------
# Too Many Failures by IP
# ----------------------------------------------------------------------
def too_many_failures_ip(db: Session, ip: str, max_failures: int = 5, minutes: int = 15) -> bool:
    """
    Checks if an IP address has exceeded the allowed number of failed login attempts
    within a time window.

    :param db: Active SQLAlchemy session.
    :type db: Session

    :param ip: IP address to check.
    :type ip: str

    :param max_failures:  Maximum allowed failed attempts. Defaults to 5.
    :type max_failures: int

    :param minutes: Time window (in minutes) to count attempts. Defaults to 15.
    :type minutes: int

    :return: (bool):  True if the number of failed attempts is equal to or exceeds max_failures.
    :rtype: bool
    """

    limit_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    failures = (
        db.query(LoginAttempt)
        .filter(
            LoginAttempt.ip == ip,
            LoginAttempt.success == False,      # noqa: E712 - intentional comparison
            LoginAttempt.created_at >= limit_time,
        )
        .count()
    )

    return failures >= max_failures


# ----------------------------------------------------------------------
# Too Many Failures by Email
# ----------------------------------------------------------------------
def too_many_failures_email(db: Session, email: str, max_failures: int = 5, minutes: int = 15) -> bool:
    """
    Checks whether an email address has exceeded the allowed number of failed login
    attempts within a defined time window.

    :param db: Active SQLAlchemy session.
    :type db: Session

    :param email: Email to check.
    :type email: str

    :param max_failures: Maximum allowed failed attempts. Defaults to 5.
    :type max_failures: int

    :param minutes: Time window (in minutes) to count attempts. Defaults to 15.
    :type minutes: int

    :return: True if the number of failed attempts is equal to or exceeds max_failures.
    :rtype: bool
    """

    limit_time = datetime.now(timezone.utc) - timedelta(minutes=minutes)

    failures = db.query(LoginAttempt).filter(
        LoginAttempt.email == email,
        LoginAttempt.success == False,      # noqa: E712 - intentional comparison
        LoginAttempt.created_at >= limit_time,
    ).count()

    return failures >= max_failures


# ----------------------------------------------------------------------
# Clear Failures After Successful Login
# ----------------------------------------------------------------------
def clear_failures(db: Session, email: str, ip: str) -> None:
    """
    Clears stored failed login attempts associated with a given email or IP.
    This is typically called after a successful authentication.

    :param db: Active SQLAlchemy session.
    :type db: Session

    :param email: Email used during login.
    :type email: str

    :param ip: Client IP address.
    :type ip: str

    :return: None
    """

    db.query(LoginAttempt).filter(
        (LoginAttempt.email == email) | (LoginAttempt.ip == ip),
    ).delete()
    db.commit()
