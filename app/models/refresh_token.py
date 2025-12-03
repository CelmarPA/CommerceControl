# app/models/refresh_token.py
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


class RefreshToken(Base):
    """
    Represents a stored refresh token used for session renewal.

    :param id: Primary key of the refresh token entry.
    :type id: int

    :param user_id: ID of the user to whom the refresh token belongs.
    :type user_id: int

    :param token_hash: Hashed representation of the refresh token for secure storage.
    :type token_hash: str

    :param revoked: Indicates whether the token has been revoked and is no longer valid.
    :type revoked: bool

    :param created_at: Timestamp (UTC) indicating when the token was created.
    :type created_at: datetime

    :param expires_at: Timestamp (UTC) indicating when the token expires.
    :type expires_at: datetime

    :param replaced_by: ID of another token that replaced this one, if applicable.
    :type replaced_by: int | None
    """

    __tablename__ = "refresh_tokens"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"),  nullable=False)
    token_hash = Column(String, nullable=False, unique=True, index=True)
    revoked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    expires_at = Column(DateTime(timezone=True), nullable=False)
    replaced_by = Column(Integer, nullable=True)

    user = relationship("User", back_populates="refresh_tokens")
