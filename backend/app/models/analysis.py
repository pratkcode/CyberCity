"""Results of analyzing the modeled network: paths, connection checks, validation."""

from enum import StrEnum

from pydantic import Field

from app.models.common import Identifier, StrictModel
from app.models.network import Protocol
from app.models.policy import PolicyDecision


class PathMetric(StrEnum):
    HOPS = "hops"
    LATENCY = "latency"


class NetworkPath(StrictModel):
    device_ids: tuple[Identifier, ...] = Field(min_length=1)
    connection_ids: tuple[Identifier, ...]
    hop_count: int = Field(ge=0)
    total_latency_ms: float = Field(ge=0)
    bottleneck_bandwidth_mbps: int | None = Field(
        description="Lowest bandwidth along the path. None for a zero-hop path."
    )


class PathResult(StrictModel):
    source_id: Identifier
    target_id: Identifier
    metric: PathMetric
    found: bool
    path: NetworkPath | None
    reason: str


class CheckName(StrEnum):
    SOURCE_OPERATIONAL = "source_operational"
    DESTINATION_OPERATIONAL = "destination_operational"
    DESTINATION_SERVICE = "destination_service"
    POLICY = "policy"
    NETWORK_PATH = "network_path"


class CheckStep(StrictModel):
    check: CheckName
    passed: bool
    detail: str


class ConnectionCheck(StrictModel):
    """Whether simulated traffic from one device to another would be permitted."""

    source_id: Identifier
    destination_id: Identifier
    protocol: Protocol
    permitted: bool
    steps: tuple[CheckStep, ...]
    policy: PolicyDecision
    path: NetworkPath | None
    summary: str


class ValidationSeverity(StrEnum):
    ERROR = "error"
    WARNING = "warning"
    INFO = "info"


class ValidationIssue(StrictModel):
    severity: ValidationSeverity
    code: str
    message: str
    subject_ids: tuple[str, ...] = ()


class ValidationReport(StrictModel):
    valid: bool = Field(description="True when there are no error-severity issues.")
    error_count: int = Field(ge=0)
    warning_count: int = Field(ge=0)
    issues: tuple[ValidationIssue, ...]

    @classmethod
    def from_issues(cls, issues: list[ValidationIssue]) -> "ValidationReport":
        order = {ValidationSeverity.ERROR: 0, ValidationSeverity.WARNING: 1, ValidationSeverity.INFO: 2}
        ordered = sorted(issues, key=lambda i: (order[i.severity], i.code, i.subject_ids))
        errors = sum(i.severity is ValidationSeverity.ERROR for i in issues)
        warnings = sum(i.severity is ValidationSeverity.WARNING for i in issues)
        return cls(valid=errors == 0, error_count=errors, warning_count=warnings, issues=tuple(ordered))
