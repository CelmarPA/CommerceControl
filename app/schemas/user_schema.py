# app/schemas/user_schema.py

"""
User Schemas
------------

Schemas for representing users in various contexts:
- Listing users
- Detailed user view
- User creation and updates
- API responses

These schemas are used in endpoints for admin management, registration, and profile management.
"""

from pydantic import BaseModel, EmailStr, ConfigDict, Field
from typing import Optional


class UserBase(BaseModel):
    """
   Base schema for user representation.

   :param email: User's email address.
   :type email: EmailStr

   :param role: User's role in the system (e.g., user, admin, superadmin).
   :type role: str

   :param is_verified: Indicates whether the user's email is verified.
   :type is_verified: bool

   :param is_active: Indicates whether the user account is active.
   :type is_active: bool
   """

    email: EmailStr
    role: str
    is_verified: bool
    is_active: bool

    model_config = ConfigDict(from_attributes=True)


class UserListItem(UserBase):
    """
    Schema for listing users.

    :param id: Primary key of the user.
    :type id: int
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class UserDetail(UserBase):
    """
    Schema for detailed user information.

    :param id: Primary key of the user.
    :type id: int
    """

    id: int
    model_config = ConfigDict(from_attributes=True)


class UserUpdate(BaseModel):
    """
    Schema for updating user attributes.

    Fields are optional to allow partial updates.

    :param email: New email address.
    :type email: Optional[EmailStr]

    :param role: New role.
    :type role: Optional[str]

    :param is_active: Account active status.
    :type is_active: Optional[bool]
    """

    email: Optional[EmailStr] = None
    role: Optional[str] = None
    is_active: Optional[bool] = None


class UserCreate(BaseModel):
    """
    Schema for creating a new user.

    :param email: User's email address.
    :type email: EmailStr

    :param password: User's password (minimum length 6).
    :type password: str

    :param role: Optional role assignment.
    :type role: Optional[str]
    """

    email: EmailStr
    password: str = Field(min_length=6)
    role: Optional[str] = None


class UserResponse(BaseModel):
    """
    Schema for returning user data in API responses.

    :param id: Primary key of the user.
    :type id: int

    :param email: User's email address.
    :type email: EmailStr

    :param role: User's role.
    :type role: str
    """

    id: int
    email: EmailStr
    role: str = "User"

    model_config = ConfigDict(from_attributes=True)
