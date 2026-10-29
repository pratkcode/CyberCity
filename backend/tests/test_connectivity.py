from app.models import OperationalStatus, Protocol
from app.simulation.connectivity import check_connection
from tests.factories import ALLOW_ALL, ZONE_A, ZONE_B, link, network, policy, rule, server, switch

SQL = Protocol.SQL


def two_zone_network(*, db_status=OperationalStatus.ONLINE, permitted=True):
    return network(
        [server("web-1"), switch("sw-1"), server("db-1", ZONE_B, protocols=(SQL,), status=db_status)],
        [link("web-1", "sw-1"), link("sw-1", "db-1", permitted=permitted)],
    )


ALLOW_SQL = policy(rule("allow-sql", 100, "allow", ZONE_A, ZONE_B, SQL))


def failed_checks(result):
    return [s.check for s in result.steps if not s.passed]


def test_permitted_when_every_check_passes():
    result = check_connection(two_zone_network(), ALLOW_SQL, "web-1", "db-1", SQL)
    assert result.permitted
    assert failed_checks(result) == []
    assert result.path.device_ids == ("web-1", "sw-1", "db-1")
    assert result.policy.matched_rule_id == "allow-sql"


def test_denied_by_default_policy():
    result = check_connection(two_zone_network(), policy(), "web-1", "db-1", SQL)
    assert not result.permitted
    assert failed_checks(result) == ["policy"]
    assert "Denied by default" in result.summary


def test_missing_service_on_destination():
    result = check_connection(two_zone_network(), ALLOW_ALL, "web-1", "db-1", Protocol.HTTPS)
    assert failed_checks(result) == ["destination_service"]
    assert "no configured https service" in result.summary


def test_offline_destination_fails_status_and_path():
    result = check_connection(two_zone_network(db_status=OperationalStatus.OFFLINE), ALLOW_SQL, "web-1", "db-1", SQL)
    assert failed_checks(result) == ["destination_operational", "network_path"]


def test_policy_allows_but_topology_blocks():
    result = check_connection(two_zone_network(permitted=False), ALLOW_SQL, "web-1", "db-1", SQL)
    assert failed_checks(result) == ["network_path"]
    assert result.policy.allowed
    assert result.path is None


def test_reports_every_check_in_fixed_order():
    result = check_connection(two_zone_network(), ALLOW_SQL, "web-1", "db-1", SQL)
    assert [s.check for s in result.steps] == [
        "source_operational", "destination_operational", "destination_service", "policy", "network_path",
    ]
