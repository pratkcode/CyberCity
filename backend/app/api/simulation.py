"""Routes for the simulation, its network and city services.

Routes stay thin: they validate input (via Pydantic and path constraints),
call the service, and return models. All logic lives in the service layer.
"""

from typing import Annotated

from fastapi import APIRouter, Path, status

from app.api.dependencies import SimulationServiceDep
from app.models import (
    CityService,
    NetworkDevice,
    NetworkSnapshot,
    SimulationConfig,
    SimulationSummary,
)
from app.models.common import IDENTIFIER_MAX_LENGTH, IDENTIFIER_PATTERN

router = APIRouter(tags=["simulation"])

DeviceIdPath = Annotated[
    str,
    Path(
        min_length=2,
        max_length=IDENTIFIER_MAX_LENGTH,
        pattern=IDENTIFIER_PATTERN,
        description="Lowercase device identifier, e.g. 'hosp-ehr-db-01'.",
    ),
]


@router.get("/simulation", response_model=SimulationSummary)
def get_simulation(service: SimulationServiceDep) -> SimulationSummary:
    return service.summary()


@router.post(
    "/simulation",
    response_model=SimulationSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new simulation from a configuration (replaces the current one).",
)
def create_simulation(config: SimulationConfig, service: SimulationServiceDep) -> SimulationSummary:
    return service.reset(config)


@router.get("/network", response_model=NetworkSnapshot)
def get_network(service: SimulationServiceDep) -> NetworkSnapshot:
    return service.network()


@router.get("/network/devices/{device_id}", response_model=NetworkDevice)
def get_device(device_id: DeviceIdPath, service: SimulationServiceDep) -> NetworkDevice:
    return service.get_device(device_id)


@router.get("/services", response_model=list[CityService])
def list_services(service: SimulationServiceDep) -> list[CityService]:
    return list(service.services())
