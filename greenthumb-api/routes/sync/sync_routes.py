"""Sync endpoints — Pi ↔ Cloud communication.

All routes are protected by device bearer-token auth
(``get_authenticated_device`` dependency).

Endpoints:
    GET  /sync/devices/{id}/config
        Return the full DeviceConfig DTO for the requesting Pi.

    POST /sync/devices/{id}/measurements
        Bulk-upsert sensor readings sent by the Pi.

    POST /sync/devices/{id}/photos
        Receive a JPEG photo from the Pi (multipart/form-data), upload it to
        Supabase Storage, and store the metadata row. The Pi never holds
        Supabase credentials.

    PATCH /sync/devices/{id}/local-changes
        Apply Pi-side mutations (device_mode changes, threshold edits) to the
        cloud DB using last-write-wins semantics (``updated_at`` comparison).

Environment variables consumed here (in addition to DATABASE_URL):
    SUPABASE_URL — Supabase project URL  (e.g. https://xyz.supabase.co)
    SUPABASE_KEY — Supabase service-role key
"""
from __future__ import annotations

import os
import secrets
from datetime import datetime
from typing import Any, Optional

import httpx
from fastapi import APIRouter, Depends, Form, HTTPException, UploadFile, File
from sqlmodel import Session, select

# ---------------------------------------------------------------------------
# Supabase Storage configuration (cloud-side only — Pi never sees these)
# ---------------------------------------------------------------------------

_SUPABASE_URL    = os.getenv("SUPABASE_URL", "").rstrip("/")
_SUPABASE_KEY    = os.getenv("SUPABASE_KEY", "")
_PHOTOS_BUCKET   = "plant-photos"

from greenthumb_models.models import (
    Device, Measurement, Photo, Threshold, CultivationPhase,
)
from greenthumb_models.sync_schemas import DeviceConfig

from auth.device_auth import get_authenticated_device
from db import get_session
from config_builder import build_config_from_db

router = APIRouter(prefix="/sync", tags=["Sync"])


# ---------------------------------------------------------------------------
# GET /sync/devices/{id}/config
# ---------------------------------------------------------------------------

