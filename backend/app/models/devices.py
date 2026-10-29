"""Device models.

Every device shares the fields on ``DeviceBase``. Each category then has its
own small subclass with only the fields that make sense for it, for example
``monitored_zone_ids`` on a security sensor. ``NetworkDevice`` is a
discriminated union on ``device_type``, so JSON input is parsed into the
right subclass and unknown categories are rejected.

Vulnerabilities are fictional modeling records with invented IDs such as
``ccv-2026-0101``. They are not real CVEs and carry no exploit details.
"""

from enum import StrEnum
from typing import Annotated, Literal

from pydantic import Field, TypeAdapter, field_validator, model_validator

from app.models.common import DisplayName, Identifier, StrictModel
from app.models.events import Severity
from app.models.network import Protocol

CURRENT_PATCH_WINDOW_DAYS = 30


class DeviceType(StrEnum):
    ROUTER = "router"
    FIREWALL = "firewall"
    SWITCH = "switch"
    WORKSTATION = "workstation"
    APPLICATION_SERVER = "application_server"
    DATABASE_SERVER = "database_server"
    CLOUD_SERVICE = "cloud_service"
    SECURITY_SENSOR = "security_sensor"
    HOSPITAL_SYSTEM = "hospital_system"
    POWER_CONTROLLER = "power_controller"
    BANKING_SYSTEM = "banking_system"


class OperationalStatus(StrEnum):
    ONLINE = "online"
    DEGRADED = "degraded"
    OFFLINE = "offline"

    @property
    def is_operational(self) -> bool:
        """Degraded devices still pass traffic. Only offline devices are unavailable."""
        return self is not OperationalStatus.OFFLINE


class Criticality(StrEnum):
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class PatchLevel(StrEnum):
    CURRENT = "current"
    BEHIND = "behind"
    UNSUPPORTED = "unsupported"


class DataClassification(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    CONFIDENTIAL = "confidential"
    REGULATED = "regulated"


class PatchStatus(StrictModel):
    level: PatchLevel = PatchLevel.CURRENT
    days_since_patch: int = Field(default=0, ge=0, le=3650)

    @model_validator(mode="after")
    def _level_matches_age(self) -> "PatchStatus":
        recent = self.days_since_patch <= CURRENT_PATCH_WINDOW_DAYS
        if self.level is PatchLevel.CURRENT and not recent:
            raise ValueError(
                f"A 'current' patch level requires days_since_patch <= {CURRENT_PATCH_WINDOW_DAYS}."
            )
        if self.level is PatchLevel.BEHIND and recent:
            raise ValueError(
                f"A 'behind' patch level requires days_since_patch > {CURRENT_PATCH_WINDOW_DAYS}."
            )
        return self


class ConfiguredService(StrictModel):
    """A network service the device is configured to offer, e.g. SQL on 5432."""

    protocol: Protocol
    port: int = Field(ge=1, le=65_535)


class Vulnerability(StrictModel):
    """A fictional, modeled weakness. Used for scoring in later phases only."""

    id: Identifier
    title: DisplayName
    severity: Severity
    affected_protocol: Protocol | None = None
    remediated: bool = False


class DeviceBase(StrictModel):
    id: Identifier
    name: DisplayName
    zone_id: Identifier
    status: OperationalStatus = OperationalStatus.ONLINE
    criticality: Criticality
    configured_services: tuple[ConfiguredService, ...] = ()
    patch: PatchStatus = PatchStatus()
    vulnerabilities: tuple[Vulnerability, ...] = ()

    @field_validator("configured_services")
    @classmethod
    def _unique_ports(cls, value: tuple[ConfiguredService, ...]) -> tuple[ConfiguredService, ...]:
        ports = [s.port for s in value]
        if len(set(ports)) != len(ports):
            raise ValueError("Each configured service must use a different port.")
        return value

    @field_validator("vulnerabilities")
    @classmethod
    def _unique_vulnerabilities(cls, value: tuple[Vulnerability, ...]) -> tuple[Vulnerability, ...]:
        ids = [v.id for v in value]
        if len(set(ids)) != len(ids):
            raise ValueError("Vulnerability ids must be unique per device.")
        return value

    @property
    def is_operational(self) -> bool:
        return self.status.is_operational

    def offers(self, protocol: Protocol) -> ConfiguredService | None:
        return next((s for s in self.configured_services if s.protocol == protocol), None)


ZoneIds = Annotated[tuple[Identifier, ...], Field(min_length=1)]


class RouterDevice(DeviceBase):
    device_type: Literal[DeviceType.ROUTER] = DeviceType.ROUTER
    internet_edge: bool = False


class FirewallDevice(DeviceBase):
    device_type: Literal[DeviceType.FIREWALL] = DeviceType.FIREWALL
    # Descriptive only. Enforcement comes from the AccessPolicy, not this field.
    protected_zone_ids: ZoneIds


class SwitchDevice(DeviceBase):
    device_type: Literal[DeviceType.SWITCH] = DeviceType.SWITCH
    port_count: int = Field(default=24, ge=4, le=96)


class WorkstationDevice(DeviceBase):
    device_type: Literal[DeviceType.WORKSTATION] = DeviceType.WORKSTATION
    user_role: DisplayName


class ApplicationServerDevice(DeviceBase):
    device_type: Literal[DeviceType.APPLICATION_SERVER] = DeviceType.APPLICATION_SERVER
    application: DisplayName


class DatabaseServerDevice(DeviceBase):
    device_type: Literal[DeviceType.DATABASE_SERVER] = DeviceType.DATABASE_SERVER
    data_classification: DataClassification


class CloudServiceDevice(DeviceBase):
    device_type: Literal[DeviceType.CLOUD_SERVICE] = DeviceType.CLOUD_SERVICE
    provider: DisplayName


class SecuritySensorDevice(DeviceBase):
    device_type: Literal[DeviceType.SECURITY_SENSOR] = DeviceType.SECURITY_SENSOR
    monitored_zone_ids: ZoneIds


class HospitalSystemDevice(DeviceBase):
    device_type: Literal[DeviceType.HOSPITAL_SYSTEM] = DeviceType.HOSPITAL_SYSTEM
    clinical_function: DisplayName
    life_safety: bool = False


class PowerControllerDevice(DeviceBase):
    device_type: Literal[DeviceType.POWER_CONTROLLER] = DeviceType.POWER_CONTROLLER
    substation: DisplayName
    control_protocol: Literal[Protocol.MODBUS, Protocol.DNP3]


class BankingSystemDevice(DeviceBase):
    device_type: Literal[DeviceType.BANKING_SYSTEM] = DeviceType.BANKING_SYSTEM
    transaction_role: DisplayName
    data_classification: DataClassification = DataClassification.REGULATED


NetworkDevice = Annotated[
    RouterDevice
    | FirewallDevice
    | SwitchDevice
    | WorkstationDevice
    | ApplicationServerDevice
    | DatabaseServerDevice
    | CloudServiceDevice
    | SecuritySensorDevice
    | HospitalSystemDevice
    | PowerControllerDevice
    | BankingSystemDevice,
    Field(discriminator="device_type"),
]

# Parses a dict or JSON into the correct device subclass.
device_adapter: TypeAdapter[NetworkDevice] = TypeAdapter(NetworkDevice)


def referenced_zone_ids(device: DeviceBase) -> tuple[str, ...]:
    """Zones a device refers to beyond its own (for reference validation)."""
    if isinstance(device, FirewallDevice):
        return device.protected_zone_ids
    if isinstance(device, SecuritySensorDevice):
        return device.monitored_zone_ids
    return ()
