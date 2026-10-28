"""FastAPI dependencies.

The service lives on ``app.state`` rather than in a module-level global, so
each app instance (and each test client) gets isolated state.
"""

from typing import Annotated

from fastapi import Depends, Request

from app.services.simulation_service import SimulationService


def get_simulation_service(request: Request) -> SimulationService:
    return request.app.state.simulation_service


SimulationServiceDep = Annotated[SimulationService, Depends(get_simulation_service)]
