"""Checks that the bundled sample city meets the Phase 2 requirements."""

import pytest

from app.models import DeviceType, Protocol, SimulationConfig, ZoneKind
from app.simulation.connectivity import check_connection
from app.simulation.sample_city import sample_city_definition
from app.simulation.service_health import evaluate_service_health
from app.simulation.state import initialize_simulation
from app.simulation.validation import validate_city


@pytest.fixture(scope="module")
def state():
    return initialize_simulation(SimulationConfig())


def test_size_is_within_target_range(state):
    assert 25 <= len(state.network.devices()) <= 40


def test_every_device_category_is_present(state):
    assert {d.device_type for d in state.network.devices()} == set(DeviceType)


def test_required_zone_kinds_are_present(state):
    kinds = {z.kind for z in state.network.zones()}
    assert {ZoneKind.PUBLIC, ZoneKind.INTERNAL, ZoneKind.RESTRICTED, ZoneKind.MONITORING,
            ZoneKind.CRITICAL_INFRASTRUCTURE} <= kinds


def test_every_zone_has_devices(state):
    assert all(state.network.devices_in_zone(z.id) for z in state.network.zones())


def test_definition_validates_without_errors():
    report = validate_city(sample_city_definition())
    assert report.valid
    assert {i.code for i in report.issues} == {"isolated_device", "multiple_segments", "device_offline"}


def test_substation_seven_is_the_only_isolated_device(state):
    assert state.network.isolated_device_ids() == ("grid-plc-02",)
    assert len(state.network.segments()) == 2


def test_service_health_matches_the_modeled_state(state):
    statuses = {s.id: evaluate_service_health(s, state.network, state.policy).status for s in state.services}
    assert statuses == {
        "svc-ehr": "operational",
        "svc-imaging": "operational",
        "svc-online-banking": "operational",
        "svc-grid-control": "degraded",
        "svc-permits": "operational",
        "svc-student-portal": "operational",
        "svc-retail-payments": "operational",
    }


def test_services_depend_on_multiple_devices(state):
    ehr = next(s for s in state.services if s.id == "svc-ehr")
    assert len(ehr.device_ids()) == 4


@pytest.mark.parametrize(
    ("source", "target", "protocol", "permitted", "rule"),
    [
        ("gov-app-01", "gov-db-01", Protocol.SQL, True, "allow-corp-to-data"),
        ("web-portal-01", "gov-db-01", Protocol.SQL, False, "deny-dmz-to-data"),
        ("gov-app-01", "grid-plc-01", Protocol.MODBUS, False, "deny-into-grid"),
        ("grid-hmi-01", "grid-plc-01", Protocol.MODBUS, True, "allow-grid-internal"),
        ("grid-hmi-01", "soc-siem-01", Protocol.SYSLOG, True, "allow-log-collection"),
        ("grid-hmi-01", "cloud-mail-01", Protocol.SMTP, False, "deny-grid-egress"),
        ("hosp-ws-01", "gov-app-01", Protocol.HTTPS, False, None),
    ],
)
def test_segmentation_policy(state, source, target, protocol, permitted, rule):
    result = check_connection(state.network, state.policy, source, target, protocol)
    assert result.policy.allowed is permitted
    assert result.policy.matched_rule_id == rule
