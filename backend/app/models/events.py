"""Model for simulated security events.

Phase 1 only defines the shape. No events are generated yet.
"""

from enum import StrEnum

from pydantic import Field

from app.models.common import Identifier, StrictModel


class Severity(StrEnum):
    INFO = "info"
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class EventCategory(StrEnum):
    AUTHENTICATION = "authentication"
    MALWARE = "malware"
    NETWORK_ANOMALY = "network_anomaly"
    POLICY_VIOLATION = "policy_violation"
    AVAILABILITY = "availability"


class SecurityEvent(StrictModel):
    """A fictional alert raised against a simulated device."""

    id: Identifier
    tick: int = Field(ge=0, description="Simulation tick when the event occurred.")
    severity: Severity
    category: EventCategory
    device_id: Identifier
    summary: str = Field(min_length=1, max_length=280)
