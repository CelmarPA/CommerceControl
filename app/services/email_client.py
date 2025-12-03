# app/services/email_client.py

"""
Email Client
------------

This module provides a simple wrapper around the Brevo (formerly SendinBlue) SMTP API
for sending transactional emails from the application.

It abstracts the HTTP requests, allowing other services to send emails without
dealing directly with the HTTP client or API details.
"""

import requests

from app.core.config import settings


class EmailClient:
    """
    A client class for sending emails via the Brevo API.

    All methods are static, so there is no need to instantiate this class.
    """

    @staticmethod
    def send_email(to_email: str, subject: str, html_content: str) -> bool:
        """
        Send an email using the Brevo API.

        :param to_email: Recipient email address.
        :type to_email: str

        :param subject: Subject line of the email.
        :type subject: str

        :param html_content: HTML content of the email body.
        :type html_content: str

        :return: True if the email was sent successfully (HTTP 201), False otherwise.
        :rtype: bool

        :raises requests.RequestException: If the HTTP request fails due to network or other issues.
        """

        # Construct the payload according to Brevo's API requirements
        payload = {
            'sender': {
                "name": "Auth API",
                "email": settings.MAIL_SENDER,
            },
            "to": [{"email": to_email}],
            "subject": subject,
            "htmlContent": html_content
        }

        # HTTP headers with API key authentication
        headers = {
            "api-key": settings.BREVO_API_KEY,
            "Content-Type": "application/json"
        }

        # Send POST request to Brevo API endpoint
        response = requests.post(
            "https://api.brevo.com/v3/smtp/email",
            json=payload,
            headers=headers
        )

        # Return True if API responded with 201 Created, else False
        return response.status_code == 201
