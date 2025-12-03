# app/core/exception_handlers.py

"""
Global Exception Handlers
-------------------------

This module centralizes exception handling for the FastAPI application.

It provides reusable handlers for:
- HTTPException (used in routes)
- Request validation errors
- Uncaught internal server errors

These handlers ensure consistent JSON responses and reduce repetitive try/except blocks
throughout the application.
"""

from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handles HTTPException raised in any route.

    :param request: The FastAPI request instance.
    :type request: Request

    :param exc: The exception object.
    :type exc: StarletteHTTPException

    :return: JSON response with the exception details and status code.
    :rtype: JSONResponse
    """

    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handles request validation errors (422 Unprocessable Entity).

    :param request: The FastAPI request instance.
    :type request: Request

    :param exc: The validation error object.
    :type exc: RequestValidationError

    :return: JSON response with validation errors.
    :rtype: JSONResponse
    """

    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={"detail": exc.errors()}
    )


async def internal_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Handles uncaught internal server errors (500).

    :param request: The FastAPI request instance.
    :type request: Request

    :param exc: The exception object.
    :type exc: Exception

    :return: JSON response with error message.
    :rtype: JSONResponse
    """

    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )
