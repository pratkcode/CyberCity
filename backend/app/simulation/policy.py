"""Zone-based access-policy evaluation.

Evaluation rules
----------------
1. Rules are ordered by ``priority`` (lowest first). At equal priority, deny
   rules come before allow rules, and then rules are ordered by ``id``. That
   ordering is total, so evaluation is fully deterministic.
2. The first rule whose source zone, destination zone and protocol all match
   decides the outcome. A ``None`` zone or an empty protocol list matches anything.
3. If no rule matches, traffic is denied (**default deny**).

This module knows nothing about the graph. It only answers "may zone A send
protocol P to zone B?". Topology checks happen in ``connectivity.py``.
"""

from app.models import AccessPolicy, PolicyAction, PolicyDecision, PolicyRule, Protocol


def evaluation_order(policy: AccessPolicy) -> tuple[PolicyRule, ...]:
    return tuple(
        sorted(
            policy.rules,
            key=lambda r: (r.priority, 0 if r.action is PolicyAction.DENY else 1, r.id),
        )
    )


def rule_matches(rule: PolicyRule, source_zone_id: str, destination_zone_id: str, protocol: Protocol) -> bool:
    return (
        (rule.source_zone_id is None or rule.source_zone_id == source_zone_id)
        and (rule.destination_zone_id is None or rule.destination_zone_id == destination_zone_id)
        and (not rule.protocols or protocol in rule.protocols)
    )


def describe_scope(rule: PolicyRule) -> str:
    source = rule.source_zone_id or "any zone"
    destination = rule.destination_zone_id or "any zone"
    protocols = ", ".join(rule.protocols) if rule.protocols else "any protocol"
    return f"{source} → {destination} over {protocols}"


def evaluate_access(
    policy: AccessPolicy, source_zone_id: str, destination_zone_id: str, protocol: Protocol
) -> PolicyDecision:
    request = f"{source_zone_id} → {destination_zone_id} over {protocol}"

    for rule in evaluation_order(policy):
        if rule_matches(rule, source_zone_id, destination_zone_id, protocol):
            allowed = rule.action is PolicyAction.ALLOW
            verb = "Allowed" if allowed else "Denied"
            note = f" ({rule.description})" if rule.description else ""
            return PolicyDecision(
                allowed=allowed,
                source_zone_id=source_zone_id,
                destination_zone_id=destination_zone_id,
                protocol=protocol,
                matched_rule_id=rule.id,
                default_applied=False,
                reason=f"{verb} by rule '{rule.id}' (priority {rule.priority}) for {request}{note}.",
            )

    return PolicyDecision(
        allowed=False,
        source_zone_id=source_zone_id,
        destination_zone_id=destination_zone_id,
        protocol=protocol,
        matched_rule_id=None,
        default_applied=True,
        reason=f"Denied by default: no rule matches {request}.",
    )


def referenced_zone_ids(policy: AccessPolicy) -> set[str]:
    zones: set[str] = set()
    for rule in policy.rules:
        zones.update(z for z in (rule.source_zone_id, rule.destination_zone_id) if z)
    return zones
