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

from fastapi.encoders import jsonable_encoder
from fastapi import Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from starlette.exceptions import HTTPException as StarletteHTTPException

from typing import Any


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
    _request = request
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": exc.detail}
    )


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Custom handler for request validation errors.

    - Normalizes/serializes Pydantic error payload (including Decimal in ctx)
    - Returns a safe JSONResponse with HTTP 422
    """
    # Raw errors from Pydantic
    errors = exc.errors()

    # Optional: normalize ctx values (Decimal etc.) for readability.
    # This converts nested non-serializable values into JSON-safe ones (using jsonable_encoder).
    normalized_errors = []
    for err in errors:
        err_copy = dict(err)  # shallow copy
        ctx = err_copy.get("ctx")
        if ctx is not None:
            # jsonable_encoder will convert Decimal -> float, datetime -> isoformat, etc.
            err_copy["ctx"] = jsonable_encoder(ctx)
        normalized_errors.append(err_copy)

    payload = {
        "detail": normalized_errors,
        "body": jsonable_encoder(exc.raw_body) if hasattr(exc, "raw_body") else jsonable_encoder(exc.body),
        "message": "Request validation error",
        "path": str(request.url.path),
    }

    # jsonable_encoder again to ensure entire payload is JSON serializable
    safe_payload: Any = jsonable_encoder(payload)

    return JSONResponse(status_code=422, content=safe_payload)

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
    _request = request
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={"detail": str(exc)}
    )
