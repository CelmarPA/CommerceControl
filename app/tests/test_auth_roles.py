# app/tests/test_auth_roles.py

"""
User Roles and Permissions Tests
--------------------------------

This module tests role-based access control (RBAC) for protected routes.

Tests included:
- test_admin_route_forbidden: Ensure a regular user cannot access admin-only endpoints.
"""

from fastapi.testclient import TestClient


def test_admin_rout_forbidden(test_client: TestClient, create_user):
    """
    Test that a non-admin user is forbidden from accessing admin routes.

    Steps:
    1. Create a regular user using the `create_user` fixture.
    2. Log in to obtain an access token.
    3. Attempt to access the admin dashboard with the user's token.
    4. Assert that the response status code is 403 (Forbidden).

    :param test_client: TestClient fixture for API requests.
    """

    create_user("user@test.com")
    login = test_client.post("/auth/login", json={"email": "user@test.com", "password": "123456"})

    token = login.json()["access_token"]

    response = test_client.get(
        "/admin/users/dashboard",
        headers={"Authorization": f"Bearer {token}"}
    )
    assert response.status_code == 403
