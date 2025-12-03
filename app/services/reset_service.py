# app/services/reset_service.py

"""
Reset Service
-------------

Provides functionality for password reset tokens, including creation, validation,
and marking tokens as used. Tokens are time-limited and securely hashed for storage.
"""

import secrets
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session

from app.models import ResetToken
from app.repositories import ResetRepository, UserRepository
from app.core.tokens import hash_token


RESET_EXPIRE_MINUTES: int = 15


class ResetService:
    """
    Service responsible for creating, verifying, and marking password reset tokens.
    """

    @staticmethod
    def create_reset_token(db: Session, user_id: int) -> ResetToken:
        """
        Creates a new password reset token for a user and stores its hashed form.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user requesting a password reset.
        :type user_id: int

        :return: The plain text reset token (to be sent via email).
        :rtype: ResetToken
        """

        plain = secrets.token_urlsafe(48)
        token_hash = hash_token(plain)

        expires = datetime.now(timezone.utc) + timedelta(minutes=RESET_EXPIRE_MINUTES)

        ResetRepository.create(db, user_id, token_hash, expires)

        return plain

    @staticmethod
    def verify_reset_token(db: Session, token: str) -> UserRepository | None:
        """
        Verifies if a reset token is valid and returns the associated user.

        :param db: Active database session.
        :type db: Session

        :param token: Plain text reset token.
        :type token: str

        :return: User object if token is valid, None otherwise.
        :rtype: UserRepository | None
        """

        record = ResetRepository.get_valid(db, token)

        if not record:
            return None

        return UserRepository.get_by_id(db, record.user_id)

    @staticmethod
    def mark_used(db: Session, token: str) -> bool:
        """
        Marks a reset token as used to prevent reuse.

        :param db: Active database session.
        :type db: Session

        :param token: Plain text reset token.
        :type token: str

        :return: True if token was successfully marked as used, False otherwise.
        :rtype: bool
        """

        return ResetRepository.mark_used(db, token)
