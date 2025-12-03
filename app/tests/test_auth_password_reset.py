# app/tests/test_auth_password_reset.py

"""
Password Reset Flow Tests
-------------------------

This module tests the complete password reset workflow:

1. Requesting a password reset (generates a token and sends email)
2. Resetting the password using the token
3. Logging in with the new password

The email sending is mocked to avoid sending real emails.
"""

from _pytest.monkeypatch import MonkeyPatch
from starlette.testclient import TestClient
from typing import Callable


def test_reset_password_flow(test_client: TestClient, create_user: Callable, monkeypatch: MonkeyPatch) -> MonkeyPatch:
    """
    Tests the end-to-end password reset process.

    Steps:
    1. Request a password reset and capture the token via monkeypatch.
    2. Reset the password using the captured token.
    3. Attempt to log in with the new password.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_user: Factory to create a user in the test database.
    :type create_user: Callable

    :param monkeypatch: Pytest monkeypatch fixture to mock functions.
    :type monkeypatch: MonkeyPatch
    """

    # Create a verified test user
    user = create_user(email="reset@test.com", verified=True)

    # Dictionary to capture the reset token
    captured = {}

    def fake_send_password_reset(to_email: str, reset_token: str) -> bool:
        """
        Mocked method to capture the password reset token
        instead of sending a real email.

        :param to_email: Email to send the password reset email to.
        :type to_email: str

        :param reset_token: Password reset token.
        :type reset_token: str

        :return: Always return True.
        :rtype: bool
        """

        _email = to_email
        captured["token"] = reset_token

        return True

    # Replace the real email sending method with our mock
    monkeypatch.setattr(
        "app.services.email_service.EmailService.send_password_reset",
        fake_send_password_reset
    )

    # ---------------------------
    # Step 1: Request password reset
    # ---------------------------
    response = test_client.post(
        "/auth/request-password-reset",
        json={"email": user.email}
    )

    assert response.status_code == 200

    # Verify that the token was captured
    token = captured["token"]
    assert token is not None

    # ---------------------------
    # Step 2: Reset password using the token
    # ---------------------------
    new_password = "newpassword123"
    response = test_client.post(
        "/auth/reset-password",
        json={"token": token, "new_password": new_password}
    )

    assert response.status_code == 200

    # Accept either response message: email sent or password updated
    assert (
            "reset link has been sent" in response.json()["detail"] or
            "Password updated successfully" in response.json()["detail"]
    )

    # ---------------------------
    # Step 3: Attempt login with new password
    # ---------------------------
    login_resp = test_client.post(
        "/auth/login",
        json={"email": user.email, "password": new_password}
    )

    assert login_resp.status_code == 200
    assert "access_token" in login_resp.json()
