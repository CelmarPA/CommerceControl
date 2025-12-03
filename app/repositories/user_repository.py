# app/repositories/user_repository.py

"""
Repository layer responsible for managing User records in the database.

This module centralizes all user-related database operations, including:
- Fetching users by email or ID
- Creating user accounts
- Updating passwords and user fields
- Enabling/disabling user accounts
- Listing paginated users

It is used by authentication, admin panels, and general user management logic.
"""

from fastapi import HTTPException
from sqlalchemy import asc
from sqlalchemy.orm import Session
from typing import List

from app.models import User


class UserRepository:
    """
    Repository responsible for database operations related to User entities.
    """

    @staticmethod
    def get_by_email(db: Session, email: str) -> User | None:
        """
        Retrieves a user by their email address.

        :param db: Active database session.
        :type db: Session

        :param email: Email address to search for.
        :type email: str

        :return: The matching user if found, otherwise None.
        :rtype: User | None
        """

        return db.query(User).filter(User.email == email).first()

    @staticmethod
    def get_by_id(db: Session, user_id: int) -> User | None:
        """
        Retrieves a user by their unique ID.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user.
        :type user_id: int

        :return: The matching user if found, otherwise None.
        :rtype: User | None
        """

        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def count(db: Session) -> int:
        """
        Returns the total number of registered users.

        :param db: Active database session.
        :type db: Session

        :return: Total user count.
        :rtype: int
        """

        return db.query(User).count()

    @staticmethod
    def create_user(db: Session, email: str, hashed_password: str, role: str) -> User:
        """
        Creates a new user.

        :param db: Active database session.
        :type db: Session

        :param email: User email.
        :type email: str

        :param hashed_password: Securely hashed password.
        :type hashed_password: str

        :param role: Role assigned to the user (e.g., 'user', 'admin').
        :type role: str

        :return: The newly created user instance.
        :rtype: User
        """

        user = User(email=email, hashed_password=hashed_password, role=role)
        db.add(user)
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def update_password(db: Session, user_id: int, hashed_password: str) -> User:
        """
        Updates a user's password.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user whose password will be changed.
        :type user_id: int

        :param hashed_password: New hashed password.
        :type hashed_password: str

        :return: The updated user, or None if not found.
        :rtype: User | None
        """

        user = db.query(User).filter(User.id == user_id).first()

        if user:
            user.hashed_password = hashed_password
            db.commit()

        return user

    @staticmethod
    def list(db: Session, skip: int = 0, limit: int = 20) -> List[User]:
        """
        Retrieves a paginated list of users.

        :param db: Active database session.
        :type db: Session

        :param skip: Number of records to skip (for pagination).
        :type skip: int

        :param limit: Maximum number of users to return.
        :type limit: int

        :return: List of User objects.
        :rtype: list[User]
        """

        user_list = (
            db.query(User)
            .order_by(asc(User.id))
            .offset(skip)
            .limit(limit)
            .all()
        )

        return user_list

    @staticmethod
    def get(db: Session, user_id: int) -> User | None:
        """
        Retrieves a user by ID (alias for get_by_id).

        :param db: Active database session.
        :type db: Session

        :param user_id: User ID to search for.
        :type user_id: int

        :return: The matching user or None.
        :rtype: User | None
        """
        return db.query(User).filter(User.id == user_id).first()

    @staticmethod
    def update(db: Session, user: User, data: dict) -> User:
        """
        Updates user fields dynamically.

        :param db: Active database session.
        :type db: Session

        :param user: The user object to be updated.
        :type user: User

        :param data: Dictionary containing fields and their new values.
        :type data: dict

        :raises HTTPException: If email is already in use by another user.

        :return: Updated user instance.
        :rtype: User
        """

        if "email" in data:
            exists = db.query(User).filter(
                User.email == data["email"],
                User.id == user.id
            ).first()

            if exists:
                raise HTTPException(
                    status_code=400,
                    detail="Email already in use by another user"
                )

        for field, value in data.items():
            setattr(user, field, value)

        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def disable(db: Session, user: User) -> User:
        """
        Disables a user account.

        :param db: Active database session.
        :type db: Session

        :param user: User instance to disable.
        :type user: User

        :return: Updated user instance.
        :rtype: User
        """
        user.is_active = False
        db.commit()
        db.refresh(user)

        return user

    @staticmethod
    def enable(db: Session, user: User) -> User:
        """
        Enables a previously disabled user account.

        :param db: Active database session.
        :type db: Session

        :param user: User instance to enable.
        :type user: User

        :return: Updated user instance.
        :rtype: User
        """

        user.is_active = True
        db.commit()
        db.refresh(user)

        return user
