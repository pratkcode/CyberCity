"""Routes for city organizations and their services."""

from fastapi import APIRouter

from app.api.dependencies import SimulationServiceDep
from app.api.params import ServiceIdPath
from app.models import Organization, ServiceOverview

router = APIRouter(prefix="/city", tags=["city"])


@router.get("/organizations", response_model=list[Organization])
def list_organizations(service: SimulationServiceDep) -> list[Organization]:
    return list(service.organizations())


@router.get("/services", response_model=list[ServiceOverview], summary="Services with current health.")
def list_services(service: SimulationServiceDep) -> list[ServiceOverview]:
    return service.services_overview()


@router.get("/services/{service_id}", response_model=ServiceOverview)
def get_service(service_id: ServiceIdPath, service: SimulationServiceDep) -> ServiceOverview:
    return service.service_overview(service_id)
