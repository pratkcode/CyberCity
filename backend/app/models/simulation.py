"""Simulation configuration, city definition, and API view models."""

from enum import StrEnum

from pydantic import Field

from app.models.city import CityService, Organization, ServiceHealth
from app.models.common import DisplayName, Identifier, StrictModel
from app.models.devices import NetworkDevice
from app.models.network import NetworkConnection, NetworkZone
from app.models.policy import AccessPolicy

MAX_SEED = 2**32 - 1


class Difficulty(StrEnum):
    TRAINING = "training"
    STANDARD = "standard"
    CHALLENGING = "challenging"


class SimulationConfig(StrictModel):
    """Inputs that fully determine a new simulation's initial state."""

    seed: int = Field(default=1337, ge=0, le=MAX_SEED)
    city_name: DisplayName = "CyberCity"
    difficulty: Difficulty = Difficulty.STANDARD
    starting_budget: int = Field(default=250_000, ge=0, le=10_000_000)
    tick_minutes: int = Field(
        default=15, ge=1, le=240, description="Simulated minutes per tick."
    )


class CityDefinition(StrictModel):
    """Everything needed to build a city. Validated before a simulation starts."""

    zones: tuple[NetworkZone, ...]
    devices: tuple[NetworkDevice, ...]
    connections: tuple[NetworkConnection, ...]
    policy: AccessPolicy
    organizations: tuple[Organization, ...]
    services: tuple[CityService, ...]


class SimulationSummary(StrictModel):
    config: SimulationConfig
    tick: int = Field(ge=0)
    simulated_minutes: int = Field(ge=0)
    zone_count: int = Field(ge=0)
    device_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)
    organization_count: int = Field(ge=0)
    service_count: int = Field(ge=0)


class Topology(StrictModel):
    """The complete modeled network, for the map."""

    zones: tuple[NetworkZone, ...]
    devices: tuple[NetworkDevice, ...]
    connections: tuple[NetworkConnection, ...]
    segments: tuple[tuple[Identifier, ...], ...] = Field(
        description="Groups of operational devices that can reach each other, largest first."
    )
    isolated_device_ids: tuple[Identifier, ...] = Field(
        description="Operational devices outside the primary (largest) segment."
    )


class DeviceLink(StrictModel):
    connection: NetworkConnection
    neighbor_id: Identifier


class DeviceDetail(StrictModel):
    device: NetworkDevice
    zone: NetworkZone
    links: tuple[DeviceLink, ...]
    reachable_device_ids: tuple[Identifier, ...]
    isolated: bool
    dependent_service_ids: tuple[Identifier, ...]


class ZoneSummary(StrictModel):
    zone: NetworkZone
    device_ids: tuple[Identifier, ...]
    operational_device_count: int = Field(ge=0)


class ServiceOverview(StrictModel):
    service: CityService
    organization: Organization
    health: ServiceHealth
