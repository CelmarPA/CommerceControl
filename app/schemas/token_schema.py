


# app/schemas/token_schema.py

"""
Token Schemas
-------------

Schemas for representing access and refresh tokens, and for token rotation requests.
Used in authentication endpoints for login, refresh, and logout operations.
"""

from pydantic import BaseModel


class Token(BaseModel):
    """
    Represents an authentication token pair (access + refresh).

    :param access_token: JWT access token for API authentication.
    :type access_token: str

    :param token_type: Type of token, default is "bearer".
    :type token_type: str

    :param refresh_token: Refresh token used to obtain new access tokens.
    :type refresh_token: str
    """

    access_token: str
    token_type: str = "bearer"
    refresh_token: str


class RefreshTokenRequest(BaseModel):
    """
    Represents a request payload containing a refresh token.

    :param refresh_token: Refresh token provided by the client for rotation.
    :type refresh_token: str
    """
    refresh_token: str
