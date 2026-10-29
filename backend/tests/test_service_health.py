from app.models import (
    CityService,
    OperationalStatus,
    Protocol,
    ServiceDependency,
)
from app.simulation.service_health import evaluate_service_health
from tests.factories import ALLOW_ALL, ZONE_B, link, network, policy, rule, server, switch

SQL, LDAP, HTTPS = Protocol.SQL, Protocol.LDAP, Protocol.HTTPS
ONLINE, DEGRADED, OFFLINE = OperationalStatus.ONLINE, OperationalStatus.DEGRADED, OperationalStatus.OFFLINE


def build(*, web=ONLINE, db=ONLINE, idp=ONLINE, idp_link_permitted=True):
    """web — sw — db (zone-b), and sw — idp. Service: web needs SQL (required) + LDAP (optional)."""
    net = network(
        [
            server("web-1", status=web),
            switch("sw-1"),
            server("db-1", ZONE_B, protocols=(SQL,), status=db),
            server("idp-1", protocols=(LDAP,), status=idp),
        ],
        [link("web-1", "sw-1"), link("sw-1", "db-1"), link("sw-1", "idp-1", permitted=idp_link_permitted)],
    )
    service = CityService(
        id="svc-shop", name="Shop", organization_id="org-test", criticality="high", entry_point_id="web-1",
        dependencies=(
            ServiceDependency(device_id="db-1", protocol=SQL, role="database"),
            ServiceDependency(device_id="idp-1", protocol=LDAP, role="directory", required=False),
        ),
    )
    return service, net


def health(policy_=ALLOW_ALL, **kwargs):
    service, net = build(**kwargs)
    return evaluate_service_health(service, net, policy_)


def test_operational_when_everything_is_available():
    result = health()
    assert result.status == "operational"
    assert all(d.ok for d in result.dependencies)
    assert result.summary == "Entry point and all 2 dependencies are available."


def test_down_when_entry_point_offline():
    result = health(web=OFFLINE)
    assert result.status == "down"
    assert "Entry point 'web-1' is offline" in result.summary


def test_down_when_required_dependency_offline():
    result = health(db=OFFLINE)
    assert result.status == "down"
    db = next(d for d in result.dependencies if d.device_id == "db-1")
    assert not db.ok
    assert db.device_status == OFFLINE


def test_down_when_policy_blocks_required_dependency():
    only_ldap = policy(rule("allow-ldap", 100, "allow", None, None, LDAP))
    result = health(policy_=only_ldap)
    assert result.status == "down"
    assert "Denied by default" in result.summary


def test_degraded_when_optional_dependency_unreachable():
    result = health(idp_link_permitted=False)
    assert result.status == "degraded"
    assert "Optional directory" in result.summary


def test_degraded_when_a_dependency_device_is_degraded():
    result = health(db=DEGRADED)
    assert result.status == "degraded"
    assert "db-1" in result.summary


def test_degraded_entry_point():
    result = health(web=DEGRADED)
    assert result.status == "degraded"
    assert result.entry_point_status == DEGRADED


def test_dependency_checked_from_its_own_client():
    """web → app over HTTPS, then app (not web) → db over SQL."""
    net = network(
        [server("web-1"), server("app-1"), server("db-1", ZONE_B, protocols=(SQL,))],
        [link("web-1", "app-1"), link("app-1", "db-1")],
    )
    service = CityService(
        id="svc-tier", name="Tiered", organization_id="org-test", criticality="high", entry_point_id="web-1",
        dependencies=(
            ServiceDependency(device_id="app-1", protocol=HTTPS, role="app"),
            ServiceDependency(device_id="db-1", protocol=SQL, role="db", client_id="app-1"),
        ),
    )
    # Only zone-a → zone-a HTTPS and zone-a → zone-b SQL. Both pass for the right clients.
    p = policy(
        rule("allow-https", 100, "allow", "zone-a", "zone-a", HTTPS),
        rule("allow-sql", 100, "allow", "zone-a", ZONE_B, SQL),
    )
    result = evaluate_service_health(service, net, p)
    assert result.status == "operational"
    assert [d.client_id for d in result.dependencies] == ["web-1", "app-1"]
