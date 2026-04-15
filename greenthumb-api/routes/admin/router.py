"""Admin CRUD routes for all Tier 1 and Tier 2 entities.

All routes require a valid user JWT (verified by ``get_current_user_id``).
The ``make_crud_router`` factory from ``utils`` generates standard
GET-list / GET-one / POST / PATCH / DELETE endpoints for each entity.

Route prefixes follow the pattern ``/admin/{entity}`` so they are cleanly
namespaced away from the sync routes.
"""
from __future__ import annotations

from fastapi import APIRouter, Depends

from greenthumb_models.models import (
    # Tier 0
    AppUser, AppUserCreate, AppUserRead, AppUserUpdate,
    # Tier 1
    Unit, UnitCreate, UnitRead, UnitUpdate,
    Variable, VariableCreate, VariableRead, VariableUpdate,
    PlantSpecies, PlantSpeciesCreate, PlantSpeciesRead, PlantSpeciesUpdate,
    GrowthPhase, GrowthPhaseCreate, GrowthPhaseRead, GrowthPhaseUpdate,
    SensorModel, SensorModelCreate, SensorModelRead, SensorModelUpdate,
    ActuatorModel, ActuatorModelCreate, ActuatorModelRead, ActuatorModelUpdate,
    # Tier 2
    Device, DeviceAdminRead, DeviceCreate, DeviceUpdate,
    DeviceSensor, DeviceSensorCreate, DeviceSensorRead, DeviceSensorUpdate,
    SensorCapability, SensorCapabilityCreate, SensorCapabilityRead, SensorCapabilityUpdate,
    DeviceActuator, DeviceActuatorCreate, DeviceActuatorRead, DeviceActuatorUpdate,
    Cultivation, CultivationCreate, CultivationRead, CultivationUpdate,
    Threshold, ThresholdCreate, ThresholdRead, ThresholdUpdate,
    # Tier 3 (read-heavy — Pi writes, cloud reads)
    Measurement, MeasurementCreate, MeasurementRead, MeasurementUpdate,
    Photo, PhotoCreate, PhotoRead, PhotoUpdate,
    ActuatorLog, ActuatorLogCreate, ActuatorLogRead,
    CultivationPhase, CultivationPhaseCreate, CultivationPhaseRead, CultivationPhaseUpdate,
)

from utils.api import make_crud_router
from auth.user_auth import get_current_user_id

# All admin routes require a logged-in user
_auth = Depends(get_current_user_id)

router = APIRouter(prefix="/admin", tags=["Admin"], dependencies=[_auth])

# ---------------------------------------------------------------------------
# Tier 0: Users
# ---------------------------------------------------------------------------
router.include_router(
    make_crud_router(AppUser, AppUserCreate, AppUserRead, AppUserUpdate, "/users", tags=["Users"])
)

# ---------------------------------------------------------------------------
# Tier 1: Global catalog
# ---------------------------------------------------------------------------
router.include_router(
    make_crud_router(Unit, UnitCreate, UnitRead, UnitUpdate, "/units", tags=["Units"])
)
router.include_router(
    make_crud_router(Variable, VariableCreate, VariableRead, VariableUpdate, "/variables", tags=["Variables"])
)
router.include_router(
    make_crud_router(PlantSpecies, PlantSpeciesCreate, PlantSpeciesRead, PlantSpeciesUpdate, "/plant-species", tags=["Plant Species"])
)
router.include_router(
    make_crud_router(GrowthPhase, GrowthPhaseCreate, GrowthPhaseRead, GrowthPhaseUpdate, "/growth-phases", tags=["Growth Phases"])
)
router.include_router(
    make_crud_router(SensorModel, SensorModelCreate, SensorModelRead, SensorModelUpdate, "/sensor-models", tags=["Sensor Models"])
)
router.include_router(
    make_crud_router(ActuatorModel, ActuatorModelCreate, ActuatorModelRead, ActuatorModelUpdate, "/actuator-models", tags=["Actuator Models"])
)

# ---------------------------------------------------------------------------
# Tier 2: Device configuration
# DeviceAdminRead is used so device_token is visible in the admin response.
# ---------------------------------------------------------------------------
router.include_router(
    make_crud_router(Device, DeviceCreate, DeviceAdminRead, DeviceUpdate, "/devices", tags=["Devices"])
)
router.include_router(
    make_crud_router(DeviceSensor, DeviceSensorCreate, DeviceSensorRead, DeviceSensorUpdate, "/device-sensors", tags=["Device Sensors"])
)
router.include_router(
    make_crud_router(SensorCapability, SensorCapabilityCreate, SensorCapabilityRead, SensorCapabilityUpdate, "/sensor-capabilities", tags=["Sensor Capabilities"])
)
router.include_router(
    make_crud_router(DeviceActuator, DeviceActuatorCreate, DeviceActuatorRead, DeviceActuatorUpdate, "/device-actuators", tags=["Device Actuators"])
)
router.include_router(
    make_crud_router(Cultivation, CultivationCreate, CultivationRead, CultivationUpdate, "/cultivations", tags=["Cultivations"])
)
router.include_router(
    make_crud_router(Threshold, ThresholdCreate, ThresholdRead, ThresholdUpdate, "/thresholds", tags=["Thresholds"])
)
router.include_router(
    make_crud_router(CultivationPhase, CultivationPhaseCreate, CultivationPhaseRead, CultivationPhaseUpdate, "/cultivation-phases", tags=["Cultivation Phases"])
)

# ---------------------------------------------------------------------------
# Tier 3: Operational data (admin read-only for Pi-written tables)
# ---------------------------------------------------------------------------
router.include_router(
    make_crud_router(Measurement, MeasurementCreate, MeasurementRead, MeasurementUpdate, "/measurements", tags=["Measurements"])
)
router.include_router(
    make_crud_router(Photo, PhotoCreate, PhotoRead, PhotoUpdate, "/photos", tags=["Photos"])
)
router.include_router(
    make_crud_router(ActuatorLog, ActuatorLogCreate, ActuatorLogRead, ActuatorLogRead, "/actuator-logs", tags=["Actuator Logs"])
)
