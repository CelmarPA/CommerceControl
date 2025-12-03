# app/services/auth_service.py

"""
Authentication Service
----------------------

Provides core authentication operations:

- User registration with automatic role assignment
- Login with brute-force protection
- Access and refresh token management
- Logout and token revocation
- Password reset requests and password updates

All security events are logged via `log_security_event`.
"""

from datetime import datetime, timezone
from fastapi import HTTPException, status, Request
from sqlalchemy.orm import Session
from typing import Any, Dict

from app.repositories import UserRepository
from app.repositories import TokenRepository
from app.repositories import ResetRepository
from app.core.security_log import log_security_event
from app.core.tokens import generate_refresh_token_plain
from app.services.email_service import EmailService
from app.services.reset_service import ResetService

from app.core.security import (
    hash_password, verify_password,
    create_access_token
)

from app.core.bruteforce import (
    record_login_attempts, clear_failures, too_many_failures_ip, too_many_failures_email
)


class AuthService:
    """
    Service class providing authentication-related methods.
    """

    # ============================
    #           REGISTER
    # ============================
    @staticmethod
    def register(db: Session, email: str, password: str, request: Request) -> Any:
        """
        Register a new user. Role assignment based on total user count:
        - First user => superadmin
        - Second user => admin
        - Others => user

        :param db: Active database session.
        :type db: Session

        :param email: Email address of the new user.
        :type email: str

        :param password: Plain text password of the new user.
        :type password: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Created user instance.
        :rtype: User

        :raises HTTPException: If email is already registered.
        """

        email = email.lower().strip()

        # Check existing
        if UserRepository.get_by_email(db, email):
            raise HTTPException(status.HTTP_400_BAD_REQUEST, "Email already registered")

        # Assign roles based on total users
        count = UserRepository.count(db)

        role = "superadmin" if count == 0 else ("admin" if count == 1 else "user")

        user = UserRepository.create_user(db, email, hash_password(password), role)

        log_security_event(
            db,
            "register_success",
            "success",
            "User registered",
            request,
            user_id=user.id,
            email=email
        )

        return user

    # ============================
    #           Login
    # ============================
    @staticmethod
    def login(db: Session, email: str, password: str, ip: str, request: Request) -> Dict[str, str]:
        """
        Authenticate user with email and password. Applies brute-force protection.

        :param db: Active database session.
        :type db: Session

        :param email: User email.
        :type email: str

        :param password: User password.
        :type password: str

        :param ip: Client IP address.
        :type ip: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Dictionary containing access_token, token_type, and refresh_token.
        :rtype: dict[str, str]

        :raises HTTPException: If credentials are invalid, email not verified, or brute-force limits exceeded.
        """

        email = email.lower().strip()

        # anti-bruteforce - IP
        if too_many_failures_ip(db, ip):
            log_security_event(
                db,
                "ip_blocked",
                "fail",
                "Too many login attempts from this IP",
                request,
                email=email
            )

            raise HTTPException(429, "Too many attempts from this IP")

        # anti-bruteforce - Email
        if too_many_failures_email(db, email):
            log_security_event(
                db,
                "email_blocked",
                "fail",
                "Too many attempts for this email",
                request,
                email=email
            )

            raise HTTPException(429, "Too many attempts for this email")

        user = UserRepository.get_by_email(db, email)

        if not user or not verify_password(password, user.hashed_password):
            record_login_attempts(db, email, ip, success=False)

            log_security_event(
                db,
                "login_failed",
                "fail",
                "Invalid credentials",
                request,
                email=email
            )

            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid credentials")

        if not user.is_verified:
            record_login_attempts(db, email, ip, success=False)

            log_security_event(
                db,
                "login_failed",
                "fail",
                "Email not verified",
                request,
                email=email
            )

            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Email not verified")

        # Success
        clear_failures(db, email, ip)
        record_login_attempts(db, email, ip, success=True)

        log_security_event(
            db,
            "login_success",
            "success",
            "Login successful",
            request,
            user_id=user.id,
            email=email
        )

        access = create_access_token({"sub": str(user.id), "role": user.role})

        refresh = generate_refresh_token_plain()
        TokenRepository.create_refresh(db, user.id, refresh["hash"], refresh["expires_at"])

        return {
            "access_token": access,
            "token_type": "Bearer",
            "refresh_token": refresh["plain"]
        }

    # ============================
    #       REFRESH TOKEN
    # ============================
    @staticmethod
    def refresh(db: Session, refresh_token: str, request: Request) -> Dict[str, str]:
        """
        Rotate refresh token and issue a new access token.

        :param db: Active database session.
        :type db: Session

        :param refresh_token: Refresh token string.
        :type refresh_token: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Dictionary containing new access_token, token_type, and refresh_token.
        :rtype: dict[str, str]

        :raises HTTPException: If refresh token is invalid.
        """

        token_data = TokenRepository.find_valid(db, refresh_token)

        expires_at = token_data.expires_at
        if expires_at.tzinfo is None:  # naive
            expires_at = expires_at.replace(tzinfo=timezone.utc)

        if not token_data or expires_at < datetime.now(timezone.utc):
            log_security_event(
                db,
                "refresh_invalid",
                "fail",
                "Invalid refresh token",
                request
            )

            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid or expired refresh token")

        # Rotate token
        TokenRepository.revoke(db, token_data)

        new_refresh = generate_refresh_token_plain()
        TokenRepository.create_refresh(db, token_data.user_id, new_refresh["hash"], new_refresh["expires_at"])

        access = create_access_token({"sub": str(token_data.user_id)})

        log_security_event(
            db,
            "refresh_success",
            "success",
            "Token rotated successfully",
            request,
            user_id=token_data.user_id
        )

        return {
            "access_token": access,
            "token_type": "Bearer",
            "refresh_token": new_refresh["plain"]
        }

    # ============================
    #            LOGOUT
    # ============================
    @staticmethod
    def logout(db: Session, refresh_token: str, request: Request) -> dict:
        """
        Revoke a refresh token to log the user out.

        :param db: Active database session.
        :type db: Session

        :param refresh_token: Refresh token string.
        :type refresh_token: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Confirmation message.
        :rtype: dict

        :raises HTTPException: If refresh token is invalid.
        """

        token = TokenRepository.get_by_plain(db, refresh_token)

        if not token:
            log_security_event(
                db,
                "logout_invalid",
                "fail",
                "Invalid refresh token",
                request
            )

            raise HTTPException(status.HTTP_401_UNAUTHORIZED, "Invalid refresh token")

        TokenRepository.revoke(db, token)

        log_security_event(
            db,
            "logout_success",
            "success",
            "User logged out",
            request,
            user_id=token.user_id
        )

        return {"detail": "Logged out successfully"}

    # ============================
    #     REQUEST PASSWORD RESET
    # ============================
    @staticmethod
    def request_password_reset(db: Session, email: str, request: Request) -> dict:
        """
        Generate password reset token and send email. Always returns success message
        without revealing existence of the user.

        :param db: Active database session.
        :type db: Session

        :param email: Email to send reset link to.
        :type email: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Confirmation message.
        :rtype: dict
        """

        email = email.lower().strip()

        user = UserRepository.get_by_email(db, email)

        if not user:
            return {"detail": "If the email exists, a reset link will be sent"}

        token = ResetService.create_reset_token(db, user.id)

        EmailService.send_password_reset(email, token)

        log_security_event(
            db,
            "reset_requested",
            "success",
            "Password reset requested",
            request, user_id=user.id
        )

        return {"detail": "If the email exists, a reset link has been sent"}

    # ============================
    #         RESET PASSWORD
    # ============================
    @staticmethod
    def reset_password(db: Session,  token: str, new_password: str, request: Request) -> dict:
        """
        Reset user's password using a valid reset token.

        :param db: Active database session.
        :type db: Session

        :param token: Reset token string.
        :type token: str

        :param new_password: New password to set.
        :type new_password: str

        :param request: FastAPI request object for logging.
        :type request: Request

        :return: Confirmation message.
        :rtype: dict

        :raises HTTPException: If reset token is invalid or expired.
        """

        user = ResetRepository.get_valid(db, token)

        if not user:
            log_security_event(
                db,
                "reset_failed",
                "fail",
                "Invalid or expired reset token",
                request
            )

            raise HTTPException(400, "Invalid or expired reset token")

        UserRepository.update_password(db, user.id, hash_password(new_password))
        ResetService.mark_used(db, token)

        log_security_event(
            db,
            "reset_success",
            "success",
            "Password reset successfully",
            request,
            user_id=user.id
        )

        return {"detail": "Password updated successfully"}
