"""User JWT authentication for admin endpoints.

Admin routes are protected by a JWT issued by the auth-service. This module
provides a FastAPI dependency that:
  1. Extracts the Bearer JWT from the Authorization header.
  2. Calls the auth-service's ``GET /auth/validate`` endpoint (internal
     service-to-service call) to verify the token.
  3. Returns the validated user ID (UUID) for downstream use.

The auth-service URL is read from the ``AUTH_SERVICE_URL`` environment variable
(default: ``http://auth-service:8081``).

In local development (``DEV_AUTH_BYPASS=true``), token validation is skipped
and a stub user ID is returned so the API can be exercised without running the
Java auth-service.
"""
from __future__ import annotations

import os
import uuid

import httpx
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer

AUTH_SERVICE_URL = os.getenv("AUTH_SERVICE_URL", "http://auth-service:8081")
DEV_AUTH_BYPASS  = os.getenv("DEV_AUTH_BYPASS", "false").lower() == "true"

_bearer = HTTPBearer(auto_error=False)

# Stub UUID used when DEV_AUTH_BYPASS is active
_DEV_USER_ID = uuid.UUID("00000000-0000-0000-0000-000000000001")


async def get_current_user_id(
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
) -> uuid.UUID:
    """FastAPI dependency: validate user JWT and return the user's UUID.

    Args:
        credentials: Parsed Authorization header (Bearer scheme).

    Returns:
        ``id_user`` UUID of the authenticated user.

    Raises:
        HTTPException 401: Token missing or rejected by auth-service.
    """
    if DEV_AUTH_BYPASS:
        return _DEV_USER_ID

    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User JWT required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    try:
        async with httpx.AsyncClient(base_url=AUTH_SERVICE_URL, timeout=5.0) as client:
            response = await client.get(
                "/auth/validate",
                headers={"Authorization": f"Bearer {token}"},
            )
    except (httpx.TimeoutException, httpx.ConnectError) as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=f"Auth service unavailable: {exc}",
        )

    if response.status_code != 200:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired user token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    data = response.json()
    try:
        return uuid.UUID(data["id_user"])
    except (KeyError, ValueError) as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Auth service returned unexpected payload: {exc}",
        )
