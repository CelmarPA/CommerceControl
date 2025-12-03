# app/store/tokens.py

"""
Token generation and storage utilities.

This module provides secure helper functions for managing:
- Refresh tokens (hashed before storage)
- Token database records
- Email verification tokens (JWT-based)

It follows security best practices:
- Refresh tokens are never stored in plaintext.
- Only SHA-256 hashes are persisted.
- Expiration timestamps use UTC for audit consistency.
"""

import hashlib
import secrets
from datetime import datetime, timedelta, timezone
from typing import Dict, Any
from jose import jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.models import RefreshToken


REFRESH_TOKEN_EXPIRE_DAYS: int = settings.REFRESH_TOKEN_EXPIRE_DAYS


def generate_refresh_token_plain() -> Dict[str, Any]:
    """
    Generate a new secure plaintext refresh token and its metadata.

    :return: Containing:
                 - plain (str): The raw token returned to the client.
                 - hash (str): SHA-256 hash to be stored in the database.
                 - expires_at (datetime): Token expiration timestamp (UTC).
    :rtype: Dict

    . note::
        - The plaintext token must NEVER be stored in the database.
        - Only the hash is persisted for security reasons.
    """

    plain: str = secrets.token_urlsafe(48)
    expires_at = datetime.now(timezone.utc) + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    return {
        "plain": plain,
        "hash": hash_token(plain),
        "expires_at": expires_at
    }


def hash_token(token: str) -> str:
    """
    Return the SHA-256 hash of a refresh token.

    :param token: Plaintext refresh token.
    :type token: str

    :return: Hexadecimal digest.
    :rtype: str

    . warning::
        Security: Using SHA-256 prevents attackers from impersonating users even if the database is compromised.
    """

    return hashlib.sha256(token.encode()).hexdigest()


def make_refresh_record(db: Session, user_id: int, plain_token: str) -> RefreshToken:
    """
    Store a new refresh token record in the database.

    :param db: Active SQLAlchemy session.
    :type db: Session

    :param user_id: Owner of the refresh token.
    :type user_id: int

    :param plain_token: Raw token string returned to the user. Only the hash is stored.
    :type plain_token: str

    :return: Persisted database record.
    :rtype: RefreshToken

    . note::
        The function commits the session and refreshes the instance.
    """

    token_hash: str = hash_token(plain_token)
    now = datetime.now(timezone.utc)
    expires = now + timedelta(days=REFRESH_TOKEN_EXPIRE_DAYS)

    rec = RefreshToken(
        user_id=user_id,
        token_hash=token_hash,
        expires_at=expires,
        revoked=False,
    )

    db.add(rec)
    db.commit()
    db.refresh(rec)

    return rec


def create_email_verification_token(user_id: int) -> str:
    """
    Create a JWT token used for validating email ownership.

    :param user_id: ID of the user being verified.
    :type user_id: int

    :return: Encoded JWT containing:
                - sub: User ID
                - exp: Expiration timestamp (24 hours from now)
    :rtype: str

    . note::
        Email verification tokens are short-lived. They do not need refresh rotation behavior.
    """

    expires_at = datetime.now(timezone.utc) + timedelta(hours=24)

    payload = {
        "sub": str(user_id),
        "exp": expires_at
    }

    return jwt.encode(
        payload,
        settings.SECRET_KEY,
        algorithm="HS256"
    )
