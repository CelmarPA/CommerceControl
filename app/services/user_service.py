# app/services/user_service.py

"""
User Service
------------

Handles business logic related to users. All methods delegate database operations
to the UserRepository, adding necessary checks and validations.
"""

from sqlalchemy.orm import Session
from fastapi import HTTPException
from typing import List

from app.models import User
from app.repositories.user_repository import UserRepository


class UserService:
    """
    Service responsible for user-related operations, including listing, fetching,
    updating, enabling, and disabling users.
    """

    @staticmethod
    def list_users(db: Session, page: int, limit: int) -> List[User]:
        """
        List users with pagination.

        :param db: Active database session.
        :type db: Session

        :param page: Page number (1-indexed).
        :type page: int

        :param limit: Number of users per page.
        :type limit: int

        :return: List of users.
        :rtype: List[User]
        """

        skip = (page - 1) * limit
        users = UserRepository.list(db, skip, limit)

        return users

    @staticmethod
    def get_user(db: Session, user_id: int) -> User:
        """
        Retrieve a user by ID.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user to retrieve.
        :type user_id: int

        :raises HTTPException: If user not found (404).

        :return: User object.
        :rtype: User
        """

        user = UserRepository.get(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return user

    @staticmethod
    def update_user(db: Session, user_id: int, data: dict) -> User:
        """
        Update a user's attributes.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user to update.
        :type user_id: int

        :param data: Dictionary of fields to update.
        :type data: dict

        :raises HTTPException: If user not found (404).

        :return: Updated user object.
        :rtype: User
        """

        user = UserRepository.get(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserRepository.update(db, user, data)

    @staticmethod
    def disable_user(db: Session, user_id: int) -> User:
        """
        Disable a user account (set is_active=False).

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user to disable.
        :type user_id: int

        :raises HTTPException: If user not found (404).

        :return: Disabled user object.
        :rtype: User
        """

        user = UserRepository.get(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserRepository.disable(db, user)

    @staticmethod
    def enable_user(db: Session, user_id: int) -> User:
        """
        Enable a user account (set is_active=True).

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user to enable.
        :type user_id: int

        :raises HTTPException: If user not found (404).

        :return: Enabled user object.
        :rtype: User
        """

        user = UserRepository.get(db, user_id)

        if not user:
            raise HTTPException(status_code=404, detail="User not found")

        return UserRepository.enable(db, user)
