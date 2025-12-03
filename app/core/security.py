# app/core/security.py

"""
Security and authentication utilities used across the application.

This module handles:
- Password hashing and verification (using passlib/bcrypt)
- JWT access token generation
- JWT token validation and user authentication
- FastAPI HTTP bearer token extraction
"""

from fastapi import HTTPException, status, Depends
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from passlib.context import CryptContext
from datetime import datetime, timedelta, timezone
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.config import settings
from app.database import get_db
from app.models import User


# HTTP Bearer authentication scheme (expects Authorization: Bearer <token>)
security = HTTPBearer()

# Password hashing context using bcrypt (secure and recommended)
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT configuration from application settings
SECRET_KEY: str = settings.SECRET_KEY
ALGORITHM: str = settings.ALGORITHM
ACCESS_TOKEN_EXPIRE_MINUTES: int = settings.ACCESS_TOKEN_EXPIRE_MINUTES


def hash_password(password: str) -> str:
    """
    Hash a plaintext password using bcrypt.

    :param password: The user's plaintext password.
    :type password: str

    :return: The securely hashed password.
    :rtype: str
    """

    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """
    Verify that a plaintext password matches a stored hashed password.

    :param plain_password: User-provided plaintext password.
    :type plain_password: str

    :param hashed_password: Stored bcrypt-hashed password.
    :type hashed_password: str

    :return: True if the password matches, False otherwise.
    :rtype: bool
    """

    return pwd_context.verify(plain_password, hashed_password)


def create_access_token(data: dict, expires_delta: timedelta | None = None) -> str:
    """
    Create a JWT access token with an expiration time.

    :param data: The payload to encode into the token. Must include a "sub" field (subject).
    :type data: dict

    :param expires_delta: Optional custom expiration duration.
    :type expires_delta: timedelta | None

    :return: The encoded JWT token.
    :rtype: str
    """

    to_encode = data.copy()

    # Use custom expiration if provided; otherwise, default application expiry
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta

    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)

    to_encode.update({"exp": expire})

    # Encode the JWT token
    encoded_jwt = jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

    return encoded_jwt


def get_current_user(credentials: HTTPAuthorizationCredentials = Depends(security), db: Session = Depends(get_db)) -> User:
    """
    Extract and validate the current authenticated user from the JWT token.

    This function:
        - Extracts JWT from Authorization header
        - Decodes it
        - Validates expiration and signature
        - Loads the user from the database

    :param credentials: Extracted Authorization header.
    :type credentials: HTTPAuthorizationCredentials

    :param db: SQLAlchemy DB session.
    :type db: Session

    :return: The authenticated user object.
    :rtype: User
    """

    token = credentials.credentials
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
    )

    try:
        # Decode token and validate structure/signature
        payload = jwt.decode(token, SECRET_KEY, algorithms=[ALGORITHM]
                             )
        user_id: str = payload.get("sub")

        if user_id is None:
            raise credentials_exception

    except JWTError:
        # Triggered if token is expired, invalid, or malformed
        raise credentials_exception

    # Query the authenticated user
    user = db.query(User).filter(User.id == user_id).first()

    if user is None:
        raise credentials_exception

    return user
