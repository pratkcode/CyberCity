"""Zone access policy for the sample city.

Priority bands: 10–40 are guardrails (denies plus narrow exceptions), and
100+ are ordinary business allowances. Anything not matched is denied by default.
"""

from app.models import AccessPolicy, PolicyAction, PolicyRule, Protocol as P
from app.simulation.sample_city.devices import CLINICAL, CLOUD, CORP, DATA, GRID, PUBLIC, SOC

ALLOW, DENY = PolicyAction.ALLOW, PolicyAction.DENY


def rule(id: str, priority: int, action: PolicyAction, src: str | None, dst: str | None,
         protocols: tuple[P, ...] = (), description: str = "") -> PolicyRule:
    return PolicyRule(id=id, priority=priority, action=action, source_zone_id=src,
                      destination_zone_id=dst, protocols=protocols, description=description)


SAMPLE_POLICY = AccessPolicy(rules=(
    # Guardrails
    rule("deny-dmz-to-data", 10, DENY, PUBLIC, DATA, description="Internet-facing systems never query databases directly"),
    rule("deny-cloud-to-data", 10, DENY, CLOUD, DATA, description="Hosted services have no database access"),
    rule("allow-log-collection", 20, ALLOW, None, SOC, (P.SYSLOG,), "Every zone may ship logs to the SOC"),
    rule("allow-grid-internal", 30, ALLOW, GRID, GRID, (P.MODBUS, P.DNP3, P.SSH), "OT control traffic stays inside the grid zone"),
    rule("deny-grid-egress", 35, DENY, GRID, None, description="OT devices may not initiate other traffic"),
    rule("deny-into-grid", 40, DENY, None, GRID, description="Only grid-internal traffic may reach OT devices"),
    # Business allowances
    rule("allow-dmz-internal", 100, ALLOW, PUBLIC, PUBLIC, (P.HTTPS,)),
    rule("allow-dmz-to-corp-web", 100, ALLOW, PUBLIC, CORP, (P.HTTPS,), "Public front ends call internal application APIs"),
    rule("allow-corp-internal", 100, ALLOW, CORP, CORP, description="Unrestricted inside the corporate LAN"),
    rule("allow-corp-to-dmz-web", 100, ALLOW, CORP, PUBLIC, (P.HTTPS,)),
    rule("allow-clinical-internal", 100, ALLOW, CLINICAL, CLINICAL),
    rule("allow-soc-internal", 100, ALLOW, SOC, SOC),
    rule("allow-corp-to-data", 110, ALLOW, CORP, DATA, (P.SQL,), "Application servers query their databases"),
    rule("allow-clinical-to-data", 110, ALLOW, CLINICAL, DATA, (P.SQL,), "Clinical systems query patient records"),
    rule("allow-clinical-identity", 120, ALLOW, CLINICAL, CORP, (P.LDAP,), "Clinical sign-on uses the citywide directory"),
    rule("allow-cloud-services", 130, ALLOW, None, CLOUD, (P.HTTPS, P.SMTP), "Backup and email are reachable from any zone"),
))
