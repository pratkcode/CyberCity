import networkx as nx
import pytest

from app.models import DeviceType, LinkType, NetworkConnection
from app.simulation.network import TopologyError, build_network_graph
from app.simulation.sample_network import SAMPLE_CONNECTIONS, SAMPLE_DEVICES, SAMPLE_SERVICES
from app.simulation.state import initialize_simulation
from app.models import SimulationConfig


def test_sample_network_builds_a_connected_graph():
    graph = build_network_graph(SAMPLE_DEVICES, SAMPLE_CONNECTIONS)

    assert graph.number_of_nodes() == len(SAMPLE_DEVICES)
    assert graph.number_of_edges() == len(SAMPLE_CONNECTIONS)
    assert nx.is_connected(graph)


def test_sample_network_has_several_device_types():
    kinds = {d.device_type for d in SAMPLE_DEVICES}
    assert len(kinds) >= 5
    assert {DeviceType.FIREWALL, DeviceType.ROUTER, DeviceType.DATABASE} <= kinds


def test_every_service_dependency_exists():
    state = initialize_simulation(SimulationConfig())
    for service in SAMPLE_SERVICES:
        for device_id in service.dependency_ids:
            assert device_id in state.graph


def test_unknown_endpoint_is_rejected():
    bad = NetworkConnection(
        id="link-bad", source_id="edge-router-01", target_id="ghost-device",
        link_type=LinkType.FIBER, bandwidth_mbps=10,
    )
    with pytest.raises(TopologyError, match="ghost-device"):
        build_network_graph(SAMPLE_DEVICES, (*SAMPLE_CONNECTIONS, bad))


def test_duplicate_device_ids_are_rejected():
    with pytest.raises(TopologyError, match="Duplicate device"):
        build_network_graph((*SAMPLE_DEVICES, SAMPLE_DEVICES[0]), SAMPLE_CONNECTIONS)


def test_parallel_links_are_rejected():
    original = SAMPLE_CONNECTIONS[0]
    reversed_copy = original.model_copy(
        update={"id": "link-dup", "source_id": original.target_id, "target_id": original.source_id}
    )
    with pytest.raises(TopologyError, match="duplicates"):
        build_network_graph(SAMPLE_DEVICES, (*SAMPLE_CONNECTIONS, reversed_copy))


def test_network_endpoint_returns_sample(client):
    body = client.get("/api/network").json()

    assert len(body["devices"]) == len(SAMPLE_DEVICES)
    assert len(body["connections"]) == len(SAMPLE_CONNECTIONS)


def test_get_device_by_id(client):
    response = client.get("/api/network/devices/hosp-ehr-db-01")

    assert response.status_code == 200
    assert response.json()["device_type"] == "database"


def test_get_unknown_device_returns_404(client):
    response = client.get("/api/network/devices/no-such-device")

    assert response.status_code == 404
    assert response.json()["error"]["code"] == "not_found"


def test_malformed_device_id_returns_422(client):
    response = client.get("/api/network/devices/BAD_ID")

    assert response.status_code == 422
    error = response.json()["error"]
    assert error["code"] == "validation_error"
    assert error["details"][0]["location"] == ["path", "device_id"]


def test_create_simulation_rejects_invalid_config(client):
    response = client.post("/api/simulation", json={"seed": -4, "surprise": True})

    assert response.status_code == 422
    fields = {tuple(d["location"]) for d in response.json()["error"]["details"]}
    assert ("body", "seed") in fields
    assert ("body", "surprise") in fields
