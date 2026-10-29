"""City organizations, the services they run, and service-health results."""

from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import DisplayName, Identifier, StrictModel
from app.models.devices import Criticality, OperationalStatus
from app.models.network import Protocol


class Sector(StrEnum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ENERGY = "energy"
    GOVERNMENT = "government"
    EDUCATION = "education"
    BUSINESS = "business"


class Organization(StrictModel):
    id: Identifier
    name: DisplayName
    sector: Sector
    description: str = Field(default="", max_length=240)


class ServiceDependency(StrictModel):
    """One device a service needs, reached from a client device over a protocol.

    ``client_id`` is the device that talks to the dependency. It defaults to the
    service's entry point, so a three-tier chain (web → app → database) is
    written with the database dependency's client set to the app server.
    """

    device_id: Identifier
    protocol: Protocol
    role: DisplayName
    required: bool = True
    client_id: Identifier | None = None


class CityService(StrictModel):
    id: Identifier
    name: DisplayName
    organization_id: Identifier
    criticality: Criticality
    entry_point_id: Identifier = Field(description="Device where users reach this service.")
    dependencies: tuple[ServiceDependency, ...] = ()
    description: str = Field(default="", max_length=240)

    @model_validator(mode="after")
    def _check_dependencies(self) -> "CityService":
        seen: set[tuple[str, str, str]] = set()
        for dep in self.dependencies:
            client = dep.client_id or self.entry_point_id
            if dep.device_id == client:
                raise ValueError(f"Dependency on '{dep.device_id}' cannot use itself as client.")
            key = (client, dep.device_id, dep.protocol)
            if key in seen:
                raise ValueError(f"Duplicate dependency on '{dep.device_id}' over {dep.protocol}.")
            seen.add(key)
        return self

    def client_of(self, dependency: ServiceDependency) -> str:
        return dependency.client_id or self.entry_point_id

    def device_ids(self) -> tuple[str, ...]:
        """Entry point plus every dependency and client, sorted and unique."""
        ids = {self.entry_point_id}
        for dep in self.dependencies:
            ids.update((dep.device_id, self.client_of(dep)))
        return tuple(sorted(ids))


class ServiceHealthStatus(StrEnum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    DOWN = "down"


class DependencyHealth(StrictModel):
    device_id: Identifier
    client_id: Identifier
    protocol: Protocol
    role: str
    required: bool
    device_status: OperationalStatus
    ok: bool
    reason: str


class ServiceHealth(StrictModel):
    service_id: Identifier
    status: ServiceHealthStatus
    entry_point_status: OperationalStatus
    dependencies: tuple[DependencyHealth, ...]
    summary: str
