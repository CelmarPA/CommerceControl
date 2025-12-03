# app/repositories/token_repository.py

"""
Repository layer responsible for managing refresh tokens.

This module centralizes database operations for the RefreshToken model, including:
- Creating new refresh tokens
- Validating tokens by their hashed representation
- Checking token revocation
- Revoking tokens during logout or token rotation

These methods are used by the authentication and session management system.
"""

from sqlalchemy.orm import Session
from datetime import datetime

from app.models import RefreshToken
from app.core.tokens import hash_token


class TokenRepository:
    """
    Repository responsible for operations involving RefreshToken records.
    """

    @staticmethod
    def create_refresh(db: Session, user_id: int, token_hash: str, expires_at: datetime) -> RefreshToken:
        """
        Creates a new refresh token entry.

        :param db: Active database session.
        :type db: Session

        :param user_id: ID of the user that owns the refresh token.
        :type user_id: int

        :param token_hash: Hashed form of the refresh token for secure storage.
        :type token_hash: str

        :param expires_at: Expiration timestamp of the refresh token.
        :type expires_at: datetime

        :return: The newly created RefreshToken entry.
        :rtype: RefreshToken
        """
        token = RefreshToken(
            user_id=user_id,
            token_hash=token_hash,
            expires_at=expires_at
        )

        db.add(token)
        db.commit()
        db.refresh(token)

        return token

    @staticmethod
    def get_by_plain(db: Session, refresh_token: str) -> RefreshToken:
        """
        Retrieves a stored refresh token by hashing its plain text value.

        :param db: Active database session.
        :type db: Session

        :param refresh_token: Plain text refresh token provided by the client.
        :type refresh_token: str

        :return: The matching RefreshToken entry if found, otherwise None.
        :rtype: RefreshToken | None
        """

        token_hash = hash_token(refresh_token)
        token = db.query(RefreshToken).filter(RefreshToken.token_hash == token_hash).first()

        return token

    @staticmethod
    def find_valid(db: Session, refresh_token: str) -> RefreshToken:
        """
        Retrieves a valid (non-revoked) refresh token by hashing the provided token.

        :param db: Active database session.
        :type db: Session

        :param refresh_token: Plain text refresh token provided by the client.
        :type refresh_token: str

        :return: A valid RefreshToken entry if found, otherwise None.
        :rtype: RefreshToken | None
        """

        token_hash = hash_token(refresh_token)
        token = db.query(RefreshToken).filter(
            RefreshToken.token_hash == token_hash,
            RefreshToken.revoked == False
        ).first()

        return token

    @staticmethod
    def revoke(db: Session, token: RefreshToken) -> None:
        """
        Marks a refresh token as revoked.

        :param db: Active database session.
        :type db: Session

        :param token: The token instance to revoke.
        :type token: RefreshToken

        :return: None
        """
        token.revoked = True
        db.add(token)
        db.commit()
