import pytest

from app.models import CityService, OperationalStatus, Protocol, ServiceDependency, SimulationConfig
from app.simulation.state import CityValidationError, initialize_simulation
from app.simulation.validation import validate_city
from tests.factories import link, policy, rule, server, switch, tiny_city


def codes(report):
    return [(i.severity, i.code) for i in report.issues]


def test_tiny_city_is_valid_with_no_issues():
    report = validate_city(tiny_city())
    assert report.valid
    assert report.issues == ()


def test_connection_to_unknown_device_is_an_error():
    city = tiny_city(connections=(link("web-1", "sw-1"), link("sw-1", "ghost-1")))
    report = validate_city(city)
    assert not report.valid
    assert ("error", "unknown_device_reference") in codes(report)


def test_device_in_unknown_zone_is_an_error():
    city = tiny_city(devices=(server("web-1"), switch("sw-1"), server("db-1", "zone-missing", protocols=(Protocol.SQL,))))
    assert ("error", "unknown_zone_reference") in codes(validate_city(city))


def test_duplicate_device_ids_are_reported():
    city = tiny_city(devices=(server("web-1"), server("web-1"), switch("sw-1"), server("db-1", "zone-b", protocols=(Protocol.SQL,))))
    assert ("error", "duplicate_device_id") in codes(validate_city(city))


def test_parallel_links_are_reported():
    reverse = link("sw-1", "web-1")
    city = tiny_city(connections=(link("web-1", "sw-1"), reverse, link("sw-1", "db-1")))
    assert ("error", "parallel_connection") in codes(validate_city(city))


def test_policy_with_unknown_zone_is_an_error():
    city = tiny_city(policy=policy(rule("allow-x", 1, "allow", "zone-nowhere", None)))
    assert ("error", "unknown_zone_reference") in codes(validate_city(city))


def test_service_with_unknown_device_or_organization():
    bad = CityService(
        id="svc-bad", name="Bad", organization_id="org-missing", criticality="low", entry_point_id="web-1",
        dependencies=(ServiceDependency(device_id="ghost-1", protocol=Protocol.SQL, role="db"),),
    )
    found = codes(validate_city(tiny_city(services=(bad,))))
    assert ("error", "unknown_organization_reference") in found
    assert ("error", "unknown_device_reference") in found


def test_dependency_on_unoffered_protocol_is_an_error():
    wrong = CityService(
        id="svc-x", name="X", organization_id="org-test", criticality="low", entry_point_id="web-1",
        dependencies=(ServiceDependency(device_id="db-1", protocol=Protocol.LDAP, role="directory"),),
    )
    assert ("error", "dependency_protocol_not_offered") in codes(validate_city(tiny_city(services=(wrong,))))


def test_isolated_device_and_segments_are_warnings():
    city = tiny_city(connections=(link("web-1", "sw-1"), link("sw-1", "db-1", permitted=False)))
    report = validate_city(city)
    assert report.valid
    assert ("warning", "isolated_device") in codes(report)
    assert ("warning", "multiple_segments") in codes(report)


def test_offline_device_severity_depends_on_criticality():
    city = tiny_city(devices=(
        server("web-1", status=OperationalStatus.OFFLINE, criticality="critical"),
        switch("sw-1"),
        server("db-1", "zone-b", protocols=(Protocol.SQL,)),
    ))
    assert ("warning", "device_offline") in codes(validate_city(city))


def test_errors_are_listed_before_warnings():
    city = tiny_city(connections=(link("web-1", "ghost-1"),))
    report = validate_city(city)
    assert report.issues[0].severity == "error"


def test_initialization_refuses_an_invalid_city():
    city = tiny_city(connections=(link("web-1", "ghost-1"),))
    with pytest.raises(CityValidationError) as exc:
        initialize_simulation(SimulationConfig(), city)
    assert exc.value.report.error_count == 1
