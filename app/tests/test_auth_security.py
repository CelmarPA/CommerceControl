# app/tests/test_auth_security.py

"""
Authentication Security Tests
-----------------------------

This module tests security-related scenarios for authentication endpoints.

Tests included:
- test_access_token_invalid: Ensure that an invalid JWT access token is rejected.
"""

from fastapi.testclient import TestClient


def test_access_token_invalid(test_client: TestClient):
    """
    Test that an invalid access token is rejected by protected endpoints.

    Steps:
    1. Define a deliberately invalid JWT token string.
    2. Attempt to access the '/auth/me' endpoint with this token.
    3. Assert that the response status code is 401 Unauthorized.

    :param test_client: TestClient fixture for API requests.
    """

    bad_token = "abc.def.ghi"
    response = test_client.get(
        "/auth/me",
        headers={"Authorization": f"Bearer {bad_token}"}
    )
    assert response.status_code == 401
