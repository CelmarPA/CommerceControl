# app/services/email_service.py

"""
Email Service
-------------

Provides high-level methods for sending transactional emails, such as:

- Password reset emails
- Email verification emails

Uses the Brevo (formerly SendinBlue) SMTP API to send emails.
This service wraps around EmailClient for sending emails, and can be extended
for other email types in the future.
"""

import requests

from app.core.config import settings
from app.services.email_client import EmailClient


class EmailService:
    """
    Service class responsible for sending different types of emails.

    All methods are static and can be called without creating an instance.
    """

    @staticmethod
    def send_password_reset(to_email: str, token: str) -> bool:
        """
        Send a password reset email to a user.

        :param to_email: Recipient's email address.
        :type to_email: str

        :param token: Password reset token to include in the reset link.
        :type token: str

        :return: True if the email was sent successfully, False otherwise.
        :rtype: bool
        """

        # Construct the reset link pointing to frontend
        url = f"{settings.FRONTEND_URL}/reset-password?token={token}"

        # HTML content of the email
        html_content = f"""
            <h2>Password Reset</h2>
            <p>Click the link below to reset your password:</p>
            <a href="{url}">Reset Password</a>
            <p>This link expires in 15 minutes.</p>
        """

        # Send the email using the EmailClient
        return EmailClient.send_email(to_email, "Password Reset Request", html_content)

    @staticmethod
    def send_verification_email(to_email: str, token: str) -> bool:
        """
        Send an email verification message to a user.

        :param to_email: Recipient's email address.
        :type to_email: str

        :param token: Verification token to include in the verification link.
        :type token: str

        :return: True if the email was sent successfully, False otherwise.
        :rtype: bool
        """

        # Construct the verification link pointing to frontend
        url = f"{settings.FRONTEND_URL}/verify-email?token={token}"

        # Prepare the payload for Brevo API
        payload = {
            "sender": {
                "name": "Auth API",
                "email": settings.MAIL_SENDER
            },
            "to": [
                {"email": to_email}
            ],
            "subject": "Verify Your Email Address",
            "htmlContent": f"""
                <h2>Email Verification</h2>
                <p>Click the link below to verify your email address:</p>
                <a href="{url}">Verify Email</a>
                <p>This link expires in 15 minutes.</p>
            """
        }

        # HTTP headers with API key
        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json"
        }

        # Send POST request to Brevo API
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers
        )

        # Return True if API responded with 201 Created
        return response.status_code == 201
