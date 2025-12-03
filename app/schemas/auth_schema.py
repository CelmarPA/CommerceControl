# app/schemas/auth_schema.py

"""
Authentication Schemas
----------------------

Pydantic models used for authentication input/output handling.

Includes:
- Login payload
- Logout request payload
"""

from pydantic import BaseModel, EmailStr

class Login(BaseModel):
    """
    Schema for user login input.

    :param email: User email address.
    :type email: EmailStr

    :param password: User plaintext password.
    :type password: str
    """

    email: EmailStr
    password: str


class LogoutRequest(BaseModel):
    """
    Schema for logout input.

    :param refresh_token: Refresh token to be revoked.
    :type refresh_token: str
    """

    refresh_token: str
