"""Validate a city definition before a simulation starts.

Checks run in two passes:

1. **References and uniqueness** (errors): duplicate IDs, devices in unknown
   zones, links to unknown devices, parallel links, policy rules naming
   unknown zones, services pointing at unknown organizations or devices, and
   dependencies on protocols the target device doesn't offer.
2. **Graph health** (warnings/info), only when pass 1 found no errors:
   split segments, isolated devices, offline devices, and empty zones.

Errors block a simulation from starting. Warnings describe a valid but
notable state, such as a deliberately isolated device.
"""

from collections import Counter
from collections.abc import Iterable

from app.models import (
    CityDefinition,
    Criticality,
    ValidationIssue,
    ValidationReport,
    ValidationSeverity,
)
from app.models.devices import referenced_zone_ids as device_zone_refs
from app.simulation.network_manager import NetworkManager
from app.simulation.policy import referenced_zone_ids as policy_zone_refs

E, W, I = ValidationSeverity.ERROR, ValidationSeverity.WARNING, ValidationSeverity.INFO


def validate_city(city: CityDefinition) -> ValidationReport:
    issues = _reference_issues(city)
    if not any(i.severity is E for i in issues):
        network = NetworkManager.build(city.zones, city.devices, city.connections)
        issues += _graph_issues(network)
    return ValidationReport.from_issues(issues)


def _duplicates(kind: str, ids: Iterable[str]) -> list[ValidationIssue]:
    return [
        ValidationIssue(severity=E, code=f"duplicate_{kind}_id", message=f"Duplicate {kind} id '{i}'.", subject_ids=(i,))
        for i, n in sorted(Counter(ids).items())
        if n > 1
    ]


def _reference_issues(city: CityDefinition) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []
    issues += _duplicates("zone", (z.id for z in city.zones))
    issues += _duplicates("device", (d.id for d in city.devices))
    issues += _duplicates("connection", (c.id for c in city.connections))
    issues += _duplicates("organization", (o.id for o in city.organizations))
    issues += _duplicates("service", (s.id for s in city.services))

    zone_ids = {z.id for z in city.zones}
    devices = {d.id: d for d in city.devices}
    org_ids = {o.id for o in city.organizations}

    def unknown(code: str, message: str, *subjects: str) -> None:
        issues.append(ValidationIssue(severity=E, code=code, message=message, subject_ids=subjects))

    for device in city.devices:
        for zone_id in (device.zone_id, *device_zone_refs(device)):
            if zone_id not in zone_ids:
                unknown("unknown_zone_reference", f"Device '{device.id}' references unknown zone '{zone_id}'.", device.id, zone_id)

    seen_pairs: dict[frozenset[str], str] = {}
    for conn in city.connections:
        for endpoint in (conn.source_id, conn.target_id):
            if endpoint not in devices:
                unknown("unknown_device_reference", f"Connection '{conn.id}' references unknown device '{endpoint}'.", conn.id, endpoint)
        pair = frozenset((conn.source_id, conn.target_id))
        if pair in seen_pairs:
            unknown("parallel_connection", f"Connection '{conn.id}' duplicates link '{seen_pairs[pair]}'.", conn.id, seen_pairs[pair])
        seen_pairs.setdefault(pair, conn.id)

    for zone_id in sorted(policy_zone_refs(city.policy) - zone_ids):
        unknown("unknown_zone_reference", f"Access policy references unknown zone '{zone_id}'.", zone_id)

    for service in city.services:
        if service.organization_id not in org_ids:
            unknown("unknown_organization_reference", f"Service '{service.id}' references unknown organization '{service.organization_id}'.", service.id)
        for device_id in service.device_ids():
            if device_id not in devices:
                unknown("unknown_device_reference", f"Service '{service.id}' references unknown device '{device_id}'.", service.id, device_id)
        for dep in service.dependencies:
            target = devices.get(dep.device_id)
            if target is not None and target.offers(dep.protocol) is None:
                unknown(
                    "dependency_protocol_not_offered",
                    f"Service '{service.id}' needs {dep.protocol} on '{dep.device_id}', which is not configured to offer it.",
                    service.id, dep.device_id,
                )
    return issues


def _graph_issues(network: NetworkManager) -> list[ValidationIssue]:
    issues: list[ValidationIssue] = []

    segments = network.segments()
    if len(segments) > 1:
        sizes = ", ".join(str(len(s)) for s in segments)
        issues.append(ValidationIssue(
            severity=W, code="multiple_segments",
            message=f"Operational devices form {len(segments)} separate segments (sizes: {sizes}).",
        ))
    for device_id in network.isolated_device_ids():
        issues.append(ValidationIssue(
            severity=W, code="isolated_device",
            message=f"'{device_id}' is operational but cut off from the primary network segment.",
            subject_ids=(device_id,),
        ))

    for device in network.devices():
        if not device.is_operational:
            important = device.criticality in (Criticality.HIGH, Criticality.CRITICAL)
            issues.append(ValidationIssue(
                severity=W if important else I, code="device_offline",
                message=f"'{device.id}' ({device.criticality} criticality) is offline.",
                subject_ids=(device.id,),
            ))

    for zone in network.zones():
        if not network.devices_in_zone(zone.id):
            issues.append(ValidationIssue(
                severity=I, code="empty_zone", message=f"Zone '{zone.id}' has no devices.", subject_ids=(zone.id,),
            ))
    return issues
