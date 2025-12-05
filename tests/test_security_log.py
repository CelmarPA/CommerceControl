# app/tests/test_security_log.py

"""
SecurityLog Tests
-----------------

This module tests the SecurityLog model and ensures that security-related
events are logged correctly in the database.

Tests cover:
1. Creating a log entry for a user-related action.
2. Logging an event without a user (anonymous).
3. Verifying that all fields are stored and retrievable.
"""

from datetime import datetime, timezone
from sqlalchemy.orm import Session
from typing import Callable


from tests.conftest import create_user
from app.models import SecurityLog


def test_create_user_security_log(db_session: Session, create_user: Callable) -> None:
    """
    Test that a security log entry can be created for a specific user.

    :param db_session: SQLAlchemy session for test database.
    :type db_session: Session

    :param create_user: Fixture to create a user in the test database.
    :type create_user: Callable

    :return: None
    """

    user = create_user(email="log_user@test.com", verified=True)

    log_entry = SecurityLog(
        user_id=user.id,
        email=user.email,
        action="login_success",
        ip="127.0.0.1",
        path="/auth/login",
        method="POST",
        status_code="success",
        detail="User logged in successfully",
        created_at=datetime.now(timezone.utc)
    )

    db_session.add(log_entry)
    db_session.commit()
    db_session.refresh(log_entry)

    # ---------------------------
    # Assertions
    # ---------------------------
    assert log_entry.id is not None
    assert log_entry.user_id == user.id
    assert log_entry.email == user.email
    assert log_entry.action == "login_success"
    assert log_entry.ip == "127.0.0.1"
    assert log_entry.path == "/auth/login"
    assert log_entry.method == "POST"
    assert log_entry.status_code == "success"
    assert log_entry.detail == "User logged in successfully"
    assert isinstance(log_entry.created_at, datetime)


def test_create_anonymous_security_log(db_session: Session) -> None:
    """
    Test creating a security log entry without an associated user.

    :param db_session: SQLAlchemy session for test database.
    :type db_session: Session

    :return: None
    """

    log_entry = SecurityLog(
        user_id=None,
        email=None,
        action="refresh_invalid",
        ip="192.168.1.1",
        path="/auth/refresh",
        method="POST",
        status_code="fail",
        detail="Expired token attempt",
        created_at=datetime.now(timezone.utc)
    )

    db_session.add(log_entry)
    db_session.commit()
    db_session.refresh(log_entry)

    # ---------------------------
    # Assertions
    # ---------------------------
    assert log_entry.id is not None
    assert log_entry.user_id is None
    assert log_entry.email is None
    assert log_entry.action == "refresh_invalid"
    assert log_entry.status_code == "fail"
