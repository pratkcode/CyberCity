"""Small builders for deterministic test networks.

Tests describe tiny graphs explicitly instead of relying on the sample city,
so each assertion can be checked by reading the test alone.
"""

from app.models import (
    AccessPolicy,
    ApplicationServerDevice,
    CityDefinition,
    CityService,
    ConfiguredService,
    Criticality,
    NetworkConnection,
    NetworkZone,
    OperationalStatus,
    Organization,
    PolicyAction,
    PolicyRule,
    Protocol,
    Sector,
    ServiceDependency,
    SwitchDevice,
    ZoneKind,
)
from app.simulation.network_manager import NetworkManager

ZONE_A = "zone-a"
ZONE_B = "zone-b"
PORTS = {Protocol.HTTPS: 443, Protocol.SQL: 5432, Protocol.LDAP: 389, Protocol.SSH: 22}


def zone(zone_id: str, kind: ZoneKind = ZoneKind.INTERNAL) -> NetworkZone:
    return NetworkZone(id=zone_id, name=zone_id.title(), kind=kind)


DEFAULT_ZONES = (zone(ZONE_A), zone(ZONE_B, ZoneKind.RESTRICTED))


def server(
    device_id: str,
    zone_id: str = ZONE_A,
    *,
    protocols: tuple[Protocol, ...] = (Protocol.HTTPS,),
    status: OperationalStatus = OperationalStatus.ONLINE,
    criticality: Criticality = Criticality.MEDIUM,
) -> ApplicationServerDevice:
    return ApplicationServerDevice(
        id=device_id,
        name=f"Server {device_id}",
        zone_id=zone_id,
        status=status,
        criticality=criticality,
        application="Test app",
        configured_services=tuple(ConfiguredService(protocol=p, port=PORTS[p]) for p in protocols),
    )


def switch(device_id: str, zone_id: str = ZONE_A, status: OperationalStatus = OperationalStatus.ONLINE) -> SwitchDevice:
    return SwitchDevice(id=device_id, name=f"Switch {device_id}", zone_id=zone_id, status=status, criticality=Criticality.LOW)


def link(a: str, b: str, *, latency: float = 1.0, mbps: int = 1000, permitted: bool = True) -> NetworkConnection:
    return NetworkConnection(
        id=f"link-{a}-{b}", source_id=a, target_id=b, link_type="ethernet",
        bandwidth_mbps=mbps, latency_ms=latency, traffic_permitted=permitted,
    )


def network(devices, links=(), zones=DEFAULT_ZONES) -> NetworkManager:
    return NetworkManager.build(zones, devices, links)


def rule(rule_id: str, priority: int, action: str, src: str | None, dst: str | None, *protocols: Protocol) -> PolicyRule:
    return PolicyRule(
        id=rule_id, priority=priority, action=PolicyAction(action),
        source_zone_id=src, destination_zone_id=dst, protocols=protocols,
    )


def policy(*rules: PolicyRule) -> AccessPolicy:
    return AccessPolicy(rules=rules)


ALLOW_ALL = policy(rule("allow-all", 1000, "allow", None, None))


def tiny_city(**overrides) -> CityDefinition:
    """web (zone-a) — sw — db (zone-b). One service: web needs SQL on db."""
    fields = dict(
        zones=DEFAULT_ZONES,
        devices=(server("web-1"), switch("sw-1"), server("db-1", ZONE_B, protocols=(Protocol.SQL,))),
        connections=(link("web-1", "sw-1"), link("sw-1", "db-1")),
        policy=policy(rule("allow-sql", 100, "allow", ZONE_A, ZONE_B, Protocol.SQL)),
        organizations=(Organization(id="org-test", name="Test Org", sector=Sector.BUSINESS),),
        services=(
            CityService(
                id="svc-shop", name="Shop", organization_id="org-test", criticality=Criticality.HIGH,
                entry_point_id="web-1",
                dependencies=(ServiceDependency(device_id="db-1", protocol=Protocol.SQL, role="database"),),
            ),
        ),
    )
    fields.update(overrides)
    return CityDefinition(**fields)
