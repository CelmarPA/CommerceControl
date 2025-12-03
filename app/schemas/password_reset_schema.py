# app/schemas/password_reset_schema.py

"""
Password Reset Schemas
---------------------

Schemas used for handling password reset requests and submissions.
"""

from pydantic import BaseModel, EmailStr


class PasswordResetRequest(BaseModel):
    """
    Schema for requesting a password reset link.

    :param email: Email address of the user requesting password reset.
    :type email: EmailStr
    """

    email: EmailStr


class PasswordResetInput(BaseModel):
    """
    Schema for submitting a new password along with a valid reset token.

    :param token: Password reset token received via email.
    :type token: str

    :param new_password: The new password to set for the user.
    :type new_password: str
    """

    token: str
    new_password: str
