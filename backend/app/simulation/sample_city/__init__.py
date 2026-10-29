"""The fictional sample city used when no other city definition is supplied."""

from app.models import CityDefinition
from app.simulation.sample_city.devices import SAMPLE_DEVICES
from app.simulation.sample_city.policy import SAMPLE_POLICY
from app.simulation.sample_city.services import SAMPLE_ORGANIZATIONS, SAMPLE_SERVICES
from app.simulation.sample_city.topology import SAMPLE_CONNECTIONS, SAMPLE_ZONES


def sample_city_definition() -> CityDefinition:
    return CityDefinition(
        zones=SAMPLE_ZONES,
        devices=SAMPLE_DEVICES,
        connections=SAMPLE_CONNECTIONS,
        policy=SAMPLE_POLICY,
        organizations=SAMPLE_ORGANIZATIONS,
        services=SAMPLE_SERVICES,
    )
