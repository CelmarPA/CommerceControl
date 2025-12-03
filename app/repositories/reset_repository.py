# app/repositories/reset_repository.py

"""
Repository layer for managing password reset tokens.

This module provides database operations for the ResetToken model, including:
- Creating new reset tokens
- Retrieving valid (non-used, non-expired) tokens
- Marking tokens as used

These methods are used by the password reset workflow to ensure token
validation, expiration enforcement, and single-use behavior.
"""

from sqlalchemy.orm import Session
from datetime import datetime, timezone

from app.models import ResetToken
from app.core.tokens import hash_token


class ResetRepository:
    """
    Repository responsible for interacting with ResetToken entries in the database.
    """

    @staticmethod
    def create(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> ResetToken:
        """
        Creates a new password reset token record.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user receiving the reset token.
        :type user_id: int

        :param token_hash: Hashed token value to be stored securely.
        :type token_hash: str

        :param expires_at: Datetime (UTC) when the token becomes invalid.
        :type expires_at: datetime

        :return: The created ResetToken instance.
        :rtype: ResetToken
        """

        rec = ResetToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        db.add(rec)
        db.commit()
        db.refresh(rec)

        return rec

    @staticmethod
    def get_valid(db: Session, token: str) -> ResetToken:
        """
        Retrieves a reset token if it is valid (unused and not expired).

        :param db: Active database session.
        :type db: Session

        :param token: Raw reset token provided by the user.
        :type token: str

        :return: The valid ResetToken instance, or None if not found or invalid.
        :rtype: ResetToken | None
        """

        token_hash = hash_token(token)
        now = datetime.now(timezone.utc)

        reset_token = db.query(ResetToken).filter(
            ResetToken.token_hash == token_hash,
            ResetToken.used == False,
            ResetToken.expires_at >= now
        ).first()

        return reset_token

    @staticmethod
    def mark_used(db: Session, token: str) -> ResetToken:
        """
        Marks a reset token as used, making it unusable for future operations.

        :param db: Active database session.
        :type db: Session

        :param token: Raw reset token to be marked as used.
        :type token: str

        :return: The ResetToken record after being updated, or None if not found.
        :rtype: ResetToken | None
        """

        token_hash = hash_token(token)
        rec = db.query(ResetToken).filter(
            ResetToken.token_hash == token_hash
        ).first()

        if rec:
            rec.used = True
            db.commit()

        return rec
