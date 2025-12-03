# app/core/config.py

"""
Application configuration module.

This module defines the Settings class, which centralizes environment-based
configuration for the entire application. It loads values from environment
variables using Pydantic Settings, making the configuration type-safe,
validated, and easy to override in different environments.

The configuration includes security keys, database URL, token expiration
settings, CORS policy, and external integrations such as the Brevo API.
"""

from typing import List
from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """
    Global application settings loaded from environment variables.

    This class centralizes all configuration used by the application.
    It is based on Pydantic Settings, which automatically loads values
    from a `.env` file or from system environment variables. All fields
    are validated and converted to the appropriate types, ensuring
    type-safe and consistent configuration across environments.

    Attributes
    ----------
    ENVIRONMENT : str
        Name of the current runtime environment
        (e.g., "development", "production").

    SECRET_KEY : str
        Secret key used for signing JWT tokens.

    ALGORITHM : str
        Cryptographic algorithm used to generate JWT tokens.

    ACCESS_TOKEN_EXPIRE_MINUTES : int
        Expiration time (in minutes) for access tokens.

    REFRESH_TOKEN_EXPIRE_DAYS : int
        Expiration time (in days) for refresh tokens.

    DATABASE_URL : str
        SQLAlchemy database connection URL.

    CORS_ORIGINS : List[str]
        List of allowed origins for CORS requests.

    BREVO_API_KEY : str
        API key for the Brevo email service.

    MAIL_SENDER : str
        Default email address used as the sender for outgoing emails.

    FRONTEND_URL : str
        Base URL of the frontend application.
    """


    ENVIRONMENT: str = "development"

    # ------------------------------------------------------------------
    # Security and JWT
    # ------------------------------------------------------------------
    SECRET_KEY: str
    ALGORITHM: str = 'HS256'

    # ------------------------------------------------------------------
    # Token expiration settings
    # ------------------------------------------------------------------
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7

    # ------------------------------------------------------------------
    # Database
    # ------------------------------------------------------------------
    DATABASE_URL: str

    # ------------------------------------------------------------------
    # CORS Configuration
    # ------------------------------------------------------------------
    CORS_ORIGINS: List[str] = Field(
        default_factory=list,
        description="List of allowed CORS origins."
    )

    # ------------------------------------------------------------------
    # External Services (Brevo API)
    # ------------------------------------------------------------------
    BREVO_API_KEY: str
    MAIL_SENDER: str
    FRONTEND_URL: str

    # Settings configuration
    model_config = SettingsConfigDict(env_file=".env")


# ----------------------------------------------------------------------
# Settings Singleton
# ----------------------------------------------------------------------
# This instantiates a single configuration object to be imported
# throughout the application.
settings = Settings()       # type: ignore[call-arg]
