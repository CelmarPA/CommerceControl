# app/tests/test_auth_register.py

"""
User Registration Tests
-----------------------

This module tests the user registration endpoint of the authentication API.

Test included:
- test_register_user: Ensure a new user can register successfully and receives the expected response.
"""

from fastapi.testclient import TestClient


def test_register_user(test_client: TestClient):
    """
    Test successful user registration.

    Steps:
    1. Send a POST request to /auth/register with email and password.
    2. Assert that the response status code is 201.
    3. Assert that the response contains the correct email and a generated user ID.

    :param test_client: TestClient fixture for API requests.
    """

    payload = {"email": "new@test.com", "password": "123456"}
    response = test_client.post("/auth/register", json=payload)

    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "new@test.com"
    assert "id" in data