@router.get("/devices/{id}/config", response_model=DeviceConfig)
async def get_device_config(
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    """Return the full DeviceConfig for the Pi to bootstrap from.

    Called during Pi lifespan startup. Returns the same DTO shape that
    ``build_config_from_db()`` produces on the Pi side, so the Pi's
    ``DeviceManager.init_from_config()`` can consume it directly.
    """
    return build_config_from_db(session, device.id_device)


# ---------------------------------------------------------------------------
# POST /sync/devices/{id}/measurements
# ---------------------------------------------------------------------------

@router.post("/devices/{id}/measurements", status_code=201)
async def receive_measurements(
    payload: list[dict[str, Any]],
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    """Bulk-insert measurements sent by the Pi.

    The Pi sends the full batch of unsynced measurements. Each dict must
    contain: ``id_device_sensor``, ``id_variable``, ``value``, ``collected_at``.
    The cloud-side ``id_measurement`` is re-assigned (Pi IDs are local).

    Returns:
        Count of inserted records.
    """
    inserted = 0
    for m in payload:
        try:
            row = Measurement(
                id_device_sensor=int(m["id_device_sensor"]),
                id_variable=int(m["id_variable"]),
                value=float(m["value"]),
                collected_at=datetime.fromisoformat(str(m["collected_at"])),
                is_synced=True,
            )
            session.add(row)
            inserted += 1
        except (KeyError, ValueError, TypeError) as exc:
            # Skip malformed rows; log and continue
            print(f"[sync] Skipping malformed measurement: {exc} — {m}")
    session.commit()
    return {"inserted": inserted}


# ---------------------------------------------------------------------------
# POST /sync/devices/{id}/photos
# ---------------------------------------------------------------------------

async def _upload_to_supabase(filename: str, photo_bytes: bytes) -> Optional[str]:
    """Upload photo bytes to Supabase Storage and return the public URL.

    Returns ``None`` if Supabase is not configured or the upload fails.
    The caller stores the metadata regardless; ``cloud_url`` will be ``None``
    if this returns ``None``.
    """
    if not _SUPABASE_URL or not _SUPABASE_KEY:
        return None

    storage_url = (
        f"{_SUPABASE_URL}/storage/v1/object/{_PHOTOS_BUCKET}/{filename}"
    )
    headers = {
        "Authorization": f"Bearer {_SUPABASE_KEY}",
        "apikey":        _SUPABASE_KEY,
        "Content-Type":  "image/jpeg",
    }
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            resp = await client.put(storage_url, content=photo_bytes, headers=headers)
        if resp.status_code in (200, 201):
            return (
                f"{_SUPABASE_URL}/storage/v1/object/public"
                f"/{_PHOTOS_BUCKET}/{filename}"
            )
        print(
            f"[sync] Supabase upload failed: HTTP {resp.status_code} — "
            f"{resp.text[:120]}"
        )
    except Exception as exc:
        print(f"[sync] Supabase upload error: {exc}")
    return None


@router.post("/devices/{id}/photos", status_code=201)
async def receive_photo(
    file: UploadFile = File(...),
    id_device_actuator: int = Form(...),
    captured_at: str = Form(...),
    id_cultivation: Optional[int] = Form(None),
    file_size_bytes: Optional[int] = Form(None),
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    """Receive a JPEG from the Pi, upload it to Supabase Storage, store metadata.

    The Pi sends the raw photo bytes as multipart/form-data. This endpoint:
      1. Reads the bytes.
      2. Uploads to Supabase Storage under ``{device_id}/{captured_at}_{filename}``.
      3. Creates a ``Photo`` row in the cloud DB (``cloud_url`` is set if
         Supabase upload succeeded; ``is_synced=True`` regardless so the Pi
         does not retry).

    Form fields:
        file (UploadFile)       — JPEG file bytes.
        id_device_actuator (int)— Camera actuator ID.
        captured_at (str)       — ISO-format capture timestamp.
        id_cultivation (int?)   — Active cultivation ID, if known.
        file_size_bytes (int?)  — File size hint (measured from bytes if omitted).
    """
    photo_bytes = await file.read()
    actual_size = file_size_bytes or len(photo_bytes)

    # Build a stable storage path: device_id/YYYY-MM-DDTHH-MM-SS_filename
    safe_ts  = captured_at.replace(":", "-").replace(".", "-")
    filename = f"{device.id_device}/{safe_ts}_{file.filename or 'photo.jpg'}"

    cloud_url = await _upload_to_supabase(filename, photo_bytes)

    try:
        row = Photo(
            id_device=device.id_device,
            id_device_actuator=id_device_actuator,
            id_cultivation=id_cultivation,
            captured_at=datetime.fromisoformat(captured_at),
            cloud_url=cloud_url,
            file_size_bytes=actual_size,
            is_synced=True,
        )
        session.add(row)
        session.commit()
        session.refresh(row)
        return {"id_photo": row.id_photo, "cloud_url": cloud_url, "status": "stored"}
    except (ValueError, TypeError) as exc:
        raise HTTPException(status_code=422, detail=f"Invalid photo metadata: {exc}")


# ---------------------------------------------------------------------------
# PATCH /sync/devices/{id}/local-changes
# ---------------------------------------------------------------------------

@router.patch("/devices/{id}/local-changes")
async def apply_local_changes(
    payload: dict[str, Any],
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    """Apply Pi-side mutations to the cloud DB (last-write-wins).

    Supported change types:
      ``device_mode``: Update ``device.device_mode`` and clear ``is_dirty``.
      ``thresholds``:  Update threshold ``min_value`` / ``max_value`` /
                       ``target_value`` / ``is_active`` for each changed row.

    All updates respect ``updated_at`` for conflict resolution — if the cloud
    record was modified more recently than the Pi's change, the update is
    skipped (the Pi will re-pull on next reboot).

    Payload shape:
        {
          "device_mode": "HIGH",                       # optional
          "thresholds": [                              # optional
            {"id_threshold": 1, "min_value": 20.0, "updated_at": "..."},
            ...
          ]
        }
    """
    applied: list[str] = []

    # ---- Device mode ----
    if "device_mode" in payload:
        new_mode = payload["device_mode"]
        device_row = session.get(Device, device.id_device)
        if device_row:
            device_row.device_mode = new_mode
            device_row.is_dirty    = False
            device_row.updated_at  = datetime.now()
            session.add(device_row)
            applied.append("device_mode")

    # ---- Threshold patches ----
    for t_patch in payload.get("thresholds", []):
        t_id = t_patch.get("id_threshold")
        if not t_id:
            continue
        row = session.get(Threshold, t_id)
        if row is None:
            continue

        # Last-write-wins: skip if cloud is newer
        pi_updated_at = t_patch.get("updated_at")
        if pi_updated_at and row.updated_at:
            try:
                pi_ts = datetime.fromisoformat(str(pi_updated_at))
                if row.updated_at > pi_ts:
                    continue
            except ValueError:
                pass

        for field in ("min_value", "max_value", "target_value", "is_active"):
            if field in t_patch and t_patch[field] is not None:
                setattr(row, field, t_patch[field])
        row.updated_at = datetime.now()
        row.is_dirty   = False
        session.add(row)
        applied.append(f"threshold:{t_id}")

    session.commit()
    return {"applied": applied}


# ---------------------------------------------------------------------------
# POST /sync/devices/{id}/token  (admin utility — generate / rotate token)
# ---------------------------------------------------------------------------

@router.post("/devices/{id}/token", tags=["Admin"])
async def rotate_device_token(
    device: Device = Depends(get_authenticated_device),
    session: Session = Depends(get_session),
):
    """Generate a new bearer token for this device and return it.

    The old token is immediately invalidated. The response is the only time
    the new token is revealed — store it securely in the Pi's environment.
    """
    new_token = secrets.token_urlsafe(32)
    device_row = session.get(Device, device.id_device)
    if device_row is None:
        raise HTTPException(status_code=404, detail="Device not found")
    device_row.device_token = new_token
    device_row.updated_at   = datetime.now()
    session.add(device_row)
    session.commit()
    return {
        "id_device":    device.id_device,
        "device_token": new_token,
        "warning":      "Store this token securely — it will not be shown again.",
    }
