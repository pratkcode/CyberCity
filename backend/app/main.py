"""FastAPI entry point.

Run with:  uvicorn app.main:app --reload   (from the backend/ directory)
"""

import os

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import __version__
from app.api import city, health, network, policy, simulation
from app.api.errors import register_error_handlers
from app.models import CityDefinition, SimulationConfig
from app.services.simulation_service import SimulationService

API_PREFIX = "/api"
DEFAULT_CORS_ORIGINS = "http://localhost:5173,http://127.0.0.1:5173"


def create_app(
    config: SimulationConfig | None = None, city_definition: CityDefinition | None = None
) -> FastAPI:
    """App factory. Tests call this to get a fresh, isolated app (optionally with a small city)."""
    app = FastAPI(
        title="CyberCity Simulation API",
        version=__version__,
        description="Fictional cybersecurity strategy simulator. No real networks are contacted.",
    )
    app.state.simulation_service = SimulationService(config, city_definition)

    # The Vite dev server proxies /api, so CORS is only needed when the
    # frontend calls the API directly (e.g. from a preview build).
    origins = os.environ.get("CYBERCITY_CORS_ORIGINS", DEFAULT_CORS_ORIGINS).split(",")
    app.add_middleware(
        CORSMiddleware,
        allow_origins=[o.strip() for o in origins if o.strip()],
        allow_methods=["GET", "POST"],
        allow_headers=["Content-Type"],
    )

    register_error_handlers(app)
    app.include_router(health.router, prefix=API_PREFIX)
    for module in (simulation, network, policy, city):
        app.include_router(module.router, prefix=API_PREFIX)
    return app


app = create_app()
