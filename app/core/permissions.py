# app/core/permissions.py

"""
Role-based access control (RBAC) dependencies for FastAPI routes.

This module provides reusable dependency functions to restrict access based on
the authenticated user's role. These dependencies are intended to be used in
FastAPI routes via the `Depends` system and work together with the authentication
function `get_current_user`.

Roles used in the system:
- superadmin
- admin
- user
"""

from fastapi import Depends, HTTPException, status

from app.models import User
from app.core.security import get_current_user


# ----------------------------------------------------------------------
# Simple Specific Role Requirements
# ----------------------------------------------------------------------
def admin_required(user: User = Depends(get_current_user)):
    """
    Restricts access to users with the 'admin' or 'superadmin' roles.

    :param user: The currently authenticated user.
    :type user: User

    :raises: HTTPException: If the user lacks admin privileges.

    :return: The authenticated user if authorized.
    :rtype: User
    """

    if user.role not in ["admin", "superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    return user


def superadmin_required(user: User = Depends(get_current_user)):
    """
    Restricts access exclusively to users with the 'superadmin' role.

    :param user: The currently authenticated user.
    :type user: User

    :raises: HTTPException: If the user lacks admin privileges.

    :return: The authenticated user if authorized.
    :rtype: User
    """

    if user.role not in ["superadmin"]:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Not allowed"
        )

    return user
