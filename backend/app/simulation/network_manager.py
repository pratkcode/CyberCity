"""NetworkManager: the NetworkX-backed topology of the modeled city.

Design notes
------------
- One undirected ``nx.Graph``. Nodes hold a ``device`` model and edges hold a
  ``connection`` model. The Pydantic models are the source of truth, and
  NetworkX supplies the graph algorithms.
- Parallel links between the same pair of devices are rejected, which keeps
  the simple ``Graph`` type sufficient.
- **Usable** means traffic can flow: both devices are operational (online or
  degraded) and the link has ``traffic_permitted``. Reachability, paths and
  segments are computed on this usable view. Access policy is *not* applied
  here; that is the job of ``app.simulation.policy``.
- Every query returns results in a stable order (sorted IDs, lexicographic
  tie-breaking between equal-cost paths), so outputs are reproducible
  regardless of the order devices were added in.
"""

from collections.abc import Iterable

import networkx as nx

from app.models import (
    NetworkConnection,
    NetworkDevice,
    NetworkPath,
    NetworkZone,
    PathMetric,
    PathResult,
)
from app.simulation.errors import (
    DuplicateIdentifierError,
    InvalidConnectionError,
    UnknownConnectionError,
    UnknownDeviceError,
    UnknownZoneError,
)


