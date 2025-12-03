# app/routers/auth.py

"""
Authentication Router
---------------------

This module exposes all authentication-related endpoints, including:

- User registration
- Login with token generation
- Refresh token rotation
- Logout with refresh token revocation
- Password reset flows (request + reset)
- Email verification
- Fetching the authenticated user's profile

All business logic is delegated to AuthService, keeping the router focused
on request/response responsibilities.
"""

from fastapi import APIRouter, Depends, Request, Body, status, HTTPException
from jose import jwt
from pydantic import EmailStr
from sqlalchemy.orm import Session

from app.core.tokens import create_email_verification_token
from app.database import get_db
from app.core.security import get_current_user
from app.core.rate_limit import limiter
from app.core.config import settings
from app.models import User
from app.repositories import UserRepository
from app.schemas.auth_schema import LogoutRequest
from app.schemas.token_schema import RefreshTokenRequest
from app.services.auth_service import AuthService
from app.services.email_service import EmailService

from app.schemas import (
    UserCreate, UserResponse, Login, Token, Message,
    PasswordResetRequest, PasswordResetInput
)


router = APIRouter(prefix="/auth", tags=["Auth"])


@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register_user(user_data: UserCreate, request: Request, db: Session = Depends(get_db)):
    """
    Register a new user.

    First user created -> superadmin
    Second user created -> admin
    All others -> user

    :param user_data: Registration input containing email + password.
    :type user_data: UserCreate

    :param request: Incoming HTTP request.
    :type request: Request

    :param db: Active database session.
    :type db: Session

    :return: Newly created user.
    :rtype: UserResponse
    """

    user = AuthService.register(
        db=db,
        email=user_data.email,
        password=user_data.password,
        request=request
    )

    return user


@router.post("/login", response_model=Token)
@limiter.limit("5/minute")
def login(
    request: Request,
    user_data: Login,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user using email and password.

    Returns both access and refresh tokens.
    Protected by rate-limiting (5 per minute).

    :param request: Incoming HTTP request (used for logging and rate-limit context).
    :type request: Request

    :param user_data: User login credentials.
    :type user_data: Login

    :param db: Active database session.
    :type db: Session

    :return: JWT access token and refresh token.
    :rtype: Token
    """

    result = AuthService.login(
        db,
        email=user_data.email,
        password=user_data.password,
        ip=request.client.host,
        request=request)

    return result


@router.post("/refresh", response_model=Token)
def refresh_token(payload: RefreshTokenRequest, request: Request, db: Session = Depends(get_db)) -> Token:
    """
    Rotate and validate a refresh token, returning new access and refresh tokens.

    :param payload: The refresh token input.
    :type payload: RefreshTokenRequest

    :param request: Incoming HTTP request.
    :type request: Request

    :param db: Active database session.
    :type db: Session

    :return: New access + refresh tokens.
    :rtype: Token
    """

    result = AuthService.refresh(
        db=db,
        refresh_token=payload.refresh_token,
        request=request
    )

    return result


@router.post("/logout", response_model=Message)
def logout(data: LogoutRequest, request: Request, db: Session = Depends(get_db)) -> Message:
    """
    Logout the user by revoking the provided refresh token.

    :param data: Request containing refresh token.
    :type data: LogoutRequest

    :param request: Incoming HTTP request.
    :type request: Request

    :param db: Active database session.
    :type db: Session

    :return: Success message.
    :rtype: Message
    """

    result = AuthService.logout(
        db=db,
        refresh_token=data.refresh_token,
        request=request
    )

    return result


@router.post("/request-password-reset", response_model=Message)
def request_password_reset(data: PasswordResetRequest, request: Request, db: Session = Depends(get_db)) -> Message:
    """
    Request a password reset email.

    Always returns a generic success message to avoid account enumeration.

    :param data: Contains the email to send the reset link to.
    :type data: PasswordResetRequest

    :param request: Incoming HTTP request.
    :type request: Request

    :param db: Active database session.
    :type db: Session

    :return: Generic success message.
    :rtype: Message
    """

    result = AuthService.request_password_reset(
        db=db,
        email=data.email,
        request=request
    )

    return result


@router.post("/reset-password", response_model=Message)
def reset_password(data: PasswordResetInput, request: Request, db: Session = Depends(get_db)) -> Message:
    """
    Reset a user's password using a password reset token.

    :param data: Contains reset token + new password.
    :type data: PasswordResetInput

    :param request: Incoming HTTP request.
    :type request: Request

    :param db: Active database session.
    :type db: Session

    :return: Confirmation message.
    :rtype: Message
    """

    result = AuthService.reset_password(
        db=db,
        token=data.token,
        new_password=data.new_password,
        request=request
    )

    return result


@router.get("/me", response_model=UserResponse)
def me(current_user=Depends(get_current_user)) -> UserResponse:
    """
    Return the currently authenticated user.

    :param current_user: The user extracted from the access token.
    :type current_user: User

    :return: The authenticated user's profile.
    :rtype: UserResponse
    """

    return current_user


@router.post("/send-verification-email", response_model=Message)
def send_email_verification(email: EmailStr = Body(...), db: Session = Depends(get_db)) -> Message:
    """
    Send a verification email to a user, if the account is not already verified.

    Does not reveal if the user exists.

    :param email: Email address to verify.
    :type email: EmailStr

    :param db: Active database session.
    :type db: Session

    :return: Success message.
    :rtype: Message
    """

    email = str(email).lower().strip()

    user = UserRepository.get_by_email(db, email)

    if not user:
        return {"detail": "If the email exists, verification email was sent"}

    if user.is_verified:
        return {"detail": "Email already verified"}

    token = create_email_verification_token(user.id)

    EmailService.send_verification_email(user.email, token)

    return {"detail": "Verification email sent"}


@router.get("/verify-email", response_model=Message)
def verify_email(token: str, db: Session = Depends(get_db)) -> Message:
    """
    Verify a user's email using a JWT token.

    :param token: Verification token sent to the user's email.
    :type token: str

    :param db: Active database session.
    :type db: Session

    :raises HTTPException: If the token is invalid or user does not exist.

    :return: Confirmation message.
    :rtype: Message
    """

    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=["HS256"])
        user_id = int(payload["sub"])

    except HTTPException:
        raise

    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid or expired token: {e}")

    user = db.query(User).filter(User.id == user_id).first()

    if not user:
        raise HTTPException(status_code=404, detail="User not found")

    user.is_verified = True
    db.commit()
    db.refresh(user)

    return {"detail": "Email verified successfully"}
