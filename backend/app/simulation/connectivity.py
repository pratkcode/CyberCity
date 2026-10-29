"""Decide whether simulated traffic between two devices would be permitted.

Combines four independent facts and reports each one, so the answer is
explainable rather than a bare yes/no:

1. Both devices are operational.
2. The destination is configured to offer the requested protocol.
3. The zone access policy allows it (end-to-end, source zone → destination zone).
4. A usable network path exists.

Simplification: policy is evaluated once between the two endpoint zones,
like a single central firewall, not hop by hop at each intermediate device.
"""

from app.models import AccessPolicy, CheckName, CheckStep, ConnectionCheck, Protocol
from app.simulation.network_manager import NetworkManager
from app.simulation.policy import evaluate_access


def check_connection(
    network: NetworkManager,
    policy: AccessPolicy,
    source_id: str,
    destination_id: str,
    protocol: Protocol,
) -> ConnectionCheck:
    source = network.get_device(source_id)
    destination = network.get_device(destination_id)

    steps: list[CheckStep] = []
    for check, device in (
        (CheckName.SOURCE_OPERATIONAL, source),
        (CheckName.DESTINATION_OPERATIONAL, destination),
    ):
        steps.append(
            CheckStep(
                check=check,
                passed=device.is_operational,
                detail=f"'{device.id}' is {device.status}.",
            )
        )

    service = destination.offers(protocol)
    steps.append(
        CheckStep(
            check=CheckName.DESTINATION_SERVICE,
            passed=service is not None,
            detail=(
                f"'{destination.id}' offers {protocol} on port {service.port}."
                if service
                else f"'{destination.id}' has no configured {protocol} service."
            ),
        )
    )

    decision = evaluate_access(policy, source.zone_id, destination.zone_id, protocol)
    steps.append(CheckStep(check=CheckName.POLICY, passed=decision.allowed, detail=decision.reason))

    path_result = network.find_path(source_id, destination_id)
    steps.append(
        CheckStep(check=CheckName.NETWORK_PATH, passed=path_result.found, detail=path_result.reason)
    )

    failed = [s for s in steps if not s.passed]
    summary = (
        f"Permitted: {protocol} traffic from '{source_id}' to '{destination_id}' passes all checks."
        if not failed
        else f"Not permitted: {failed[0].detail}"
    )
    return ConnectionCheck(
        source_id=source_id,
        destination_id=destination_id,
        protocol=protocol,
        permitted=not failed,
        steps=tuple(steps),
        policy=decision,
        path=path_result.path,
        summary=summary,
    )
