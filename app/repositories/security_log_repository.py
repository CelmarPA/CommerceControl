# app/repositories/security_log_repository.py

"""
Repository layer for managing security event logs.

This module contains database operations for the SecurityLog model, including:
- Creating log records for security-related actions
- Fetching paginated and filtered log entries

These logs are used for auditing and monitoring security events such as:
- Authentication attempts
- Permission failures
- Suspicious activity detection
"""

from sqlalchemy import desc
from sqlalchemy.orm import Session
from typing import List

from app.models import SecurityLog


class SecurityLogRepository:
    """
    Repository responsible for CRUD operations on SecurityLog entries.
    """

    @staticmethod
    def create(db: Session, **data: dict) -> SecurityLog:
        """
        Creates a new security log entry.

        :param db: Active database session.
        :type db: Session

        :param data: Arbitrary keyword arguments representing log fields.
        :type data: dict

        :return: The created SecurityLog instance.
        :rtype: SecurityLog
        """

        log = SecurityLog(**data)
        db.add(log)
        db.commit()
        db.refresh(log)

        return log

    @staticmethod
    def list(db: Session, filters: dict, page: int, limit: int) -> List[SecurityLog]:
        """
        Retrieves a paginated and optionally filtered list of security logs.

        :param db: Active database session.
        :type db: Session

        :param filters: Dictionary where keys are field names and values are filters.
        :type filters: dict

        :param page: Page number used for pagination.
        :type page: int

        :param limit: Number of items per page.
        :type limit: int

        :return: A tuple containing the total record count and the list of logs.
        :rtype: tuple[int, list[SecurityLog]]
        """

        query = db.query(SecurityLog)

        for field, value in filters.items():
            if value:
                query = query.filter(getattr(SecurityLog, field) == value)

        total = query.count()

        logs = query.order_by(desc(SecurityLog.created_at)) \
            .offset((page - 1) * limit) \
            .limit(limit) \
            .all()

        return total, logs
