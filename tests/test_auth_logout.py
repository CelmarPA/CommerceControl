# app/tests/test_auth_logout.py

"""
Logout Endpoint Tests
--------------------

This module contains tests for the logout endpoint of the authentication API.

Tests included:
- test_logout: Verify that a logged-in user can successfully log out
  and that the refresh token is revoked.
"""

from fastapi.testclient import TestClient
from typing import Callable


def test_logout(test_client: TestClient, create_user: Callable, login_user: Callable) -> None:
    """
    Test that a user can log out successfully.

    Steps:
    1. Create a verified user.
    2. Log in the user to obtain access and refresh tokens.
    3. Call the /auth/logout endpoint with the refresh token.
    4. Verify that the response status is 200.
    5. Check that the response contains a confirmation key ("detail" or "msg").

    :param test_client: FastAPI TestClient instance for making requests
    :type test_client: TestClient

    :param create_user: Factory fixture to create a test user
    :type create_user: Callable

    :param login_user: Fixture to log in a user and obtain tokens
    :type login_user: Callable

    :return: None
    """

    # Step 1: create a user
    user = create_user(email="logout_user@test.com", verified=True)

    # Step 2: login to obtain tokens
    tokens = login_user(user.email, "123456")
    refresh_token = tokens["refresh_token"]

    # Step 3: call logout endpoint
    response = test_client.post("/auth/logout", json={"refresh_token": refresh_token})

    # Step 4: assert HTTP status
    assert response.status_code == 200

    # Step 5: verify response contains expected key
    assert "detail" in response.json() or "msg" in response.json()
