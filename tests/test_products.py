# app/tests/test_products.py

"""
Products API Tests
------------------

This module tests all CRUD operations for the products API, including:

1. Listing products
2. Creating products (authorized and unauthorized)
3. Updating products
4. Deleting products
5. Handling non-existent products

All tests use the FastAPI TestClient and database fixtures.
"""

from fastapi.testclient import TestClient
from typing import Callable


def test_list_products(test_client: TestClient, create_product_in_db: Callable) -> None:
    """
    Test retrieving a list of products.

    Steps:
    1. Create two products in the test database.
    2. Call the /products/ endpoint.
    3. Assert the response status code is 200.
    4. Assert that at least 2 products are returned.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_product_in_db: Factory function to create a product in the database.
    :type create_product_in_db: Callable

    :return: None
    """
    create_product_in_db(name="Prod 1", description="Desc 1", price=20.0, stock=5)
    create_product_in_db(name="Prod 2", description="Desc 2", price=30.0, stock=5)

    response = test_client.get("/products/")
    assert response.status_code == 200
    data = response.json()
    assert len(data) >= 2


def test_create_product_authorized(test_client: TestClient, create_admin_user: Callable) -> None:
    """
    Test that an admin user can create a product.

    Steps:
    1. Create an admin user.
    2. Log in to obtain an access token.
    3. Send a POST request to /products/ with product data.
    4. Assert the response status code is 201.
    5. Assert the product data that matches the send as payload.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :return: None
    """

    user = create_admin_user()

    # Login to get access token
    login = test_client.post("/auth/login", json={"email": user.email, "password": "123456"})
    token = login.json()["access_token"]

    payload = {
        "name": "New Product",
        "description": "New Product Description",
        "price": 20.0,
        "stock": 10
    }

    response = test_client.post("/products/", json=payload, headers={"Authorization": f"Bearer {token}"})

    assert response.status_code == 201

    data = response.json()

    assert data["name"] == payload["name"]


def test_create_product_unauthorized(test_client: TestClient, create_user: Callable, login_user: Callable) -> None:
    """
    Test that a non-admin user cannot create a product.

    Steps:
    1. Create a regular user.
    2. Log in to obtain an access token.
    3. Attempt to POST a new product with this user's token.
    4. Assert the response status code is 403 (Forbidden).

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_user: Factory function to create a regular user.
    :type create_user: Callable

    :param login_user: Factory function to log in a user and get tokens.
    :type login_user: Callable

    :return: None
    """

    user = create_user(email="regular_user@test.com", verified=True)
    tokens = login_user(user.email, "123456")
    access_token = tokens.get("access_token")

    assert access_token is not None

    response = test_client.post(
        "/products/",
        json={"name": "Prod 1", "description": "Desc", "price": 10.0, "stock": 5},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 403


def test_update_product(test_client: TestClient, create_admin_user: Callable, create_product_in_db: Callable, login_user: Callable) -> None:
    """
    Test updating an existing product.

    Steps:
    1. Create an admin user and log in to obtain a token.
    2. Create a product in the database.
    3. Send a PUT request to update the product's name.
    4. Assert the response status code is 200.
    5. Assert the product name is updated in the response.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :param create_product_in_db: Factory function to create a product in the database.
    :type create_product_in_db: Callable

    :param login_user: Factory function to log in a user and get tokens.
    :type login_user: Callable

    :return: None
    """

    admin = create_admin_user(email="admin_update@test.com")
    tokens = login_user(admin.email, "123456")
    access_token = tokens.get("access_token")

    assert access_token is not None

    product = create_product_in_db()

    response = test_client.put(
        f"/products/{product.id}",
        json={"name": "Updated Name"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200
    assert response.json()["name"] == "Updated Name"


def test_delete_product(test_client: TestClient, create_admin_user: Callable, create_product_in_db: Callable, login_user: Callable) -> None:
    """
    Test deleting a product.

    Steps:
    1. Create an admin user and log in to obtain a token.
    2. Create a product in the database.
    3. Send a DELETE request to remove the product.
    4. Assert the response status code is 200.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :param create_product_in_db: Factory function to create a product in the database.
    :type create_product_in_db: Callable

    :param login_user: Factory function to log in a user and get tokens.
    :type login_user: Callable

    :return: None
    """

    admin = create_admin_user(email="admin_delete@test.com")
    tokens = login_user(admin.email, "123456")
    access_token = tokens.get("access_token")

    assert access_token is not None

    product = create_product_in_db()

    response = test_client.delete(
        f"/products/{product.id}",
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 200


def test_update_nonexistent_product(test_client: TestClient, create_admin_user: Callable, login_user: Callable) -> None:
    """
    Test updating a non-existent product.

    Steps:
    1. Create an admin user and log in to obtain a token.
    2. Send a PUT request to update a product ID that doesn't exist.
    3. Assert the response status code is 404.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :param login_user: Factory function to log in a user and get tokens.
    :type login_user: Callable

    :return: None
    """

    admin = create_admin_user(email="admin_nonexist@test.com")
    tokens = login_user(admin.email, "123456")
    access_token = tokens.get("access_token")

    assert access_token is not None

    response = test_client.put(
        "/products/9999",
        json={"name": "Doesn't matter"},
        headers={"Authorization": f"Bearer {access_token}"}
    )

    assert response.status_code == 404


def test_delete_nonexistent_product(test_client: TestClient, create_admin_user: Callable, login_user: Callable) -> None:
    """
    Test deleting a non-existent product.

    Steps:
    1. Create an admin user and log in to obtain a token.
    2. Send a DELETE request for a product ID that doesn't exist.
    3. Assert the response status code is 404.

    :param test_client: FastAPI TestClient instance.
    :type test_client: TestClient

    :param create_admin_user: Factory function to create an admin user.
    :type create_admin_user: Callable

    :param login_user: Factory function to log in a user and get tokens.
    :type login_user: Callable

    :return: None
    """

    admin = create_admin_user(email="admin_nonexist_delete@test.com")
    tokens = login_user(admin.email, "123456")
    access_token = tokens.get("access_token")
    assert access_token is not None

    response = test_client.delete(
        "/products/9999",
        headers={"Authorization": f"Bearer {access_token}"}
    )
    assert response.status_code == 404
