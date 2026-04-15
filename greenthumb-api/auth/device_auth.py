"""Device bearer-token authentication for sync endpoints.

Each Pi authenticates with the cloud by sending:
    Authorization: Bearer <device_token>

The token is stored in ``device.device_token`` (set when the device is
registered through the admin UI). This dependency:
  1. Extracts the token from the Authorization header.
  2. Queries the DB for a device whose ``device_token`` matches AND whose
     ``id_device`` matches the ``{id}`` path parameter.
  3. Returns the Device row for downstream route use.
  4. Raises HTTP 401 if the token is missing, invalid, or doesn't match the
     device ID in the path (prevents a valid token from accessing another
     device's data).
"""
from __future__ import annotations

from fastapi import Depends, HTTPException, Path, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlmodel import Session, select

from greenthumb_models.models import Device

from db import get_session

_bearer = HTTPBearer(auto_error=False)


async def get_authenticated_device(
    device_id: int = Path(..., alias="id"),
    credentials: HTTPAuthorizationCredentials | None = Depends(_bearer),
    session: Session = Depends(get_session),
) -> Device:
    """FastAPI dependency: validate device bearer token.

    Args:
        device_id:   ``id_device`` from the URL path (alias ``id``).
        credentials: Parsed Authorization header (Bearer scheme).
        session:     DB session injected by FastAPI.

    Returns:
        The authenticated Device row.

    Raises:
        HTTPException 401: Token missing or invalid.
        HTTPException 404: Device not found (avoids token enumeration via
                           returning 403 instead of 404 when token is wrong).
    """
    if credentials is None or not credentials.credentials:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Device bearer token required",
            headers={"WWW-Authenticate": "Bearer"},
        )

    token = credentials.credentials

    device = session.exec(
        select(Device).where(
            Device.id_device == device_id,
            Device.device_token == token,
        )
    ).first()

    if device is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid or expired device token",
            headers={"WWW-Authenticate": "Bearer"},
        )

    return device
