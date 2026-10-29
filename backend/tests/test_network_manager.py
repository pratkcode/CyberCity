import pytest

from app.models import OperationalStatus
from app.simulation.errors import (
    DuplicateIdentifierError,
    InvalidConnectionError,
    UnknownConnectionError,
    UnknownDeviceError,
    UnknownZoneError,
)
from app.simulation.network_manager import NetworkManager
from tests.factories import DEFAULT_ZONES, ZONE_B, link, network, server, switch

OFFLINE = OperationalStatus.OFFLINE


def diamond():
    """a — b — d and a — c — d. The a–b link is slow (latency 10)."""
    return network(
        [server("a-1"), server("b-1"), server("c-1"), server("d-1")],
        [link("a-1", "b-1", latency=10), link("b-1", "d-1"), link("a-1", "c-1"), link("c-1", "d-1", mbps=100)],
    )


class TestDevices:
    def test_add_and_get_device(self):
        net = NetworkManager(DEFAULT_ZONES)
        net.add_device(server("web-1"))
        assert net.get_device("web-1").name == "Server web-1"
        assert [d.id for d in net.devices()] == ["web-1"]

    def test_add_duplicate_device_fails(self):
        net = network([server("web-1")])
        with pytest.raises(DuplicateIdentifierError):
            net.add_device(server("web-1"))

    def test_add_device_in_unknown_zone_fails(self):
        net = NetworkManager(DEFAULT_ZONES)
        with pytest.raises(UnknownZoneError):
            net.add_device(server("web-1", "zone-missing"))

    def test_remove_device_removes_its_connections(self):
        net = network([server("a-1"), server("b-1"), server("c-1")], [link("a-1", "b-1"), link("b-1", "c-1")])
        removed = net.remove_device("b-1")
        assert removed == ("link-a-1-b-1", "link-b-1-c-1")
        assert not net.has_device("b-1")
        assert net.connections() == ()

    def test_unknown_device_lookups_fail(self):
        net = network([server("a-1")])
        for call in (net.get_device, net.remove_device, net.neighbors, net.reachable_from, net.connections_of):
            with pytest.raises(UnknownDeviceError):
                call("ghost-1")

    def test_update_device_keeps_links(self):
        net = network([server("a-1"), server("b-1")], [link("a-1", "b-1")])
        net.update_device(server("a-1", status=OFFLINE))
        assert net.get_device("a-1").status == OFFLINE
        assert net.neighbors("a-1") == ("b-1",)

    def test_devices_in_zone(self):
        net = network([server("a-1"), server("b-1", ZONE_B)])
        assert [d.id for d in net.devices_in_zone(ZONE_B)] == ["b-1"]


class TestConnections:
    def test_add_and_remove_connection(self):
        net = network([server("a-1"), server("b-1")])
        net.add_connection(link("a-1", "b-1"))
        assert net.neighbors("a-1") == ("b-1",)
        removed = net.remove_connection("link-a-1-b-1")
        assert removed.source_id == "a-1"
        assert net.neighbors("a-1") == ()

    def test_connection_to_unknown_device_fails(self):
        net = network([server("a-1")])
        with pytest.raises(UnknownDeviceError, match="ghost-1"):
            net.add_connection(link("a-1", "ghost-1"))

    def test_duplicate_connection_id_fails(self):
        net = network([server("a-1"), server("b-1"), server("c-1")], [link("a-1", "b-1")])
        clash = link("a-1", "c-1").model_copy(update={"id": "link-a-1-b-1"})
        with pytest.raises(DuplicateIdentifierError):
            net.add_connection(clash)

    def test_parallel_link_fails_in_either_direction(self):
        net = network([server("a-1"), server("b-1")], [link("a-1", "b-1")])
        with pytest.raises(InvalidConnectionError, match="duplicates"):
            net.add_connection(link("b-1", "a-1"))

    def test_remove_unknown_connection_fails(self):
        with pytest.raises(UnknownConnectionError):
            network([server("a-1")]).remove_connection("link-nope")


