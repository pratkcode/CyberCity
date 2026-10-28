"""Models for fictional network devices and the links between them."""

from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import DisplayName, Identifier, StrictModel


class DeviceType(StrEnum):
    WORKSTATION = "workstation"
    SERVER = "server"
    DATABASE = "database"
    ROUTER = "router"
    SWITCH = "switch"
    FIREWALL = "firewall"
    IOT_CONTROLLER = "iot_controller"
    CLOUD_GATEWAY = "cloud_gateway"


class Criticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class LinkType(StrEnum):
    ETHERNET = "ethernet"
    FIBER = "fiber"
    WIRELESS = "wireless"
    VPN = "vpn"


class NetworkDevice(StrictModel):
    """A single simulated device in the city network."""

    id: Identifier
    name: DisplayName
    device_type: DeviceType
    zone: Identifier = Field(description="Logical network segment, e.g. 'hospital-lan'.")
    criticality: Criticality
    online: bool = True
    patch_age_days: int = Field(
        default=0,
        ge=0,
        le=365,
        description="Simulated days since the device was last patched. Seeded at initialization.",
    )


class NetworkConnection(StrictModel):
    """An undirected link between two devices."""

    id: Identifier
    source_id: Identifier
    target_id: Identifier
    link_type: LinkType
    bandwidth_mbps: int = Field(gt=0, le=100_000)
    encrypted: bool = False

    @model_validator(mode="after")
    def _endpoints_must_differ(self) -> "NetworkConnection":
        if self.source_id == self.target_id:
            raise ValueError("A connection cannot link a device to itself.")
        return self
