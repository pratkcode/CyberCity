"""Simulation state and deterministic initialization.

Determinism rule: every random choice must come from ``SimulationState.rng``,
which is seeded only from ``SimulationConfig.seed``. Never use the global
``random`` module, wall-clock time, or unordered iteration (e.g. over sets)
when making a random choice.
"""

import random
from dataclasses import dataclass, field

from app.models import (
    AccessPolicy,
    CityDefinition,
    CityService,
    Difficulty,
    NetworkDevice,
    Organization,
    PatchLevel,
    PatchStatus,
    SimulationConfig,
    ValidationReport,
)
from app.models.devices import CURRENT_PATCH_WINDOW_DAYS
from app.simulation.network_manager import NetworkManager
from app.simulation.sample_city import sample_city_definition
from app.simulation.validation import validate_city

# Harder settings start with devices that have gone longer without patches.
MAX_INITIAL_PATCH_AGE_DAYS: dict[Difficulty, int] = {
    Difficulty.TRAINING: 30,
    Difficulty.STANDARD: 90,
    Difficulty.CHALLENGING: 180,
}


class CityValidationError(ValueError):
    """The city definition has errors and cannot start a simulation."""

    def __init__(self, report: ValidationReport) -> None:
        first = next(i.message for i in report.issues if i.severity == "error")
        super().__init__(f"City definition is invalid ({report.error_count} error(s)). First: {first}")
        self.report = report


@dataclass
class SimulationState:
    config: SimulationConfig
    network: NetworkManager
    policy: AccessPolicy
    organizations: tuple[Organization, ...]
    services: tuple[CityService, ...]
    rng: random.Random = field(repr=False)
    tick: int = 0

    @property
    def simulated_minutes(self) -> int:
        return self.tick * self.config.tick_minutes

    def definition(self) -> CityDefinition:
        """The current city as a definition, e.g. for re-validation."""
        return CityDefinition(
            zones=self.network.zones(),
            devices=self.network.devices(),
            connections=self.network.connections(),
            policy=self.policy,
            organizations=self.organizations,
            services=self.services,
        )


def initialize_simulation(
    config: SimulationConfig, city: CityDefinition | None = None
) -> SimulationState:
    """Validate a city (the sample city by default) and build a seeded simulation from it."""
    city = city or sample_city_definition()
    rng = random.Random(config.seed)
    devices = _seed_patch_status(city.devices, rng, MAX_INITIAL_PATCH_AGE_DAYS[config.difficulty])
    city = city.model_copy(update={"devices": devices})

    report = validate_city(city)
    if not report.valid:
        raise CityValidationError(report)

    return SimulationState(
        config=config,
        network=NetworkManager.build(city.zones, city.devices, city.connections),
        policy=city.policy,
        organizations=city.organizations,
        services=city.services,
        rng=rng,
    )


def _seed_patch_status(
    devices: tuple[NetworkDevice, ...], rng: random.Random, max_days: int
) -> tuple[NetworkDevice, ...]:
    # Sorted so the sequence of rng draws doesn't depend on definition order.
    seeded = []
    for device in sorted(devices, key=lambda d: d.id):
        days = rng.randint(0, max_days)
        if device.patch.level is PatchLevel.UNSUPPORTED:
            level = PatchLevel.UNSUPPORTED
        else:
            level = PatchLevel.CURRENT if days <= CURRENT_PATCH_WINDOW_DAYS else PatchLevel.BEHIND
        patch = PatchStatus(level=level, days_since_patch=days)
        seeded.append(device.model_copy(update={"patch": patch}))
    return tuple(seeded)
