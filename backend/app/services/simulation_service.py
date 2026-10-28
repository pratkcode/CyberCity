"""Application service that owns the active simulation.

The API routes call this class and never touch NetworkX or the simulation
internals directly. State is held in memory for Phase 1. A later phase can
swap in SQLite persistence behind the same methods.
"""

from threading import Lock

from app.models import (
    CityService,
    NetworkDevice,
    NetworkSnapshot,
    SimulationConfig,
    SimulationSummary,
)
from app.services.errors import InvalidTopologyError, NotFoundError
from app.simulation.network import TopologyError
from app.simulation.state import SimulationState, initialize_simulation


class SimulationService:
    def __init__(self, config: SimulationConfig | None = None) -> None:
        self._lock = Lock()
        self._state = self._initialize(config or SimulationConfig())

    def reset(self, config: SimulationConfig) -> SimulationSummary:
        state = self._initialize(config)
        with self._lock:
            self._state = state
        return self.summary()

    def summary(self) -> SimulationSummary:
        state = self._state
        return SimulationSummary(
            config=state.config,
            tick=state.tick,
            simulated_minutes=state.simulated_minutes,
            device_count=state.graph.number_of_nodes(),
            connection_count=state.graph.number_of_edges(),
            services=state.services,
        )

    def network(self) -> NetworkSnapshot:
        return self._state.snapshot()

    def get_device(self, device_id: str) -> NetworkDevice:
        graph = self._state.graph
        if device_id not in graph:
            raise NotFoundError(f"Device '{device_id}' does not exist in this simulation.")
        return graph.nodes[device_id]["device"]

    def services(self) -> tuple[CityService, ...]:
        return self._state.services

    @staticmethod
    def _initialize(config: SimulationConfig) -> SimulationState:
        try:
            return initialize_simulation(config)
        except TopologyError as exc:
            raise InvalidTopologyError(str(exc)) from exc
