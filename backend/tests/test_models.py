import pytest
from pydantic import ValidationError

from app.models import (
    AccessPolicy,
    CityService,
    DeviceType,
    FirewallDevice,
    NetworkConnection,
    PatchStatus,
    PolicyRule,
    PowerControllerDevice,
    SecurityEvent,
    ServiceDependency,
    SimulationConfig,
    device_adapter,
)
from tests.factories import server

BASE = {"id": "dev-01", "name": "Device", "zone_id": "zone-a", "criticality": "medium"}

# Minimal valid extra fields for each category.
CATEGORY_FIELDS = {
    "router": {},
    "firewall": {"protected_zone_ids": ["zone-a"]},
    "switch": {},
    "workstation": {"user_role": "Clerk"},
    "application_server": {"application": "Portal"},
    "database_server": {"data_classification": "regulated"},
    "cloud_service": {"provider": "Fictional Cloud"},
    "security_sensor": {"monitored_zone_ids": ["zone-a"]},
    "hospital_system": {"clinical_function": "Imaging"},
    "power_controller": {"substation": "Sub 1", "control_protocol": "modbus"},
    "banking_system": {"transaction_role": "Payments"},
}


class TestDeviceCategories:
    def test_every_category_has_test_data(self):
        assert set(CATEGORY_FIELDS) == {t.value for t in DeviceType}

    @pytest.mark.parametrize("device_type", list(CATEGORY_FIELDS))
    def test_each_category_parses_to_its_own_model(self, device_type):
        device = device_adapter.validate_python(BASE | {"device_type": device_type} | CATEGORY_FIELDS[device_type])
        assert device.device_type == device_type
        assert device.status == "online"
        assert device.patch.level == "current"

    def test_unknown_category_is_rejected(self):
        with pytest.raises(ValidationError):
            device_adapter.validate_python(BASE | {"device_type": "mainframe"})

    def test_category_specific_fields_are_required(self):
        with pytest.raises(ValidationError, match="protected_zone_ids"):
            FirewallDevice(**BASE)

    def test_fields_from_other_categories_are_rejected(self):
        with pytest.raises(ValidationError):
            device_adapter.validate_python(BASE | {"device_type": "router", "user_role": "Clerk"})

    def test_power_controller_requires_an_ot_protocol(self):
        with pytest.raises(ValidationError):
            PowerControllerDevice(**BASE, substation="Sub 1", control_protocol="https")


class TestDeviceValidation:
    @pytest.mark.parametrize(
        "bad_id",
        ["", "a", "Has-Upper", "under_score", "-leading", "trailing-", "double--dash", "1starts-digit", "x" * 49],
    )
    def test_rejects_invalid_identifiers(self, bad_id):
        with pytest.raises(ValidationError):
            server(bad_id)

    def test_rejects_duplicate_ports(self):
        with pytest.raises(ValidationError, match="different port"):
            device_adapter.validate_python(BASE | {
                "device_type": "switch",
                "configured_services": [{"protocol": "ssh", "port": 22}, {"protocol": "https", "port": 22}],
            })

    @pytest.mark.parametrize("port", [0, 65_536])
    def test_rejects_invalid_port(self, port):
        with pytest.raises(ValidationError):
            device_adapter.validate_python(BASE | {
                "device_type": "switch", "configured_services": [{"protocol": "ssh", "port": port}],
            })

    def test_rejects_duplicate_vulnerability_ids(self):
        vuln = {"id": "ccv-2026-0001", "title": "Fictional issue", "severity": "low"}
        with pytest.raises(ValidationError, match="unique"):
            device_adapter.validate_python(BASE | {"device_type": "switch", "vulnerabilities": [vuln, vuln]})

    def test_offers_returns_configured_service(self):
        device = server("web-1")
        assert device.offers("https").port == 443
        assert device.offers("sql") is None

    def test_is_immutable(self):
        with pytest.raises(ValidationError):
            server("web-1").status = "offline"


class TestPatchStatus:
    def test_current_must_be_recent(self):
        with pytest.raises(ValidationError):
            PatchStatus(level="current", days_since_patch=45)

    def test_behind_must_be_old(self):
        with pytest.raises(ValidationError):
            PatchStatus(level="behind", days_since_patch=5)

    def test_unsupported_accepts_any_age(self):
        assert PatchStatus(level="unsupported", days_since_patch=5).level == "unsupported"


class TestNetworkConnection:
    def make(self, **overrides):
        fields = {"id": "link-a-b", "source_id": "node-a", "target_id": "node-b",
                  "link_type": "ethernet", "bandwidth_mbps": 1000}
        return NetworkConnection(**(fields | overrides))

    def test_defaults(self):
        conn = self.make()
        assert conn.traffic_permitted is True
        assert conn.latency_ms == 1.0

    def test_rejects_self_loop(self):
        with pytest.raises(ValidationError, match="itself"):
            self.make(target_id="node-a")

    @pytest.mark.parametrize("overrides", [{"bandwidth_mbps": 0}, {"bandwidth_mbps": 100_001}, {"latency_ms": -1}])
    def test_rejects_invalid_properties(self, overrides):
        with pytest.raises(ValidationError):
            self.make(**overrides)

    def test_other_end(self):
        assert self.make().other_end("node-a") == "node-b"


class TestPolicyModels:
    def test_rule_rejects_negative_priority(self):
        with pytest.raises(ValidationError):
            PolicyRule(id="r-1", priority=-1, action="allow")

    def test_rule_rejects_unknown_protocol(self):
        with pytest.raises(ValidationError):
            PolicyRule(id="r-1", priority=1, action="allow", protocols=["telnet"])

    def test_policy_rejects_duplicate_rule_ids(self):
        r = PolicyRule(id="r-1", priority=1, action="allow")
        with pytest.raises(ValidationError, match="unique"):
            AccessPolicy(rules=(r, r))


class TestCityService:
    def make(self, *deps):
        return CityService(id="svc-x", name="X", organization_id="org-x", criticality="high",
                           entry_point_id="web-1", dependencies=deps)

    def test_dependency_cannot_be_its_own_client(self):
        with pytest.raises(ValidationError, match="itself"):
            self.make(ServiceDependency(device_id="web-1", protocol="sql", role="db"))

    def test_rejects_duplicate_dependency(self):
        dep = ServiceDependency(device_id="db-1", protocol="sql", role="db")
        with pytest.raises(ValidationError, match="Duplicate"):
            self.make(dep, dep)

    def test_device_ids_include_entry_clients_and_dependencies(self):
        service = self.make(
            ServiceDependency(device_id="app-1", protocol="https", role="app"),
            ServiceDependency(device_id="db-1", protocol="sql", role="db", client_id="app-1"),
        )
        assert service.device_ids() == ("app-1", "db-1", "web-1")


class TestOtherModels:
    def test_security_event_rejects_negative_tick(self):
        with pytest.raises(ValidationError):
            SecurityEvent(id="evt-0001", tick=-1, severity="low", category="malware", device_id="web-1", summary="x")

    @pytest.mark.parametrize(
        "overrides",
        [{"seed": -1}, {"seed": 2**32}, {"tick_minutes": 0}, {"starting_budget": -5},
         {"difficulty": "impossible"}, {"city_name": "   "}],
    )
    def test_config_rejects_invalid_values(self, overrides):
        with pytest.raises(ValidationError):
            SimulationConfig(**overrides)
