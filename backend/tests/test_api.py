"""API tests: status codes, error envelopes, and response schemas.

Responses are parsed back into the Pydantic response models, so any schema
drift fails here, not in the frontend.
"""

import pytest
from fastapi.testclient import TestClient
from pydantic import TypeAdapter

from app.main import create_app
from app.models import (
    AccessPolicy,
    ConnectionCheck,
    DeviceDetail,
    Organization,
    PathResult,
    ServiceOverview,
    SimulationSummary,
    Topology,
    ValidationReport,
    ZoneSummary,
)
from tests.factories import tiny_city


@pytest.fixture
def tiny_client() -> TestClient:
    return TestClient(create_app(city_definition=tiny_city()))


def parse(model, response, status=200):
    assert response.status_code == status, response.text
    return TypeAdapter(model).validate_python(response.json())


def error_of(response, status):
    assert response.status_code == status, response.text
    return response.json()["error"]


class TestSimulation:
    def test_summary_counts(self, client):
        summary = parse(SimulationSummary, client.get("/api/simulation"))
        assert summary.device_count == 36
        assert summary.zone_count == 7
        assert summary.service_count == 7

    def test_create_simulation(self, client):
        summary = parse(SimulationSummary, client.post("/api/simulation", json={"seed": 5}), 201)
        assert summary.config.seed == 5

    def test_create_rejects_invalid_config(self, client):
        error = error_of(client.post("/api/simulation", json={"seed": -4, "surprise": True}), 422)
        fields = {tuple(d["location"]) for d in error["details"]}
        assert {("body", "seed"), ("body", "surprise")} <= fields


class TestNetwork:
    def test_topology(self, tiny_client):
        topology = parse(Topology, tiny_client.get("/api/network"))
        assert [d.id for d in topology.devices] == ["db-1", "sw-1", "web-1"]
        assert topology.segments == (("db-1", "sw-1", "web-1"),)
        assert topology.isolated_device_ids == ()

    def test_zones(self, tiny_client):
        zones = parse(list[ZoneSummary], tiny_client.get("/api/network/zones"))
        assert {z.zone.id: z.device_ids for z in zones} == {"zone-a": ("sw-1", "web-1"), "zone-b": ("db-1",)}

    def test_device_detail(self, tiny_client):
        detail = parse(DeviceDetail, tiny_client.get("/api/network/devices/sw-1"))
        assert detail.zone.id == "zone-a"
        assert [link.neighbor_id for link in detail.links] == ["db-1", "web-1"]
        assert detail.reachable_device_ids == ("db-1", "web-1")
        assert detail.dependent_service_ids == ()

    def test_device_detail_lists_dependent_services(self, tiny_client):
        detail = parse(DeviceDetail, tiny_client.get("/api/network/devices/db-1"))
        assert detail.dependent_service_ids == ("svc-shop",)

    def test_unknown_device_is_404(self, tiny_client):
        error = error_of(tiny_client.get("/api/network/devices/ghost-1"), 404)
        assert error == {"code": "not_found", "message": "Device 'ghost-1' does not exist.", "details": []}

    @pytest.mark.parametrize("bad_id", ["BAD_ID", "a", "x" * 49, "-dash"])
    def test_malformed_device_id_is_422(self, tiny_client, bad_id):
        error = error_of(tiny_client.get(f"/api/network/devices/{bad_id}"), 422)
        assert error["code"] == "validation_error"
        assert error["details"][0]["location"] == ["path", "device_id"]

    def test_path_found(self, tiny_client):
        result = parse(PathResult, tiny_client.get("/api/network/path", params={"source": "web-1", "target": "db-1"}))
        assert result.found
        assert result.path.device_ids == ("web-1", "sw-1", "db-1")

    def test_no_path_is_200_with_found_false(self, client):
        result = parse(PathResult, client.get("/api/network/path", params={"source": "grid-hmi-01", "target": "grid-plc-02"}))
        assert not result.found
        assert result.path is None

    def test_path_validates_query(self, tiny_client):
        error = error_of(tiny_client.get("/api/network/path", params={"source": "web-1", "target": "db-1", "metric": "fastest"}), 422)
        assert error["details"][0]["location"] == ["query", "metric"]
        error = error_of(tiny_client.get("/api/network/path", params={"source": "web-1"}), 422)
        assert error["details"][0]["location"] == ["query", "target"]

    def test_path_unknown_device_is_404(self, tiny_client):
        error_of(tiny_client.get("/api/network/path", params={"source": "web-1", "target": "ghost-1"}), 404)

    def test_validation_report(self, client):
        report = parse(ValidationReport, client.get("/api/network/validation"))
        assert report.valid
        assert report.warning_count == 2


class TestPolicy:
    def test_rules_in_evaluation_order(self, client):
        policy = parse(AccessPolicy, client.get("/api/policy/rules"))
        priorities = [r.priority for r in policy.rules]
        assert priorities == sorted(priorities)

    def test_check_permitted(self, tiny_client):
        params = {"source": "web-1", "target": "db-1", "protocol": "sql"}
        check = parse(ConnectionCheck, tiny_client.get("/api/policy/check", params=params))
        assert check.permitted
        assert check.policy.matched_rule_id == "allow-sql"

    def test_check_denied_explains_why(self, tiny_client):
        params = {"source": "db-1", "target": "web-1", "protocol": "https"}
        check = parse(ConnectionCheck, tiny_client.get("/api/policy/check", params=params))
        assert not check.permitted
        assert check.policy.default_applied
        assert check.summary.startswith("Not permitted:")

    def test_check_rejects_unknown_protocol(self, tiny_client):
        params = {"source": "web-1", "target": "db-1", "protocol": "telnet"}
        error = error_of(tiny_client.get("/api/policy/check", params=params), 422)
        assert error["details"][0]["location"] == ["query", "protocol"]

    def test_check_unknown_device_is_404(self, tiny_client):
        params = {"source": "web-1", "target": "ghost-1", "protocol": "sql"}
        error_of(tiny_client.get("/api/policy/check", params=params), 404)


class TestCity:
    def test_organizations(self, client):
        orgs = parse(list[Organization], client.get("/api/city/organizations"))
        assert {o.sector for o in orgs} == {"healthcare", "finance", "energy", "government", "education", "business"}

    def test_services_include_health(self, tiny_client):
        overviews = parse(list[ServiceOverview], tiny_client.get("/api/city/services"))
        assert [(o.service.id, o.health.status) for o in overviews] == [("svc-shop", "operational")]
        assert overviews[0].organization.id == "org-test"

    def test_single_service(self, client):
        overview = parse(ServiceOverview, client.get("/api/city/services/svc-grid-control"))
        assert overview.health.status == "degraded"

    def test_unknown_service_is_404(self, client):
        error_of(client.get("/api/city/services/svc-missing"), 404)


def test_invalid_city_fails_fast_at_startup():
    from tests.factories import link

    from app.services.errors import InvalidTopologyError

    with pytest.raises(InvalidTopologyError) as exc:
        create_app(city_definition=tiny_city(connections=(link("web-1", "ghost-1"),)))
    assert exc.value.details[0]["code"] == "unknown_device_reference"
