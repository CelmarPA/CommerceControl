# app/tests/test_auth_refresh.py

"""
Refresh Token Endpoint Tests
----------------------------

This module contains tests for the refresh token functionality of the authentication API.

Tests included:
- test_refresh_token: Verify that a valid refresh token can be used
  to obtain new access and refresh tokens.
"""

from fastapi.testclient import TestClient
from typing import Callable


def test_refresh_token(test_client: TestClient, create_user: Callable, login_user: Callable) -> None:
    """
    Test that a refresh token can be used to get new tokens.

    Steps:
    1. Create a verified user.
    2. Log in the user to obtain access and refresh tokens.
    3. Call the /auth/refresh endpoint with the refresh token.
    4. Verify that the response status is 200.
    5. Check that the response contains a new access token.

    :param test_client: FastAPI TestClient instance for making requests
    :type test_client: TestClient

    :param create_user: Factory fixture to create a test user
    :type create_user: Callable

    :param login_user: Fixture to log in a user and obtain tokens
    :type login_user: Callable

    :return: None
    """

    # Step 1: create a verified user
    user = create_user(email="refresh_user@test.com", verified=True)

    # Step 2: log in to obtain tokens
    tokens = login_user(user.email, "123456")
    refresh_token = tokens.get("refresh_token")
    assert refresh_token is not None

    # Step 3: call refresh endpoint
    response = test_client.post("/auth/refresh", json={"refresh_token": refresh_token})

    # Step 4: assert HTTP status
    assert response.status_code == 200

    # Step 5: verify response contains new access token
    data = response.json()
    assert "access_token" in data
