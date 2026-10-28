"""Simulation configuration and snapshot models."""

from enum import StrEnum

from pydantic import Field

from app.models.city import CityService
from app.models.common import DisplayName, StrictModel
from app.models.network import NetworkConnection, NetworkDevice

MAX_SEED = 2**32 - 1


class Difficulty(StrEnum):
    TRAINING = "training"
    STANDARD = "standard"
    CHALLENGING = "challenging"


class SimulationConfig(StrictModel):
    """Inputs that fully determine a new simulation's initial state."""

    seed: int = Field(default=1337, ge=0, le=MAX_SEED)
    city_name: DisplayName = "CyberCity"
    difficulty: Difficulty = Difficulty.STANDARD
    starting_budget: int = Field(default=250_000, ge=0, le=10_000_000)
    tick_minutes: int = Field(
        default=15, ge=1, le=240, description="Simulated minutes per tick."
    )


class NetworkSnapshot(StrictModel):
    """Serializable view of the network, for the frontend map."""

    devices: tuple[NetworkDevice, ...]
    connections: tuple[NetworkConnection, ...]


class SimulationSummary(StrictModel):
    """Top-level state returned after creating or fetching a simulation."""

    config: SimulationConfig
    tick: int = Field(ge=0)
    simulated_minutes: int = Field(ge=0)
    device_count: int = Field(ge=0)
    connection_count: int = Field(ge=0)
    services: tuple[CityService, ...]
