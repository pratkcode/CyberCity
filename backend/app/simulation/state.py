"""Simulation state and deterministic initialization.

Determinism rule: every random choice must come from ``SimulationState.rng``,
which is seeded only from ``SimulationConfig.seed``. Never use the global
``random`` module, wall-clock time, or unordered iteration (e.g. over sets)
when making a random choice. Following this rule means the same seed and
config always produce the same simulation.
"""

import random
from dataclasses import dataclass, field

import networkx as nx

from app.models import CityService, Difficulty, NetworkSnapshot, SimulationConfig
from app.simulation.network import (
    build_network_graph,
    snapshot_from_graph,
    validate_service_dependencies,
)
from app.simulation.sample_network import (
    SAMPLE_CONNECTIONS,
    SAMPLE_DEVICES,
    SAMPLE_SERVICES,
)

# Harder settings start with devices that have gone longer without patches.
MAX_INITIAL_PATCH_AGE_DAYS: dict[Difficulty, int] = {
    Difficulty.TRAINING: 30,
    Difficulty.STANDARD: 90,
    Difficulty.CHALLENGING: 180,
}


@dataclass
class SimulationState:
    config: SimulationConfig
    graph: nx.Graph
    services: tuple[CityService, ...]
    rng: random.Random = field(repr=False)
    tick: int = 0

    @property
    def simulated_minutes(self) -> int:
        return self.tick * self.config.tick_minutes

    def snapshot(self) -> NetworkSnapshot:
        return snapshot_from_graph(self.graph)


def initialize_simulation(config: SimulationConfig) -> SimulationState:
    """Create a new simulation from the fictional sample network."""
    rng = random.Random(config.seed)
    graph = build_network_graph(SAMPLE_DEVICES, SAMPLE_CONNECTIONS)
    validate_service_dependencies(SAMPLE_SERVICES, graph)

    _seed_patch_ages(graph, rng, MAX_INITIAL_PATCH_AGE_DAYS[config.difficulty])

    return SimulationState(config=config, graph=graph, services=SAMPLE_SERVICES, rng=rng)


def _seed_patch_ages(graph: nx.Graph, rng: random.Random, max_days: int) -> None:
    # sorted() keeps the order of rng draws independent of graph insertion order.
    for node_id in sorted(graph.nodes):
        device = graph.nodes[node_id]["device"]
        graph.nodes[node_id]["device"] = device.model_copy(
            update={"patch_age_days": rng.randint(0, max_days)}
        )
