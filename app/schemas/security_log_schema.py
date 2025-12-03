








































































































































































































































































































































































































































































# app/schemas/security_log_schema.py

"""
Security Log Schemas
-------------------

Schemas for representing security log entries and paginated lists of logs.
Used for audit trails, security monitoring, and API responses.
"""

from pydantic import BaseModel, EmailStr, ConfigDict
from datetime import datetime
from typing import Optional, List


class SecurityLogEntry(BaseModel):
    """
    Represents a single security log entry.

    :param id: Primary key of the log entry.
    :type id: int

    :param user_id: ID of the user associated with the action, if any.
    :type user_id: int | None

    :param email: Email of the user who performed the action, if known.
    :type email: str | None

    :param action: Description of the performed action.
    :type action: str

    :param ip: IP address from which the action originated.
    :type ip: str | None

    :param path: API endpoint or path where the action occurred.
    :type path: str

    :param method: HTTP method of the request (GET, POST, etc.).
    :type method: str

    :param status_code: Status of the action (success/fail or HTTP code).
    :type status_code: str

    :param detail: Detailed message describing the event.
    :type detail: str

    :param created_at: Timestamp (UTC) when the log entry was created.
    :type created_at: datetime
    """

    id: int
    user_id: Optional[int]
    email: Optional[EmailStr]
    action: str
    ip:  Optional[str]
    path: str
    method: str
    status_code: str
    detail: str
    created_at: datetime

    model_config = ConfigDict(from_attributes=True)


class SecurityLogList(BaseModel):
    """
    Represents a paginated list of security log entries.

    :param total: Total number of log entries.
    :type total: int

    :param page: Current page number.
    :type page: int

    :param limit: Number of entries per page.
    :type limit: int

    :param result: List of security log entries on the current page.
    :type result: List[SecurityLogEntry]
    """

    total: int
    page: int
    limit: int
    result: List[SecurityLogEntry]
