"""Models for the city services that depend on the network."""

from enum import StrEnum

from pydantic import Field, field_validator

from app.models.common import DisplayName, Identifier, StrictModel


class Sector(StrEnum):
    HEALTHCARE = "healthcare"
    FINANCE = "finance"
    ENERGY = "energy"
    GOVERNMENT = "government"
    BUSINESS = "business"
    CLOUD = "cloud"


class ServiceStatus(StrEnum):
    OPERATIONAL = "operational"
    DEGRADED = "degraded"
    OFFLINE = "offline"


class CityService(StrictModel):
    """A public-facing service (e.g. hospital records) and the devices it relies on."""

    id: Identifier
    name: DisplayName
    sector: Sector
    status: ServiceStatus = ServiceStatus.OPERATIONAL
    dependency_ids: tuple[Identifier, ...] = Field(min_length=1)

    @field_validator("dependency_ids")
    @classmethod
    def _no_duplicate_dependencies(cls, value: tuple[str, ...]) -> tuple[str, ...]:
        if len(set(value)) != len(value):
            raise ValueError("dependency_ids must not contain duplicates.")
        return value
