"""Build and read the NetworkX graph that represents the city network.

Design notes:
- The graph is undirected (``nx.Graph``) because Phase 1 links are physical or
  logical connections without direction. Traffic rules such as firewall
  policies can be layered on later without changing this module's API.
- Each node stores its ``NetworkDevice`` model and each edge stores its
  ``NetworkConnection``. The Pydantic models remain the source of truth, and
  NetworkX provides graph algorithms (paths, reachability) for later phases.
- Nodes and edges are inserted in sorted order so that iteration order, and
  therefore any seeded randomness applied while iterating, is reproducible.
"""

from collections.abc import Iterable

import networkx as nx

from app.models import CityService, NetworkConnection, NetworkDevice, NetworkSnapshot


class TopologyError(ValueError):
    """Raised when devices, connections or services don't form a valid network."""


def build_network_graph(
    devices: Iterable[NetworkDevice], connections: Iterable[NetworkConnection]
) -> nx.Graph:
    devices = sorted(devices, key=lambda d: d.id)
    connections = sorted(connections, key=lambda c: c.id)

    _ensure_unique((d.id for d in devices), "device")
    _ensure_unique((c.id for c in connections), "connection")

    graph = nx.Graph()
    for device in devices:
        graph.add_node(device.id, device=device)

    for conn in connections:
        missing = [e for e in (conn.source_id, conn.target_id) if e not in graph]
        if missing:
            raise TopologyError(
                f"Connection '{conn.id}' references unknown device(s): {', '.join(missing)}."
            )
        if graph.has_edge(conn.source_id, conn.target_id):
            raise TopologyError(
                f"Connection '{conn.id}' duplicates an existing link between "
                f"'{conn.source_id}' and '{conn.target_id}'."
            )
        graph.add_edge(conn.source_id, conn.target_id, connection=conn)

    return graph


def validate_service_dependencies(services: Iterable[CityService], graph: nx.Graph) -> None:
    services = list(services)
    _ensure_unique((s.id for s in services), "service")
    for service in services:
        missing = [d for d in service.dependency_ids if d not in graph]
        if missing:
            raise TopologyError(
                f"Service '{service.id}' depends on unknown device(s): {', '.join(missing)}."
            )


def snapshot_from_graph(graph: nx.Graph) -> NetworkSnapshot:
    devices = sorted((data["device"] for _, data in graph.nodes(data=True)), key=lambda d: d.id)
    connections = sorted(
        (data["connection"] for _, _, data in graph.edges(data=True)), key=lambda c: c.id
    )
    return NetworkSnapshot(devices=tuple(devices), connections=tuple(connections))


def _ensure_unique(ids: Iterable[str], label: str) -> None:
    seen: set[str] = set()
    for item_id in ids:
        if item_id in seen:
            raise TopologyError(f"Duplicate {label} id '{item_id}'.")
        seen.add(item_id)
