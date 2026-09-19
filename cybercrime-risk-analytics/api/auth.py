"""
API Authentication Guard — Shared Dependency
Cybercrime Predictive Analytics Framework (Problem Statement ID 26184)

Provides a lightweight auth dependency for routes that were previously public:
  - POST /predict, /predict/batch, /explain
  - GET/POST /gis/*
  - GET/POST/PATCH /alerts/*

Two accepted credentials (either is sufficient):
  1. X-API-Key header  — Static dashboard/prototype API key.
     Value: DASHBOARD_API_KEY env var, defaulting to the prototype key below.
     Used by the dashboard JS (no login flow needed for public-facing charts).

  2. Authorization: Bearer <JWT> — The same analyst JWT already used for
     /analyst/* routes. Analysts who are logged in can also call these routes
     without a separate API key.

Returns HTTP 401 with a consistent error body if neither credential is present
or if both fail validation. Response style matches the 403 format already used
in analyst_routes.py.

IMPORTANT:
  - This does NOT change how /analyst/* JWT auth or role checks work.
  - This does NOT add role gating — any valid credential passes.
  - The dashboard API key is intentionally not a secret in a prototype;
    it is a guard against truly anonymous/accidental calls.
"""
from __future__ import annotations

import logging
import os
from typing import Optional

from fastapi import Header, HTTPException, status as http_status
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi import Depends

logger = logging.getLogger("api.auth")

# ---------------------------------------------------------------------------
# Dashboard / prototype static API key
# Set DASHBOARD_API_KEY env var to override in any deployment environment.
# ---------------------------------------------------------------------------
_DASHBOARD_API_KEY = os.getenv(
    "DASHBOARD_API_KEY",
    "sih26184-dashboard-prototype-key-2026"
)

# ---------------------------------------------------------------------------
# JWT settings — must match analyst_routes.py exactly
# ---------------------------------------------------------------------------
_SECRET_KEY = os.getenv(
    "ANALYST_JWT_SECRET",
    "prototype-dev-secret-NOT-for-production-CHANGE-before-deployment-26184"
)
_ALGORITHM = "HS256"

_bearer_scheme = HTTPBearer(auto_error=False)


def _verify_jwt(token: str) -> bool:
    """Return True if the token is a valid analyst JWT, False otherwise."""
    try:
        from jose import jwt, JWTError
        payload = jwt.decode(token, _SECRET_KEY, algorithms=[_ALGORITHM])
        return bool(payload.get("sub"))
    except Exception:
        return False


def require_api_key(
    x_api_key: Optional[str] = Header(default=None, alias="X-API-Key"),
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(_bearer_scheme),
) -> str:
    """
    FastAPI dependency — blocks unauthenticated requests with HTTP 401.

    Accepts (either is sufficient):
      • X-API-Key: sih26184-dashboard-prototype-key-2026
      • Authorization: Bearer <valid analyst JWT>

    Usage in a router (apply to ALL routes in the router):
        router = APIRouter(..., dependencies=[Depends(require_api_key)])

    Usage on a single endpoint:
        async def my_endpoint(..., _: str = Depends(require_api_key)):
    """
    # ── Path 0: Bypass via environment variable (e.g. testing) ─────────
    if os.getenv("DISABLE_API_KEY_AUTH", "").lower() in ("true", "1", "yes"):
        return "bypass"

    # ── Path 1: Static API key ──────────────────────────────────────────
    if x_api_key and x_api_key == _DASHBOARD_API_KEY:
        return "api_key"

    # ── Path 2: Analyst JWT Bearer token ───────────────────────────────
    if credentials and credentials.credentials:
        if _verify_jwt(credentials.credentials):
            return "jwt"

    # ── Neither credential matched ──────────────────────────────────────
    logger.warning(
        "Unauthorized access attempt — no valid X-API-Key or Bearer token."
    )
    raise HTTPException(
        status_code=http_status.HTTP_401_UNAUTHORIZED,
        detail=(
            "Authentication required. Provide either:\n"
            "  • X-API-Key header with the dashboard API key, or\n"
            "  • Authorization: Bearer <analyst JWT token>\n"
            "Contact the system administrator if you do not have credentials."
        ),
        headers={"WWW-Authenticate": "Bearer"},
    )
