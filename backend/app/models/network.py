"""Models for network zones, modeled protocols, and the links between devices.

Connection properties describe how a link is *configured* (capacity,
latency, whether traffic is administratively permitted). They do not
record traffic or activity, which a later phase may model separately.
"""

from enum import StrEnum

from pydantic import Field, model_validator

from app.models.common import DisplayName, Identifier, StrictModel


class Protocol(StrEnum):
    """Protocol labels for modeled traffic. Labels only. Nothing is transmitted."""

    HTTP = "http"
    HTTPS = "https"
    SSH = "ssh"
    RDP = "rdp"
    SQL = "sql"
    LDAP = "ldap"
    DNS = "dns"
    SMTP = "smtp"
    SMB = "smb"
    SYSLOG = "syslog"
    DICOM = "dicom"
    MODBUS = "modbus"
    DNP3 = "dnp3"


class ZoneKind(StrEnum):
    PUBLIC = "public"
    INTERNAL = "internal"
    RESTRICTED = "restricted"
    MONITORING = "monitoring"
    CRITICAL_INFRASTRUCTURE = "critical_infrastructure"
    CLOUD = "cloud"


class NetworkZone(StrictModel):
    """A logical network segment. Access policies are written between zones."""

    id: Identifier
    name: DisplayName
    kind: ZoneKind
    description: str = Field(default="", max_length=240)


class LinkType(StrEnum):
    ETHERNET = "ethernet"
    FIBER = "fiber"
    WIRELESS = "wireless"
    VPN = "vpn"


class NetworkConnection(StrictModel):
    """An undirected link between two devices."""

    id: Identifier
    source_id: Identifier
    target_id: Identifier
    link_type: LinkType
    bandwidth_mbps: int = Field(gt=0, le=100_000)
    latency_ms: float = Field(default=1.0, ge=0, le=5_000)
    encrypted: bool = False
    traffic_permitted: bool = Field(
        default=True,
        description="False models a link that exists physically but carries no routed "
        "traffic (e.g. administratively disabled or a passive monitoring tap).",
    )
    description: str = Field(default="", max_length=160)

    @model_validator(mode="after")
    def _endpoints_must_differ(self) -> "NetworkConnection":
        if self.source_id == self.target_id:
            raise ValueError("A connection cannot link a device to itself.")
        return self

    def other_end(self, device_id: str) -> str:
        return self.target_id if device_id == self.source_id else self.source_id
