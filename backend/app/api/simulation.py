"""Routes for starting and inspecting the simulation itself."""

from fastapi import APIRouter, status

from app.api.dependencies import SimulationServiceDep
from app.models import SimulationConfig, SimulationSummary

router = APIRouter(tags=["simulation"])


@router.get("/simulation", response_model=SimulationSummary)
def get_simulation(service: SimulationServiceDep) -> SimulationSummary:
    return service.summary()


@router.post(
    "/simulation",
    response_model=SimulationSummary,
    status_code=status.HTTP_201_CREATED,
    summary="Start a new simulation from a configuration (replaces the current one).",
)
def create_simulation(config: SimulationConfig, service: SimulationServiceDep) -> SimulationSummary:
    return service.reset(config)