class NetworkManager:
    def __init__(self, zones: Iterable[NetworkZone] = ()) -> None:
        self._graph = nx.Graph()
        self._zones: dict[str, NetworkZone] = {}
        self._edge_by_id: dict[str, tuple[str, str]] = {}
        for zone in zones:
            self.add_zone(zone)

    @classmethod
    def build(
        cls,
        zones: Iterable[NetworkZone],
        devices: Iterable[NetworkDevice],
        connections: Iterable[NetworkConnection],
    ) -> "NetworkManager":
        manager = cls(sorted(zones, key=lambda z: z.id))
        for device in sorted(devices, key=lambda d: d.id):
            manager.add_device(device)
        for connection in sorted(connections, key=lambda c: c.id):
            manager.add_connection(connection)
        return manager

    # ------------------------------------------------------------------ zones
    def add_zone(self, zone: NetworkZone) -> None:
        if zone.id in self._zones:
            raise DuplicateIdentifierError("zone", zone.id)
        self._zones[zone.id] = zone

    def get_zone(self, zone_id: str) -> NetworkZone:
        try:
            return self._zones[zone_id]
        except KeyError:
            raise UnknownZoneError(zone_id) from None

    def zones(self) -> tuple[NetworkZone, ...]:
        return tuple(self._zones[z] for z in sorted(self._zones))

    def devices_in_zone(self, zone_id: str) -> tuple[NetworkDevice, ...]:
        self.get_zone(zone_id)
        return tuple(d for d in self.devices() if d.zone_id == zone_id)

    # ---------------------------------------------------------------- devices
    def add_device(self, device: NetworkDevice) -> None:
        if device.id in self._graph:
            raise DuplicateIdentifierError("device", device.id)
        self.get_zone(device.zone_id)
        self._graph.add_node(device.id, device=device)

    def update_device(self, device: NetworkDevice) -> None:
        """Replace an existing device's model (e.g. a status change), keeping its links."""
        self.get_device(device.id)
        self.get_zone(device.zone_id)
        self._graph.nodes[device.id]["device"] = device

    def remove_device(self, device_id: str) -> tuple[str, ...]:
        """Remove a device and every connection touching it. Returns removed connection IDs."""
        self.get_device(device_id)
        removed = tuple(c.id for c in self.connections_of(device_id))
        for connection_id in removed:
            del self._edge_by_id[connection_id]
        self._graph.remove_node(device_id)
        return removed

    def has_device(self, device_id: str) -> bool:
        return device_id in self._graph

    def get_device(self, device_id: str) -> NetworkDevice:
        if device_id not in self._graph:
            raise UnknownDeviceError(device_id)
        return self._graph.nodes[device_id]["device"]

    def devices(self) -> tuple[NetworkDevice, ...]:
        return tuple(self._graph.nodes[n]["device"] for n in sorted(self._graph.nodes))

    # ------------------------------------------------------------ connections
    def add_connection(self, connection: NetworkConnection) -> None:
        if connection.id in self._edge_by_id:
            raise DuplicateIdentifierError("connection", connection.id)
        for endpoint in (connection.source_id, connection.target_id):
            if endpoint not in self._graph:
                raise UnknownDeviceError(endpoint)
        if self._graph.has_edge(connection.source_id, connection.target_id):
            existing = self._graph.edges[connection.source_id, connection.target_id]["connection"]
            raise InvalidConnectionError(
                f"Connection '{connection.id}' duplicates link '{existing.id}' between "
                f"'{connection.source_id}' and '{connection.target_id}'."
            )
        self._graph.add_edge(connection.source_id, connection.target_id, connection=connection)
        self._edge_by_id[connection.id] = (connection.source_id, connection.target_id)

    def remove_connection(self, connection_id: str) -> NetworkConnection:
        connection = self.get_connection(connection_id)
        self._graph.remove_edge(connection.source_id, connection.target_id)
        del self._edge_by_id[connection_id]
        return connection

    def get_connection(self, connection_id: str) -> NetworkConnection:
        try:
            u, v = self._edge_by_id[connection_id]
        except KeyError:
            raise UnknownConnectionError(connection_id) from None
        return self._graph.edges[u, v]["connection"]

    def connections(self) -> tuple[NetworkConnection, ...]:
        return tuple(self.get_connection(c) for c in sorted(self._edge_by_id))

    def connections_of(self, device_id: str) -> tuple[NetworkConnection, ...]:
        self.get_device(device_id)
        links = (self._graph.edges[device_id, n]["connection"] for n in self._graph.neighbors(device_id))
        return tuple(sorted(links, key=lambda c: c.id))

    # ---------------------------------------------------------------- queries
    def neighbors(self, device_id: str, *, usable_only: bool = False) -> tuple[str, ...]:
        """Directly linked devices. With ``usable_only``, only those traffic can reach now."""
        self.get_device(device_id)
        graph = self._usable_view() if usable_only else self._graph
        if device_id not in graph:
            return ()
        return tuple(sorted(graph.neighbors(device_id)))

    def reachable_from(self, device_id: str) -> tuple[str, ...]:
        """Devices reachable over usable links, excluding the device itself."""
        self.get_device(device_id)
        view = self._usable_view()
        if device_id not in view:
            return ()
        return tuple(sorted(nx.node_connected_component(view, device_id) - {device_id}))

    def find_path(
        self, source_id: str, target_id: str, metric: PathMetric = PathMetric.HOPS
    ) -> PathResult:
        metric = PathMetric(metric)  # also accept the plain string value
        source = self.get_device(source_id)
        target = self.get_device(target_id)

        def not_found(reason: str) -> PathResult:
            return PathResult(
                source_id=source_id, target_id=target_id, metric=metric,
                found=False, path=None, reason=reason,
            )

        for role, device in (("Source", source), ("Target", target)):
            if not device.is_operational:
                return not_found(f"{role} device '{device.id}' is offline.")

        view = self._usable_view()
        weight = None if metric is PathMetric.HOPS else _latency_weight
        try:
            # min() over all equally short paths gives a deterministic tie-break.
            device_ids = min(nx.all_shortest_paths(view, source_id, target_id, weight=weight))
        except nx.NetworkXNoPath:
            return not_found(
                f"No route from '{source_id}' to '{target_id}' over operational devices "
                "and traffic-permitted links."
            )

        path = self._describe_path(device_ids)
        hops = "hop" if path.hop_count == 1 else "hops"
        return PathResult(
            source_id=source_id, target_id=target_id, metric=metric, found=True, path=path,
            reason=f"Shortest path by {metric.value}: {path.hop_count} {hops}, "
            f"{path.total_latency_ms:g} ms total latency.",
        )

    def segments(self) -> tuple[tuple[str, ...], ...]:
        """Connected groups of operational devices over usable links, largest first."""
        groups = (tuple(sorted(c)) for c in nx.connected_components(self._usable_view()))
        return tuple(sorted(groups, key=lambda g: (-len(g), g)))

    def isolated_device_ids(self) -> tuple[str, ...]:
        """Operational devices that are cut off from the primary (largest) segment."""
        segments = self.segments()
        return tuple(sorted(d for seg in segments[1:] for d in seg))

    # -------------------------------------------------------------- internals
    def _usable_view(self) -> nx.Graph:
        nodes = self._graph.nodes
        edges = self._graph.edges
        return nx.subgraph_view(
            self._graph,
            filter_node=lambda n: nodes[n]["device"].is_operational,
            filter_edge=lambda u, v: edges[u, v]["connection"].traffic_permitted,
        )

    def _describe_path(self, device_ids: list[str]) -> NetworkPath:
        links = [self._graph.edges[u, v]["connection"] for u, v in zip(device_ids, device_ids[1:])]
        return NetworkPath(
            device_ids=tuple(device_ids),
            connection_ids=tuple(c.id for c in links),
            hop_count=len(links),
            total_latency_ms=round(sum(c.latency_ms for c in links), 3),
            bottleneck_bandwidth_mbps=min((c.bandwidth_mbps for c in links), default=None),
        )


def _latency_weight(_u: str, _v: str, data: dict) -> float:
    return data["connection"].latency_ms
