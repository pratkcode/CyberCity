"""Read-only routes for the modeled network topology."""

from fastapi import APIRouter

from app.api.dependencies import SimulationServiceDep
from app.api.params import DeviceIdPath, SourceIdQuery, TargetIdQuery
from app.models import DeviceDetail, PathMetric, PathResult, Topology, ValidationReport, ZoneSummary

router = APIRouter(prefix="/network", tags=["network"])


@router.get("", response_model=Topology, summary="Complete topology: zones, devices, links, segments.")
def get_topology(service: SimulationServiceDep) -> Topology:
    return service.topology()


@router.get("/zones", response_model=list[ZoneSummary])
def list_zones(service: SimulationServiceDep) -> list[ZoneSummary]:
    return service.zones()


@router.get("/devices/{device_id}", response_model=DeviceDetail)
def get_device(device_id: DeviceIdPath, service: SimulationServiceDep) -> DeviceDetail:
    return service.device_detail(device_id)


@router.get(
    "/path",
    response_model=PathResult,
    summary="Shortest usable path between two devices.",
    description="Returns 200 with `found: false` when no path exists; 404 if a device is unknown.",
)
def find_path(
    source: SourceIdQuery,
    target: TargetIdQuery,
    service: SimulationServiceDep,
    metric: PathMetric = PathMetric.HOPS,
) -> PathResult:
    return service.find_path(source, target, metric)


@router.get("/validation", response_model=ValidationReport)
def validate_network(service: SimulationServiceDep) -> ValidationReport:
    return service.validation()
