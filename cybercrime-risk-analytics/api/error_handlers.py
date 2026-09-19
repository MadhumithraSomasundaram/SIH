"""
Phase 12 — Custom Error Handlers
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Converts unhandled exceptions and Pydantic/FastAPI errors into safe, structured
HTTP responses. Stack traces, file paths, and internal model details are NEVER
exposed to API clients.
"""

import logging
from typing import Any, Dict

from fastapi import Request, status
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException as StarletteHTTPException

log = logging.getLogger(__name__)


def _safe_response(status_code: int, error_type: str, message: str, details: Any = None) -> JSONResponse:
    """Build a uniform error envelope safe to return to clients."""
    body: Dict[str, Any] = {
        "error": error_type,
        "message": message,
        "detail": message,
        "status_code": status_code,
    }
    if details is not None:
        body["details"] = details
    return JSONResponse(status_code=status_code, content=body)


async def validation_exception_handler(request: Request, exc: RequestValidationError) -> JSONResponse:
    """
    Handle Pydantic / FastAPI schema validation failures (HTTP 422).
    Returns field-level error messages without internal stack traces.
    """
    errors = []
    for err in exc.errors():
        field = " -> ".join(str(loc) for loc in err.get("loc", []))
        errors.append({"field": field, "issue": err.get("msg", "Validation error")})

    log.warning("Validation error on %s: %s", request.url.path, errors)
    return _safe_response(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        error_type="ValidationError",
        message="One or more input fields failed validation. Review the details.",
        details=errors,
    )


async def http_exception_handler(request: Request, exc: StarletteHTTPException) -> JSONResponse:
    """
    Handle explicit HTTP errors raised by route handlers.
    """
    log.warning("HTTP %d on %s: %s", exc.status_code, request.url.path, exc.detail)
    return _safe_response(
        status_code=exc.status_code,
        error_type="HTTPError",
        message=str(exc.detail),
    )


async def generic_exception_handler(request: Request, exc: Exception) -> JSONResponse:
    """
    Catch-all for unhandled internal exceptions.
    Logs the full exception server-side but returns only a safe message to clients.
    """
    log.exception("Unhandled exception on %s", request.url.path)
    return _safe_response(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        error_type="InternalServerError",
        message=(
            "An internal error occurred while processing the request. "
            "Please contact the system administrator."
        ),
    )


async def value_error_handler(request: Request, exc: ValueError) -> JSONResponse:
    """
    Handle ValueError raised by inference pipeline (e.g., missing features, leakage detected).
    Returns HTTP 400 with a safe, informative message.
    """
    log.warning("Prediction ValueError on %s: %s", request.url.path, str(exc))
    return _safe_response(
        status_code=status.HTTP_400_BAD_REQUEST,
        error_type="InvalidPredictionInput",
        message=str(exc),
    )
