# app/tests/test_auto_crud.py

"""
Automatic CRUD Tests (CID / CDI)
--------------------------------

This module generates automatic tests for all CRUD endpoints of models,
including role-based access checks (admin/user) and integration with the database.

Models tested:
- Product (can be extended to other models)

The test performs the full CRUD cycle:
1. CREATE
2. READ (list)
3. UPDATE
4. DELETE

Additionally, it verifies role-based restrictions:
- Admin users can perform all actions.
- Regular users are restricted from admin-only actions.
"""

import pytest
from fastapi.testclient import TestClient
from typing import Callable


# --------------------------
# Configuration for automatic CRUD testing
# --------------------------
MODELS_TO_TEST = [
    {
        "name": "Product",
        "route": "/products",
        "create_payload": lambda: {
            "name": "AutoTest Product",
            "description": "Created by auto-test",
            "price": 10.0,
            "stock": 5
        },
        "admin_only": True  # Only admins can create/update/delete
    },
    # Additional models can be added here with the same structure
]

@pytest.mark.parametrize("item", MODELS_TO_TEST)
def test_auto_crud(
    test_client: TestClient,
    create_admin_user: Callable,
    create_user: Callable,
    login_user: Callable,
    item: dict
) -> None:
    """
    Automatic CRUD + Role-Based Access Test.

    This test dynamically checks CRUD operations for the specified model,
    verifying that admin users can fully manage the resource and regular users
    are restricted for admin-only models.

    Steps:
    1. Create admin and regular user accounts.
    2. Login as both users and obtain access tokens.
    3. Admin performs CREATE operation successfully.
    4. If admin_only=True, regular user CREATE should fail.
    5. Admin performs READ operation to list items.
    6. Admin performs UPDATE operation on the created item.
    7. Admin performs DELETE operation on the created item.
    8. Verify that the item is removed from the list after deletion.

    :param test_client: FastAPI TestClient instance for making API requests.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :param create_user: Factory function to create a regular user.
    :type create_user: Callable

    :param login_user: Factory function to perform user login and return tokens.
    :type login_user: Callable

    :param item: Dictionary defining model to test, route, payload, and admin-only flag.
    :type item: dict

    :return: None
    """

    # --------------------------
    # Create admin and regular user
    # --------------------------
    admin = create_admin_user()
    user = create_user()

    admin_token = login_user(admin.email, "123456")["access_token"]
    user_token = login_user(user.email, "123456")["access_token"]

    headers_admin = {"Authorization": f"Bearer {admin_token}"}
    headers_user = {"Authorization": f"Bearer {user_token}"}

    # --------------------------
    # CREATE
    # --------------------------
    create_payload = item["create_payload"]()
    response = test_client.post(item["route"] + "/", json=create_payload, headers=headers_admin)
    assert response.status_code == 201
    created_item = response.json()

    # Admin-only check for regular user
    if item.get("admin_only", False):
        response_user = test_client.post(item["route"] + "/", json=create_payload, headers=headers_user)
        assert response_user.status_code in [403, 401]

    # --------------------------
    # READ (LIST)
    # --------------------------
    response = test_client.get(item["route"] + "/", headers=headers_admin)
    assert response.status_code == 200
    assert any(d["name"] == create_payload["name"] for d in response.json())

    # --------------------------
    # UPDATE
    # --------------------------
    update_payload = {"name": "Updated AutoTest"}
    response = test_client.put(
        f"{item['route']}/{created_item['id']}",
        json=update_payload,
        headers=headers_admin
    )
    assert response.status_code == 200
    assert response.json()["name"] == "Updated AutoTest"

    # --------------------------
    # DELETE
    # --------------------------
    response = test_client.delete(
        f"{item['route']}/{created_item['id']}",
        headers=headers_admin
    )
    assert response.status_code == 200

    # Verify deletion
    response = test_client.get(item["route"] + "/", headers=headers_admin)
    assert all(d["id"] != created_item["id"] for d in response.json())
