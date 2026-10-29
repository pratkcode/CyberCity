"""Application service that owns the active simulation.

API routes call this class and never touch NetworkX or simulation internals
directly. State lives in memory on the FastAPI app instance (no module-level
globals). A later phase can add SQLite persistence behind these methods.
"""

from collections.abc import Iterator
from contextlib import contextmanager
from threading import Lock

from app.models import (
    AccessPolicy,
    CityDefinition,
    ConnectionCheck,
    DeviceDetail,
    DeviceLink,
    Organization,
    PathMetric,
    PathResult,
    Protocol,
    ServiceOverview,
    SimulationConfig,
    SimulationSummary,
    Topology,
    ValidationReport,
    ZoneSummary,
)
from app.services.errors import InvalidTopologyError, NotFoundError
from app.simulation.connectivity import check_connection
from app.simulation.errors import UnknownDeviceError, UnknownZoneError
from app.simulation.policy import evaluation_order
from app.simulation.service_health import evaluate_service_health
from app.simulation.state import CityValidationError, SimulationState, initialize_simulation
from app.simulation.validation import validate_city


@contextmanager
def _translate_lookup_errors() -> Iterator[None]:
    try:
        yield
    except (UnknownDeviceError, UnknownZoneError) as exc:
        raise NotFoundError(str(exc)) from exc


class SimulationService:
    def __init__(
        self, config: SimulationConfig | None = None, city: CityDefinition | None = None
    ) -> None:
        self._lock = Lock()
        self._city = city
        self._state = self._initialize(config or SimulationConfig())

    # ------------------------------------------------------------ simulation
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
            zone_count=len(state.network.zones()),
            device_count=len(state.network.devices()),
            connection_count=len(state.network.connections()),
            organization_count=len(state.organizations),
            service_count=len(state.services),
        )

    # --------------------------------------------------------------- network
    def topology(self) -> Topology:
        network = self._state.network
        return Topology(
            zones=network.zones(),
            devices=network.devices(),
            connections=network.connections(),
            segments=network.segments(),
            isolated_device_ids=network.isolated_device_ids(),
        )

    def zones(self) -> list[ZoneSummary]:
        network = self._state.network
        summaries = []
        for zone in network.zones():
            devices = network.devices_in_zone(zone.id)
            summaries.append(
                ZoneSummary(
                    zone=zone,
                    device_ids=tuple(d.id for d in devices),
                    operational_device_count=sum(d.is_operational for d in devices),
                )
            )
        return summaries

    def device_detail(self, device_id: str) -> DeviceDetail:
        state = self._state
        network = state.network
        with _translate_lookup_errors():
            device = network.get_device(device_id)
            links = tuple(
                DeviceLink(connection=c, neighbor_id=c.other_end(device_id))
                for c in network.connections_of(device_id)
            )
            return DeviceDetail(
                device=device,
                zone=network.get_zone(device.zone_id),
                links=links,
                reachable_device_ids=network.reachable_from(device_id),
                isolated=device_id in network.isolated_device_ids(),
                dependent_service_ids=tuple(
                    s.id for s in state.services if device_id in s.device_ids()
                ),
            )

    def find_path(self, source_id: str, target_id: str, metric: PathMetric) -> PathResult:
        with _translate_lookup_errors():
            return self._state.network.find_path(source_id, target_id, metric)

    def validation(self) -> ValidationReport:
        return validate_city(self._state.definition())

    # ---------------------------------------------------------------- policy
    def policy(self) -> AccessPolicy:
        """Rules in the order they are evaluated."""
        return AccessPolicy(rules=evaluation_order(self._state.policy))

    def check_access(self, source_id: str, destination_id: str, protocol: Protocol) -> ConnectionCheck:
        state = self._state
        with _translate_lookup_errors():
            return check_connection(state.network, state.policy, source_id, destination_id, protocol)

    # ------------------------------------------------------------------ city
    def organizations(self) -> tuple[Organization, ...]:
        return self._state.organizations

    def services_overview(self) -> list[ServiceOverview]:
        state = self._state
        return [self._overview(state, s.id) for s in state.services]

    def service_overview(self, service_id: str) -> ServiceOverview:
        return self._overview(self._state, service_id)

    # ------------------------------------------------------------- internals
    @staticmethod
    def _overview(state: SimulationState, service_id: str) -> ServiceOverview:
        service = next((s for s in state.services if s.id == service_id), None)
        if service is None:
            raise NotFoundError(f"Service '{service_id}' does not exist.")
        organization = next(o for o in state.organizations if o.id == service.organization_id)
        return ServiceOverview(
            service=service,
            organization=organization,
            health=evaluate_service_health(service, state.network, state.policy),
        )

    def _initialize(self, config: SimulationConfig) -> SimulationState:
        try:
            return initialize_simulation(config, self._city)
        except CityValidationError as exc:
            details = [i.model_dump(mode="json") for i in exc.report.issues if i.severity == "error"]
            raise InvalidTopologyError(str(exc), details) from exc
