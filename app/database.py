# app/database.py

"""
Database configuration module.

This module initializes the SQLAlchemy engine, session factory, and declarative
base used across the application. It also provides a database dependency for
FastAPI routes, ensuring proper session management using dependency injection.
"""

from typing import Generator
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base, Session

from app.core.config import settings


# ----------------------------------------------------------------------
# SQLAlchemy Engine
# ----------------------------------------------------------------------
# The engine manages the database connection. For SQLite, the argument
# "check_same_thread=False" is required when using multiple threads such as
# with FastAPI's async model.
engine = create_engine(
    settings.DATABASE_URL,
    connect_args={"check_same_thread": False}
)


# ----------------------------------------------------------------------
# Session Factory
# ----------------------------------------------------------------------
# Creates database sessions. FastAPI will use `get_db()` to instantiate a
# session per request.
SessionLocal = sessionmaker(
    autocommit=False,
    autoflush=False,
    bind=engine)


# ----------------------------------------------------------------------
# Base Class for ORM Models
# ----------------------------------------------------------------------
# All SQLAlchemy models must inherit from this base.
Base = declarative_base()


# ----------------------------------------------------------------------
# Database Dependency
# ----------------------------------------------------------------------
def get_db() -> Generator[Session, None, None]:
    """
    Provides a database session for FastAPI routes.

    This function is used as a dependency in FastAPI endpoints.
    It creates a new SQLAlchemy session for each request, yields it to the
    endpoint, and ensures that the session is properly closed afterward.

    :yield: Session: An active SQLAlchemy database session.
    """

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
