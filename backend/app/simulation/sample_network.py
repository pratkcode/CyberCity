"""A small, entirely fictional city network used as the Phase 1 sample.

All names are invented. There are no IP addresses or hostnames here on
purpose: the simulator never needs to resolve or contact anything real.
"""

from app.models import (
    CityService,
    Criticality as C,
    DeviceType as D,
    LinkType as L,
    NetworkConnection,
    NetworkDevice,
    Sector,
)


def _device(id: str, name: str, kind: D, zone: str, criticality: C) -> NetworkDevice:
    return NetworkDevice(id=id, name=name, device_type=kind, zone=zone, criticality=criticality)


SAMPLE_DEVICES: tuple[NetworkDevice, ...] = (
    _device("edge-router-01", "City Edge Router", D.ROUTER, "internet-edge", C.CRITICAL),
    _device("edge-fw-01", "Perimeter Firewall", D.FIREWALL, "internet-edge", C.CRITICAL),
    _device("core-switch-01", "Municipal Core Switch", D.SWITCH, "city-core", C.HIGH),
    _device("hosp-fw-01", "St. Aurelia Hospital Firewall", D.FIREWALL, "hospital-lan", C.HIGH),
    _device("hosp-ehr-db-01", "St. Aurelia Patient Records DB", D.DATABASE, "hospital-lan", C.CRITICAL),
    _device("hosp-ws-01", "Ward 3 Nurse Station", D.WORKSTATION, "hospital-lan", C.MEDIUM),
    _device("bank-app-01", "Harbor Trust Payments Server", D.SERVER, "bank-lan", C.CRITICAL),
    _device("bank-db-01", "Harbor Trust Ledger DB", D.DATABASE, "bank-lan", C.CRITICAL),
    _device("grid-hmi-01", "Grid Operator Console", D.WORKSTATION, "grid-ot", C.HIGH),
    _device("grid-scada-01", "Substation 4 Controller", D.IOT_CONTROLLER, "grid-ot", C.CRITICAL),
    _device("gov-portal-01", "City Permits Portal", D.SERVER, "gov-lan", C.HIGH),
    _device("biz-pos-01", "Market Street Retail Terminal", D.WORKSTATION, "business-lan", C.LOW),
    _device("cloud-gw-01", "Metro Cloud Gateway", D.CLOUD_GATEWAY, "cloud-dmz", C.HIGH),
    _device("cloud-app-01", "Shared Hosting Node", D.SERVER, "cloud-dmz", C.MEDIUM),
)


def _link(
    id: str, source: str, target: str, kind: L, mbps: int, encrypted: bool = False
) -> NetworkConnection:
    return NetworkConnection(
        id=id,
        source_id=source,
        target_id=target,
        link_type=kind,
        bandwidth_mbps=mbps,
        encrypted=encrypted,
    )


SAMPLE_CONNECTIONS: tuple[NetworkConnection, ...] = (
    _link("link-edge-fw", "edge-router-01", "edge-fw-01", L.FIBER, 10_000),
    _link("link-fw-core", "edge-fw-01", "core-switch-01", L.FIBER, 10_000),
    _link("link-core-hosp", "core-switch-01", "hosp-fw-01", L.FIBER, 1_000),
    _link("link-hosp-db", "hosp-fw-01", "hosp-ehr-db-01", L.ETHERNET, 1_000),
    _link("link-hosp-ws", "hosp-fw-01", "hosp-ws-01", L.ETHERNET, 1_000),
    _link("link-core-bank", "core-switch-01", "bank-app-01", L.FIBER, 1_000, encrypted=True),
    _link("link-bank-db", "bank-app-01", "bank-db-01", L.ETHERNET, 1_000, encrypted=True),
    _link("link-core-grid", "core-switch-01", "grid-hmi-01", L.VPN, 100, encrypted=True),
    _link("link-grid-scada", "grid-hmi-01", "grid-scada-01", L.ETHERNET, 100),
    _link("link-core-gov", "core-switch-01", "gov-portal-01", L.ETHERNET, 1_000),
    _link("link-core-biz", "core-switch-01", "biz-pos-01", L.WIRELESS, 300),
    _link("link-fw-cloud", "edge-fw-01", "cloud-gw-01", L.VPN, 1_000, encrypted=True),
    _link("link-cloud-app", "cloud-gw-01", "cloud-app-01", L.ETHERNET, 10_000),
    _link("link-cloud-gov", "cloud-gw-01", "gov-portal-01", L.VPN, 500, encrypted=True),
)


SAMPLE_SERVICES: tuple[CityService, ...] = (
    CityService(
        id="svc-hospital-records",
        name="Hospital Patient Records",
        sector=Sector.HEALTHCARE,
        dependency_ids=("hosp-ehr-db-01", "hosp-fw-01"),
    ),
    CityService(
        id="svc-payments",
        name="Retail Banking Payments",
        sector=Sector.FINANCE,
        dependency_ids=("bank-app-01", "bank-db-01"),
    ),
    CityService(
        id="svc-power-grid",
        name="Eastside Power Distribution",
        sector=Sector.ENERGY,
        dependency_ids=("grid-scada-01", "grid-hmi-01"),
    ),
    CityService(
        id="svc-permits",
        name="Online Permits & Licensing",
        sector=Sector.GOVERNMENT,
        dependency_ids=("gov-portal-01", "cloud-gw-01"),
    ),
    CityService(
        id="svc-retail",
        name="Market Street Commerce",
        sector=Sector.BUSINESS,
        dependency_ids=("biz-pos-01",),
    ),
    CityService(
        id="svc-cloud-hosting",
        name="Metro Cloud Hosting",
        sector=Sector.CLOUD,
        dependency_ids=("cloud-gw-01", "cloud-app-01"),
    ),
)
