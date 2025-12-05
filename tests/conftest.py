# app/test/conftest.py

"""
Test Fixtures and Factories
---------------------------

This module contains fixtures and factories used in unit and integration tests
for the FastAPI app. It provides:

- An in-memory test database for isolated testing
- FastAPI TestClient
- Factories to create users, admins, and products
- Rate limiter disabled for testing
"""

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from typing import Callable

from app.main import app, limiter
from app.database import Base, get_db
from app.models import User, Product
from app.core.security import hash_password


# --------------------------
# In-memory test database engine
# --------------------------
engine_test = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool
)

TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


# --------------------------
# Fixture to reset DB before each test
# --------------------------
@pytest.fixture(autouse=True)
def reset_db() -> None:
    """
    Resets the in-memory database before each test.

    Ensures that each test runs in a clean environment and is not affected
    by previous tests.

    :return: None
    """
    Base.metadata.drop_all(bind=engine_test)
    Base.metadata.create_all(bind=engine_test)
    yield

# --------------------------
# Fixture db_session
# --------------------------
@pytest.fixture()
def db_session() -> Session:
    """
    Provides a SQLAlchemy session for tests.

    :return: SQLAlchemy session connected to the test database
    :rtype: Session
    """

    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()

# --------------------------
# Override get_db dependency for tests
# --------------------------
@pytest.fixture(autouse=True)
def override_get_db() -> None:
    """
    Overrides the FastAPI get_db dependency to use the test database.

    Ensures that all routes use the in-memory database during tests.

    :return: None
    """

    app.dependency_overrides[get_db] = lambda: TestingSessionLocal()
    yield
    app.dependency_overrides.clear()

# --------------------------
# Fixture TestClient
# --------------------------
@pytest.fixture()
def test_client() -> TestClient:
    """
    Provides a FastAPI TestClient for making HTTP requests in tests.

    :return: TestClient instance for the FastAPI app
    :rtype: TestClient
    """

    return TestClient(app)


# --------------------------
# Disable rate limiter for tests
# --------------------------
@pytest.fixture(autouse=True, scope="session")
def disable_rate_limit() -> None:
    """
    Disables slowapi rate limiting during tests.

    Prevents request limit errors when running multiple tests.
    """

    limiter.enabled = False


# --------------------------
# Factory create_user
# --------------------------
@pytest.fixture()
def create_user(db_session: Session) -> Callable:
    """
    Factories to create users, admins, and products.

    :param db_session: Session database
    :type db_session: Session

    :return: Created user
    :rtype: Callable
    """

    def _create(email: str = None, password: str = "123456", verified: bool = True) -> User:
        """"
        Factory to create a regular user in the test database.

        :param email: Email address of the user. If None, generates a unique email automatically.
        :type email: str | None

        :param password: User password.
        :type password: str

        :param verified: Indicates if the user is already verified.
        :type verified: bool

        :return: The created User instance.
        :rtype: User
        """

        if email is None:
            import uuid
            email = f"user_{uuid.uuid4().hex}@test.com"

        hashed_password = hash_password(password)

        user = User(
            email=email,
            hashed_password=hashed_password,
            role="user",
            is_verified=verified,
            is_active=True
        )

        db_session.add(user)
        db_session.commit()
        db_session.refresh(user)

        return user

    return _create


# --------------------------
# Factory create_admin_user
# --------------------------
@pytest.fixture()
def create_admin_user(db_session: Session) -> Callable:
    """
    Factories to create admin users, admins, and products.

    :param db_session: Session database
    :type db_session: Session

    :return: Created admin user
    :rtype: Callable
    """

    def _create(email: str = None, password: str = "123456") -> User:
        """
        Factory to create an admin user in the test database.

        :param email: Email address of the admin. If None, generates a unique email automatically.
        :type email: str | None

        :param password: Admin password.
        :type password: str

        :return: The created admin User instance.
        :rtype: User
        """

        if email is None:
            import uuid
            email = f"admin_{uuid.uuid4().hex}@test.com"

        hashed_password = hash_password(password)

        admin = User(
            email=email,
            hashed_password=hashed_password,
            role="admin",
            is_verified=True,
            is_active=True
        )

        db_session.add(admin)
        db_session.commit()
        db_session.refresh(admin)

        return admin

    return _create


# --------------------------
# Factory create_product_in_db
# --------------------------
@pytest.fixture()
def create_product_in_db(db_session: Session) -> Callable:
    """
    Factories to create products in the test database.

    :param db_session: Session database
    :type db_session: Session

    :return: Created product
    :rtype: Callable
    """

    def _create(
        name: str = "Test Product",
        price: float = 10.0,
        description: str = "Default description",
        stock: int = 0
    ) -> Product:
        """
        Factory to create a product in the test database.

        :param name: Product name.
        :type name: str

        :param price: Product price.
        :type price: float

        :param description: Product description.
        :type description: str

        :param stock: Quantity in stock.
        :type stock: int

        :return: The created Product instance.
        :rtype: Product
        """

        product = Product(
            name=name,
            price=price,
            description=description,
            stock=stock
        )

        db_session.add(product)
        db_session.commit()
        db_session.refresh(product)

        return product

    return _create


# --------------------------
# Fixture for login
# --------------------------
@pytest.fixture()
def login_user(test_client: TestClient) -> Callable:
    """
    Factories to create users, admins, and products.

    :param test_client: TestClient object
    :type test_client: TestClient

    :return: Login response
    :rtype: Callable
    """

    def _login(email: str, password: str):
        """
        Logs in a user via TestClient and returns authentication tokens.

        Prints debug information to help during test development.

        :param email: User email for login.
        :type email: str

        :param password: User password.
        :type password: str

        :return: JSON containing access_token and refresh_token.
        :rtype: dict
        """

        resp = test_client.post("/auth/login", json={"email": email, "password": password})
        resp.raise_for_status()

        return resp.json()

    return _login
