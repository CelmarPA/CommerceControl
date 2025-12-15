# app/routers/admin_users.py

"""
Admin Users Router
------------------

This module exposes administrative endpoints for managing users.
All routes are protected by admin-level permissions and allow:

- Listing users with pagination
- Fetching user details
- Updating user attributes
- Enabling/disabling user accounts
- Deleting users (superadmin only)

Every route delegates business logic to `UserService`, keeping the router thin.
"""
from typing import List

from fastapi import APIRouter, Depends, Query, HTTPException
from sqlalchemy.orm import Session

from app.core.permissions import admin_required, superadmin_required
from app.database import get_db
from app.schemas.user_schema import UserListItem, UserDetail, UserUpdate
from app.services.user_service import UserService

router = APIRouter(prefix="/admin/users", tags=["Admin Users"])


@router.get("/", response_model=list[UserListItem], dependencies=[Depends(admin_required)])
def list_users(
        page: int = Query(1, ge=1),
        limit: int = Query(20, ge=1, le=200),
        db: Session = Depends(get_db),
) -> List[UserListItem]:
    """
    Retrieves a paginated list of users.

    :param page: Page number for pagination.
    :type page: int

    :param limit: Number of results per page.
    :type limit: int

    :param db: Active database session.
    :type db: Session

    :return: A list of users corresponding to the selected page.
    :rtype: list[UserListItem]
    """

    users_list = UserService.list_users(db, page, limit)

    return users_list


@router.get("/{user_id}", response_model=UserDetail, dependencies=[Depends(admin_required)])
def get_user(
        user_id: int,
        db: Session = Depends(get_db),
) -> UserDetail:
    """
    Retrieves detailed information for a specific user.

    :param user_id: ID of the target user.
    :type user_id: int

    :param db: Active database session.
    :type db: Session

    :return: The user details.
    :rtype: UserDetail
    """

    user = UserService.get_user(db, user_id)

    return user


@router.put("/{user_id}", response_model=UserDetail, dependencies=[Depends(admin_required)])
def update_user(
        user_id: int,
        payload: UserUpdate,
        db: Session = Depends(get_db),
) -> UserDetail:
    """
    Updates a user's information.

    :param user_id: ID of the target user.
    :type user_id: int

    :param payload: Fields to update.
    :type payload: UserUpdate

    :param db: Active database session.
    :type db: Session

    :return: The updated user record.
    :rtype: UserDetail
    """

    user_update = UserService.update_user(db, user_id, payload.model_dump(exclude_unset=True))

    return user_update


@router.patch("/{user_id}/disable", response_model=UserDetail, dependencies=[Depends(admin_required)])
def disable_user(
        user_id: int,
        db: Session = Depends(get_db),
) -> UserDetail:
    """
    Disables a user account.

    :param user_id: ID of the user to disable.
    :type user_id: int

    :param db: Active database session.
    :type db: Session

    :return: The updated user record with `is_active` set to False.
    :rtype: UserDetail
    """

    disabled = UserService.disable_user(db, user_id)

    return disabled


@router.patch("/{user_id}/enable", response_model=UserDetail, dependencies=[Depends(admin_required)])
def enable_user(
        user_id: int,
        db: Session = Depends(get_db),
) -> UserDetail:
    """
    Enables a previously disabled user account.

    :param user_id: ID of the user to enable.
    :type user_id: int

    :param db: Active database session.
    :type db: Session

    :return: The updated user record with `is_active` set to True.
    :rtype: UserDetail
    """

    enabled = UserService.enable_user(db, user_id)

    return enabled


@router.delete("/{user_id}", response_model=UserDetail, dependencies=[Depends(superadmin_required)])
def delete_user(
    user_id: int,
    db: Session = Depends(get_db),
) -> UserDetail:
    """
    Permanently deletes a user. Only superadmins may perform this action.

    :param user_id: ID of the user to delete.
    :type user_id: int

    :param db: Active database session.
    :type db: Session

    :raises HTTPException: If the user does not exist.

    :return: Confirmation message.
    :rtype: dict
    """

    user = UserService.get_user(db, user_id)

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    db.delete(user)
    db.commit()

    return {"detail": f"User {user_id} deleted"}


@router.get("/admin/dashboard", dependencies=[Depends(admin_required)])
def admin_dashboard() -> dict:
    """
    Returns a simple response for validating admin access.

    :return: A message confirming access to the admin dashboard.
    :rtype: dict
    """

    return {"message": "Admin dashboard"}


