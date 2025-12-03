# app/model/user.py

"""
Database model representing application users.

This table stores core user account data, including authentication details,
roles, and verification status. It is used for:
- Authentication and session management
- Role-based access control (RBAC)
- Tracking account status (active, verified, etc.)
- Relating users to refresh tokens or other dependent tables
"""

from sqlalchemy import Column, Integer, String, Boolean
from sqlalchemy.orm import relationship

from app.database import Base


class User(Base):
    """
    Represents an application user account.

    :param id: Primary key of the user.
    :type id: int

    :param email: User's unique email address.
    :type email: str

    :param hashed_password: Encrypted user password.
    :type hashed_password: str

    :param role: User access role (e.g., 'user', 'admin', 'superadmin').
    :type role: str

    :param is_verified: Indicates whether the user's email has been verified.
    :type is_verified: bool

    :param is_active: Indicates whether the account is active.
    :type is_active: bool

    :param refresh_tokens: List of refresh tokens associated with the user.
    :type refresh_tokens: list[RefreshToken]
    """

    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email= Column(String, unique=True, nullable=False, index=True)
    hashed_password = Column(String, nullable=False)
    role = Column(String, default="user")
    is_verified = Column(Boolean, default=False)
    is_active = Column(Boolean, default=True)


    refresh_tokens = relationship("RefreshToken", back_populates="user")
