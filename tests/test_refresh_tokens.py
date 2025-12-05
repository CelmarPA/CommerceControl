# app/tests/test_refresh_tokens.py

"""
Refresh Token Tests
-------------------

This module tests the refresh token functionality of the authentication system.

Tests include:
1. Valid refresh token returns new access and refresh tokens.
2. Expired refresh token returns 401 Unauthorized.

All tests use manually created refresh tokens in the test database.
"""

from datetime import datetime, timedelta, timezone
from fastapi.testclient import TestClient
from typing import Callable

from app.repositories import TokenRepository
from app.core.tokens import hash_token
from tests.conftest import TestingSessionLocal, create_user


def test_refresh_token_valid(test_client: TestClient, create_user: Callable) -> None:
    """
    Test refreshing an access token using a valid refresh token.

    Steps:
    1. Create a verified test user.
    2. Create a valid refresh token in the database for that user.
    3. Call the /auth/refresh endpoint with the valid token.
    4. Assert that the response status code is 200.
    5. Assert that response contains access_token, refresh_token, and token_type.

    :param test_client: FastAPI TestClient instance for making API requests.
    :type test_client: TestClient

    :param create_user: Factory function to create a user in the test database.
    :type create_user: Callable

    :return: None
    """

    db = TestingSessionLocal()
    user = create_user(email="valid@test.com", verified=True)

    plain_token = "validtoken123"
    hashed_token = hash_token(plain_token)
    expires_at = datetime.now(timezone.utc) + timedelta(minutes=5)

    TokenRepository.create_refresh(db, user.id, hashed_token, expires_at)

    # Tries to use the valid token
    response = test_client.post("/auth/refresh", json={"refresh_token": plain_token})

    assert response.status_code == 200

    data = response.json()

    assert "access_token" in data
    assert "refresh_token" in data
    assert data["token_type"] == "Bearer"

    db.close()


def test_refresh_token_expired(test_client: TestClient, create_user: Callable) -> None:
    """
    Test that using an expired refresh token returns a 401 Unauthorized error.

    Steps:
    1. Create a verified test user.
    2. Create a refresh token in the past (expired) for that user.
    3. Call the /auth/refresh endpoint with the expired token.
    4. Assert that the response status code is 401.
    5. Assert that response detail contains "Invalid or expired refresh token".

    :param test_client: FastAPI TestClient instance for making API requests.
    :type test_client: TestClient

    :param create_user: Factory function to create a user in the test database.
    :type create_user: Callable

    :return: None
    """

    db = TestingSessionLocal()

    user = create_user(email="expired@test.com", verified=True)

    # Create refresh expired refresh token
    plain_token = "expiredtoken123"
    hashed_token = hash_token(plain_token)
    expires_at = datetime.now(timezone.utc) - timedelta(minutes=1)  # Already expired

    TokenRepository.create_refresh(db, user.id, hashed_token, expires_at)

    # Tries to use the expired token
    response = test_client.post("/auth/refresh", json={"refresh_token": plain_token})

    assert response.status_code == 401
    assert "Invalid or expired refresh token" in response.json()["detail"]

    db.close()
