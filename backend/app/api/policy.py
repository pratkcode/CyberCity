"""Routes for the zone access policy."""

from fastapi import APIRouter

from app.api.dependencies import SimulationServiceDep
from app.api.params import SourceIdQuery, TargetIdQuery
from app.models import AccessPolicy, ConnectionCheck, Protocol

router = APIRouter(prefix="/policy", tags=["policy"])


@router.get("/rules", response_model=AccessPolicy, summary="Rules in evaluation order.")
def list_rules(service: SimulationServiceDep) -> AccessPolicy:
    return service.policy()


@router.get(
    "/check",
    response_model=ConnectionCheck,
    summary="Would simulated traffic from source to target be permitted?",
)
def check_access(
    source: SourceIdQuery,
    target: TargetIdQuery,
    protocol: Protocol,
    service: SimulationServiceDep,
) -> ConnectionCheck:
    return service.check_access(source, target, protocol)
