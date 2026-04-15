"""Build a DeviceConfig DTO from the cloud PostgreSQL database.

This module is the single place that touches SQLModel to assemble the
DeviceConfig returned by ``GET /sync/devices/{id}/config``. The Pi deserialises
the JSON response directly into a DeviceConfig DTO.

Typical usage (inside sync_routes.py):
    from config_builder import build_config_from_db
    config = build_config_from_db(session, device.id_device)
    return config
"""
from __future__ import annotations

from sqlmodel import Session, select

from utils import get_by_id
from greenthumb_models.models import Device, CultivationPhase
from greenthumb_models.sync_schemas import (
    ActivePhaseInfo,
    ActuatorConfig,
    CapabilityConfig,
    DeviceConfig,
    SensorConfig,
    ThresholdConfig,
)


def build_config_from_db(session: Session, device_id: int) -> DeviceConfig:
    """Query the local DB and assemble a DeviceConfig for ``device_id``.

    Loads:
    - All *active* device sensors and their sensor capabilities.
    - All *active* device actuators and their model config.
    - All *active* thresholds for the active cultivation (if any).
    - The current active cultivation phase (ended_at IS NULL).

    Args:
        session:   Open SQLModel session against the local PostgreSQL DB.
        device_id: Primary key of the device row (matches DEVICE_ID env var).

    Returns:
        A fully-populated DeviceConfig DTO ready for DeviceManager.init_from_config().

    Raises:
        ValueError: If no device with ``device_id`` is found.
    """
    device = get_by_id(session, Device, device_id)
    if device is None:
        raise ValueError(f"Device {device_id} not found in local database")

    # ------------------------------------------------------------------
    # Sensors
    # ------------------------------------------------------------------
    sensors: list[SensorConfig] = [
        SensorConfig(
            id_device_sensor=ds.id_device_sensor,
            id_sensor_model=ds.id_sensor_model,
            model_name=ds.sensor_model.model_name,
            port_address=ds.port_address,
            capabilities=[
                CapabilityConfig(
                    id_variable=cap.id_variable,
                    # Match the key format used in Sensor.read_data() dicts
                    variable_name=cap.variable.name.replace(" ", "_").lower(),
                    min_range=float(cap.min_range) if cap.min_range is not None else None,
                    max_range=float(cap.max_range) if cap.max_range is not None else None,
                )
                for cap in ds.sensor_model.capabilities
            ],
        )
        for ds in (device.device_sensors or [])
        if ds.is_active
    ]

    # ------------------------------------------------------------------
    # Actuators
    # ------------------------------------------------------------------
    actuators: list[ActuatorConfig] = [
        ActuatorConfig(
            id_device_actuator=da.id_device_actuator,
            id_actuator_model=da.id_actuator_model,
            actuator_type=da.actuator_model.actuator_type,
            model_name=da.actuator_model.model_name,
            instance_config=da.instance_config or {},
            model_config_json=da.actuator_model.model_config_json or {},
        )
        for da in (device.device_actuators or [])
        if da.is_active
    ]

    # ------------------------------------------------------------------
    # Active cultivation → thresholds
    # ------------------------------------------------------------------
    thresholds: list[ThresholdConfig] = []
    active_cultivation = next(
        (c for c in (device.cultivations or []) if c.end_date is None),
        None,
    )

    if active_cultivation:
        thresholds = [
            ThresholdConfig(
                id_threshold=t.id_threshold,
                id_cultivation=t.id_cultivation,
                id_variable=t.id_variable,
                id_growth_phase=t.id_growth_phase,
                is_default_phase=t.growth_phase.is_default,
                min_value=float(t.min_value) if t.min_value is not None else None,
                max_value=float(t.max_value) if t.max_value is not None else None,
                target_value=float(t.target_value) if t.target_value is not None else None,
                id_actuator_action=t.id_actuator_action,
                is_active=t.is_active,
            )
            for t in (active_cultivation.thresholds or [])
        ]

    # ------------------------------------------------------------------
    # Active cultivation phase (ended_at IS NULL)
    # ------------------------------------------------------------------
    active_phase: ActivePhaseInfo | None = None
    if active_cultivation:
        stmt = select(CultivationPhase).where(
            CultivationPhase.id_cultivation == active_cultivation.id_cultivation,
            CultivationPhase.ended_at.is_(None),  # type: ignore[union-attr]
        )
        active_cp = session.exec(stmt).first()
        if active_cp:
            active_phase = ActivePhaseInfo(
                id_cultivation_phase=active_cp.id_cultivation_phase,
                id_cultivation=active_cp.id_cultivation,
                id_growth_phase=active_cp.id_growth_phase,
                started_at=active_cp.started_at,
            )

    # ------------------------------------------------------------------
    # Assemble
    # ------------------------------------------------------------------
    device_mode = (
        device.device_mode.value
        if hasattr(device.device_mode, "value")
        else str(device.device_mode)
    )

    return DeviceConfig(
        id_device=device.id_device,
        name=device.name,
        device_mode=device_mode,
        sensors=sensors,
        actuators=actuators,
        thresholds=thresholds,
        active_phase=active_phase,
    )
