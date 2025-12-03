# app/model/reset_token.py

"""
Database model for storing refresh tokens.

This table supports secure session renewal by storing hashed refresh tokens.
It is used to:
- Associate refresh tokens with specific users
- Track token revocation
- Enforce expiration rules
- Support rotating refresh token mechanisms

Each entry represents a single stored refresh token.
"""

from sqlalchemy import Column, Integer, String, Boolean, ForeignKey, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime, timezone

from app.database import Base


class ResetToken(Base):
    """
    Represents a password reset token associated with a user.

    :param id: Primary key of the reset token entry.
    :type id: int

    :param user_id: ID of the user to whom the reset token belongs.
    :type user_id: int

    :param token_hash: Secure hash of the reset token (raw token is never stored).
    :type token_hash: str

    :param used: Indicates whether the token has already been used.
    :type used: bool

    :param expires_at: Timestamp (UTC) indicating when the token expires.
    :type expires_at: datetime

    :param created_at: Timestamp (UTC) indicating when the token was generated.
    :type created_at: datetime
    """

    __tablename__ = "reset_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False)

    token_hash = Column(String, nullable=False, unique=True, index=True)
    used = Column(Boolean, default=False)
    expires_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User")
