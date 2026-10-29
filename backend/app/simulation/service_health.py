"""Service-health calculation.

A deliberately simple model, not a reproduction of real infrastructure:

- **down**: the entry point is offline, or any *required* dependency fails
  its connection check (offline, missing service, policy denial, or no path).
- **degraded**: everything required works, but the entry point or a
  dependency is in ``degraded`` status, or an *optional* dependency fails.
- **operational**: everything else.

It ignores capacity, load, latency budgets, failover timing, and data
consistency.
"""

from app.models import (
    AccessPolicy,
    CityService,
    DependencyHealth,
    OperationalStatus,
    ServiceHealth,
    ServiceHealthStatus,
)
from app.simulation.connectivity import check_connection
from app.simulation.network_manager import NetworkManager


def evaluate_service_health(
    service: CityService, network: NetworkManager, policy: AccessPolicy
) -> ServiceHealth:
    entry = network.get_device(service.entry_point_id)

    dependencies: list[DependencyHealth] = []
    for dep in service.dependencies:
        client_id = service.client_of(dep)
        check = check_connection(network, policy, client_id, dep.device_id, dep.protocol)
        dependencies.append(
            DependencyHealth(
                device_id=dep.device_id,
                client_id=client_id,
                protocol=dep.protocol,
                role=dep.role,
                required=dep.required,
                device_status=network.get_device(dep.device_id).status,
                ok=check.permitted,
                reason=check.summary,
            )
        )

    status, summary = _classify(entry.status, entry.id, dependencies)
    return ServiceHealth(
        service_id=service.id,
        status=status,
        entry_point_status=entry.status,
        dependencies=tuple(dependencies),
        summary=summary,
    )


def _classify(
    entry_status: OperationalStatus, entry_id: str, deps: list[DependencyHealth]
) -> tuple[ServiceHealthStatus, str]:
    if not entry_status.is_operational:
        return ServiceHealthStatus.DOWN, f"Entry point '{entry_id}' is offline."

    failed_required = [d for d in deps if d.required and not d.ok]
    if failed_required:
        first = failed_required[0]
        return (
            ServiceHealthStatus.DOWN,
            f"Required {first.role} ('{first.device_id}', {first.protocol}) is unavailable. "
            f"{first.reason}",
        )

    failed_optional = [d for d in deps if not d.ok]
    if failed_optional:
        first = failed_optional[0]
        return (
            ServiceHealthStatus.DEGRADED,
            f"Optional {first.role} ('{first.device_id}') is unavailable. {first.reason}",
        )

    degraded = [entry_id] if entry_status is OperationalStatus.DEGRADED else []
    degraded += [d.device_id for d in deps if d.device_status is OperationalStatus.DEGRADED]
    if degraded:
        return (
            ServiceHealthStatus.DEGRADED,
            f"Running on degraded device(s): {', '.join(sorted(set(degraded)))}.",
        )

    count = len(deps)
    noun = "dependency" if count == 1 else "dependencies"
    return ServiceHealthStatus.OPERATIONAL, f"Entry point and all {count} {noun} are available."