class TestNeighborsAndReachability:
    def test_neighbors_are_sorted(self):
        net = network([switch("sw-1"), server("c-1"), server("a-1")], [link("sw-1", "c-1"), link("sw-1", "a-1")])
        assert net.neighbors("sw-1") == ("a-1", "c-1")

    def test_usable_neighbors_skip_offline_devices_and_blocked_links(self):
        net = network(
            [switch("sw-1"), server("a-1"), server("b-1", status=OFFLINE), server("c-1")],
            [link("sw-1", "a-1"), link("sw-1", "b-1"), link("sw-1", "c-1", permitted=False)],
        )
        assert net.neighbors("sw-1") == ("a-1", "b-1", "c-1")
        assert net.neighbors("sw-1", usable_only=True) == ("a-1",)

    def test_reachable_crosses_multiple_hops(self):
        net = network([server("a-1"), server("b-1"), server("c-1")], [link("a-1", "b-1"), link("b-1", "c-1")])
        assert net.reachable_from("a-1") == ("b-1", "c-1")

    def test_offline_device_blocks_reachability_through_it(self):
        net = network(
            [server("a-1"), server("b-1", status=OFFLINE), server("c-1")],
            [link("a-1", "b-1"), link("b-1", "c-1")],
        )
        assert net.reachable_from("a-1") == ()

    def test_offline_device_reaches_nothing(self):
        net = network([server("a-1", status=OFFLINE), server("b-1")], [link("a-1", "b-1")])
        assert net.reachable_from("a-1") == ()

    def test_degraded_device_still_passes_traffic(self):
        net = network(
            [server("a-1"), server("b-1", status=OperationalStatus.DEGRADED), server("c-1")],
            [link("a-1", "b-1"), link("b-1", "c-1")],
        )
        assert net.reachable_from("a-1") == ("b-1", "c-1")


class TestPathfinding:
    def test_hop_metric_breaks_ties_lexicographically(self):
        result = diamond().find_path("a-1", "d-1")
        assert result.found
        assert result.path.device_ids == ("a-1", "b-1", "d-1")
        assert result.path.hop_count == 2

    def test_latency_metric_prefers_faster_route(self):
        result = diamond().find_path("a-1", "d-1", metric="latency")
        assert result.path.device_ids == ("a-1", "c-1", "d-1")
        assert result.path.total_latency_ms == 2.0
        assert result.path.bottleneck_bandwidth_mbps == 100
        assert result.path.connection_ids == ("link-a-1-c-1", "link-c-1-d-1")

    def test_path_avoids_blocked_link(self):
        net = diamond()
        net.remove_connection("link-a-1-c-1")
        net.add_connection(link("a-1", "c-1", permitted=False))
        assert net.find_path("a-1", "d-1", metric="latency").path.device_ids == ("a-1", "b-1", "d-1")

    def test_no_path_between_segments(self):
        net = network([server("a-1"), server("b-1")])
        result = net.find_path("a-1", "b-1")
        assert not result.found
        assert result.path is None
        assert "No route" in result.reason

    def test_offline_endpoint_has_no_path(self):
        net = network([server("a-1"), server("b-1", status=OFFLINE)], [link("a-1", "b-1")])
        result = net.find_path("a-1", "b-1")
        assert not result.found
        assert "offline" in result.reason

    def test_path_to_self_is_zero_hops(self):
        result = diamond().find_path("a-1", "a-1")
        assert result.path.hop_count == 0
        assert result.path.bottleneck_bandwidth_mbps is None

    def test_unknown_endpoint_raises(self):
        with pytest.raises(UnknownDeviceError):
            diamond().find_path("a-1", "ghost-1")

    def test_result_is_independent_of_insertion_order(self):
        devices = [server("d-1"), server("c-1"), server("b-1"), server("a-1")]
        links = [link("c-1", "d-1"), link("a-1", "c-1"), link("b-1", "d-1"), link("a-1", "b-1")]
        net = NetworkManager(DEFAULT_ZONES)
        for d in devices:
            net.add_device(d)
        for c in links:
            net.add_connection(c)
        assert net.find_path("a-1", "d-1").path.device_ids == ("a-1", "b-1", "d-1")


class TestSegments:
    def test_single_segment(self):
        net = diamond()
        assert net.segments() == (("a-1", "b-1", "c-1", "d-1"),)
        assert net.isolated_device_ids() == ()

    def test_disconnected_segments_sorted_largest_first(self):
        net = network(
            [server("a-1"), server("b-1"), server("c-1"), server("x-1"), server("y-1"), server("z-1")],
            [link("a-1", "b-1"), link("b-1", "c-1"), link("x-1", "y-1")],
        )
        assert net.segments() == (("a-1", "b-1", "c-1"), ("x-1", "y-1"), ("z-1",))
        assert net.isolated_device_ids() == ("x-1", "y-1", "z-1")

    def test_blocked_link_splits_segment(self):
        net = network([server("a-1"), server("b-1"), server("c-1")], [link("a-1", "b-1"), link("b-1", "c-1", permitted=False)])
        assert net.segments() == (("a-1", "b-1"), ("c-1",))
        assert net.isolated_device_ids() == ("c-1",)

    def test_offline_devices_are_unavailable_not_isolated(self):
        net = network([server("a-1"), server("b-1"), server("c-1", status=OFFLINE)], [link("a-1", "b-1")])
        assert net.segments() == (("a-1", "b-1"),)
        assert net.isolated_device_ids() == ()

    def test_offline_hub_splits_network(self):
        net = network(
            [server("a-1"), switch("sw-1", status=OFFLINE), server("b-1")],
            [link("a-1", "sw-1"), link("sw-1", "b-1")],
        )
        assert net.segments() == (("a-1",), ("b-1",))
        assert net.isolated_device_ids() == ("b-1",)
