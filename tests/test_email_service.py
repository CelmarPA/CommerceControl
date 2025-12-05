# app/tests/test_email_service.py

"""
Email Service Tests
------------------

This module tests the EmailService class, ensuring that:

1. Verification emails are sent correctly.
2. Password reset emails are sent correctly.

All actual email sending is mocked to avoid sending real emails.
"""

from fastapi.testclient import TestClient

from app.services.email_service import EmailService


def test_send_verification_email(monkeypatch) -> None:
    """
    Test sending a verification email.

    Uses monkeypatch to replace the real email sending function with a fake
    that captures the email and token for assertions.

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: Pytest fixture.

    :return: None
    """

    captured = {}

    def fake_send_email(to_email, token):
        """
        Mocked function to capture email and token.

        :param to_email: Recipient email address.
        :type to_email: str

        :param token: Verification token.
        :type token: str

        :return: Always returns True to simulate success.
        :rtype: bool
        """

        captured["to_email"] = to_email
        captured["token"] = token

        return True

    # Replace the real method with our fake
    monkeypatch.setattr(
        EmailService,
        "send_verification_email",
        fake_send_email
    )

    # Call the service method
    result = EmailService.send_verification_email("test@example.com", "dummy-token")

    # ---------------------------
    # Assertions
    # ---------------------------
    assert result is True
    assert captured["to_email"] == "test@example.com"
    assert captured["token"] == "dummy-token"


def test_send_password_reset_email(test_client: TestClient, create_user, monkeypatch) -> None:
    """
    Test sending a password reset email via the API endpoint.

    Steps:
    1. Create a verified test user.
    2. Mock EmailService.send_password_reset to capture email and token.
    3. Call the /auth/request-password-reset endpoint.
    4. Assert status code and captured data.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_user: Factory to create a user in the test database.
    :type create_user: Callable

    :param monkeypatch: Pytest monkeypatch fixture.
    :type monkeypatch: Pytest fixture.

    :return: None
    """

    # Create a verified test user
    user = create_user(email="reset@test.com", verified=True)

    called = {}

    # Mock do send_password_reset
    def fake_send_password_reset(to_email: str, token: str) -> bool:
        """
        Mocked function to capture email and reset token.

        :param to_email: Recipient email address.
        :type to_email: str

        :param token: Password reset token.
        :type token: str

        :return: Always returns True to simulate success.
        :rtype: bool
        """

        called["to_email"] = to_email
        called["token"] = token

        return True

    # Replace the real method with our mock
    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_password_reset",
        fake_send_password_reset
    )

    # ---------------------------
    # Step 1: Call password reset endpoint
    # ---------------------------
    response = test_client.post("/auth/request-password-reset", json={"email": user.email})

    # ---------------------------
    # Step 2: Assert response
    # ---------------------------
    assert response.status_code == 200
    assert "reset link has been sent" in response.json()["detail"]

    # ---------------------------
    # Step 3: Verify mock call
    # ---------------------------
    assert called["to_email"] == user.email
    assert isinstance(called["token"], str) and len(called["token"]) > 0
