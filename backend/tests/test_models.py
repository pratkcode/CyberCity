import pytest
from pydantic import ValidationError

from app.models import (
    CityService,
    Criticality,
    DeviceType,
    LinkType,
    NetworkConnection,
    NetworkDevice,
    SecurityEvent,
    SimulationConfig,
)


def make_device(**overrides):
    fields = {
        "id": "test-server-01",
        "name": "Test Server",
        "device_type": DeviceType.SERVER,
        "zone": "test-lan",
        "criticality": Criticality.MEDIUM,
    }
    return NetworkDevice(**(fields | overrides))


def make_connection(**overrides):
    fields = {
        "id": "link-a-b",
        "source_id": "node-a",
        "target_id": "node-b",
        "link_type": LinkType.ETHERNET,
        "bandwidth_mbps": 1000,
    }
    return NetworkConnection(**(fields | overrides))


class TestNetworkDevice:
    def test_valid_device(self):
        device = make_device()
        assert device.online is True
        assert device.patch_age_days == 0

    @pytest.mark.parametrize(
        "bad_id",
        ["", "a", "Has-Upper", "under_score", "-leading", "trailing-", "double--dash", "1starts-digit", "x" * 49],
    )
    def test_rejects_invalid_identifiers(self, bad_id):
        with pytest.raises(ValidationError):
            make_device(id=bad_id)

    def test_rejects_unknown_device_type(self):
        with pytest.raises(ValidationError):
            make_device(device_type="mainframe")

    def test_rejects_unknown_fields(self):
        with pytest.raises(ValidationError):
            make_device(ip_address="10.0.0.1")

    @pytest.mark.parametrize("patch_age", [-1, 366])
    def test_rejects_out_of_range_patch_age(self, patch_age):
        with pytest.raises(ValidationError):
            make_device(patch_age_days=patch_age)

    def test_is_immutable(self):
        device = make_device()
        with pytest.raises(ValidationError):
            device.online = False


class TestNetworkConnection:
    def test_valid_connection(self):
        assert make_connection().encrypted is False

    def test_rejects_self_loop(self):
        with pytest.raises(ValidationError, match="itself"):
            make_connection(target_id="node-a")

    @pytest.mark.parametrize("bandwidth", [0, -10, 100_001])
    def test_rejects_invalid_bandwidth(self, bandwidth):
        with pytest.raises(ValidationError):
            make_connection(bandwidth_mbps=bandwidth)


class TestCityService:
    def test_requires_at_least_one_dependency(self):
        with pytest.raises(ValidationError):
            CityService(id="svc-x", name="X", sector="cloud", dependency_ids=())

    def test_rejects_duplicate_dependencies(self):
        with pytest.raises(ValidationError, match="duplicates"):
            CityService(id="svc-x", name="X", sector="cloud", dependency_ids=("dev-a", "dev-a"))


class TestSecurityEvent:
    def test_valid_event(self):
        event = SecurityEvent(
            id="evt-0001",
            tick=3,
            severity="high",
            category="authentication",
            device_id="hosp-ws-01",
            summary="Repeated failed logins (simulated).",
        )
        assert event.severity == "high"

    def test_rejects_negative_tick(self):
        with pytest.raises(ValidationError):
            SecurityEvent(
                id="evt-0001", tick=-1, severity="low", category="malware",
                device_id="hosp-ws-01", summary="x",
            )


class TestSimulationConfig:
    def test_defaults_are_valid(self):
        config = SimulationConfig()
        assert config.seed == 1337

    @pytest.mark.parametrize(
        "overrides",
        [
            {"seed": -1},
            {"seed": 2**32},
            {"tick_minutes": 0},
            {"starting_budget": -5},
            {"difficulty": "impossible"},
            {"city_name": "   "},
        ],
    )
    def test_rejects_invalid_values(self, overrides):
        with pytest.raises(ValidationError):
            SimulationConfig(**overrides)
