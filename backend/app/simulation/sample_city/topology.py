"""Zones and links of the fictional sample city.

Shape: the edge firewall fronts the DMZ and cloud links, and the core router
fans out to every internal zone through that zone's firewall or switch.

Two links are present but carry no traffic (``traffic_permitted=False``):
- passive IDS monitoring taps, which observe but do not route, and
- the Substation 7 controller link, administratively disabled. This makes
  ``grid-plc-02`` an *isolated* device in its own segment.
"""

from app.models import LinkType as L, NetworkConnection, NetworkZone, ZoneKind
from app.simulation.sample_city.devices import CLINICAL, CLOUD, CORP, DATA, GRID, PUBLIC, SOC

SAMPLE_ZONES = (
    NetworkZone(id=PUBLIC, name="Public DMZ", kind=ZoneKind.PUBLIC,
                description="Internet-facing systems behind the perimeter firewall."),
    NetworkZone(id=CORP, name="Corporate & Civic LAN", kind=ZoneKind.INTERNAL,
                description="Shared internal network for city, bank, university and business systems."),
    NetworkZone(id=CLINICAL, name="St. Aurelia Clinical Network", kind=ZoneKind.INTERNAL,
                description="Hospital clinical systems, segmented from the corporate LAN."),
    NetworkZone(id=DATA, name="Restricted Data Zone", kind=ZoneKind.RESTRICTED,
                description="Databases holding regulated and confidential records."),
    NetworkZone(id=SOC, name="Security Operations", kind=ZoneKind.MONITORING,
                description="Log collection and intrusion-detection sensors."),
    NetworkZone(id=GRID, name="Grid Operations (OT)", kind=ZoneKind.CRITICAL_INFRASTRUCTURE,
                description="Operational technology controlling power distribution."),
    NetworkZone(id=CLOUD, name="Hosted Cloud Services", kind=ZoneKind.CLOUD,
                description="Third-party hosted services reached over VPN."),
)


def link(id: str, a: str, b: str, kind: L, mbps: int, latency: float, *,
         encrypted: bool = False, permitted: bool = True, note: str = "") -> NetworkConnection:
    return NetworkConnection(
        id=id, source_id=a, target_id=b, link_type=kind, bandwidth_mbps=mbps, latency_ms=latency,
        encrypted=encrypted, traffic_permitted=permitted, description=note,
    )


TAP_NOTE = "Passive monitoring tap. Observes traffic but does not route it."

SAMPLE_CONNECTIONS = (
    # Perimeter
    link("link-edge-fw", "edge-rtr-01", "edge-fw-01", L.FIBER, 10_000, 0.5),
    link("link-fw-portal", "edge-fw-01", "web-portal-01", L.ETHERNET, 1_000, 0.4),
    link("link-fw-bankweb", "edge-fw-01", "bank-web-01", L.ETHERNET, 1_000, 0.4, encrypted=True),
    link("link-fw-core", "edge-fw-01", "core-rtr-01", L.FIBER, 10_000, 0.5),
    link("link-fw-backup", "edge-fw-01", "cloud-backup-01", L.VPN, 500, 18.0, encrypted=True),
    link("link-fw-mail", "edge-fw-01", "cloud-mail-01", L.VPN, 200, 22.0, encrypted=True),
    # Corporate LAN
    link("link-core-sw", "core-rtr-01", "core-sw-01", L.FIBER, 10_000, 0.3),
    link("link-sw-idp", "core-sw-01", "idp-01", L.ETHERNET, 1_000, 0.3),
    link("link-sw-govapp", "core-sw-01", "gov-app-01", L.ETHERNET, 1_000, 0.3),
    link("link-sw-govws", "core-sw-01", "gov-ws-01", L.ETHERNET, 1_000, 0.5),
    link("link-sw-univapp", "core-sw-01", "univ-app-01", L.ETHERNET, 1_000, 0.3),
    link("link-sw-univws", "core-sw-01", "univ-ws-01", L.ETHERNET, 1_000, 0.5),
    link("link-sw-bizapp", "core-sw-01", "biz-app-01", L.ETHERNET, 1_000, 0.3),
    link("link-sw-bizpos", "core-sw-01", "biz-pos-01", L.WIRELESS, 150, 4.0, encrypted=True),
    link("link-sw-bankcore", "core-sw-01", "bank-core-01", L.ETHERNET, 1_000, 0.3, encrypted=True),
    link("link-sw-bankws", "core-sw-01", "bank-ws-01", L.ETHERNET, 1_000, 0.5),
    # Clinical
    link("link-core-hospfw", "core-rtr-01", "hosp-fw-01", L.FIBER, 10_000, 0.6),
    link("link-hospfw-sw", "hosp-fw-01", "hosp-sw-01", L.ETHERNET, 1_000, 0.3),
    link("link-hospsw-ehr", "hosp-sw-01", "hosp-ehr-app-01", L.ETHERNET, 1_000, 0.3),
    link("link-hospsw-pacs", "hosp-sw-01", "hosp-pacs-01", L.ETHERNET, 1_000, 0.3),
    link("link-hospsw-infusion", "hosp-sw-01", "hosp-infusion-01", L.WIRELESS, 100, 5.0),
    link("link-hospsw-ws", "hosp-sw-01", "hosp-ws-01", L.ETHERNET, 1_000, 0.5),
    # Restricted data
    link("link-core-datafw", "core-rtr-01", "data-fw-01", L.FIBER, 10_000, 0.4),
    link("link-datafw-ehrdb", "data-fw-01", "hosp-ehr-db-01", L.ETHERNET, 10_000, 0.2, encrypted=True),
    link("link-datafw-ledger", "data-fw-01", "bank-ledger-db-01", L.ETHERNET, 10_000, 0.2, encrypted=True),
    link("link-datafw-govdb", "data-fw-01", "gov-db-01", L.ETHERNET, 1_000, 0.2),
    link("link-datafw-univdb", "data-fw-01", "univ-db-01", L.ETHERNET, 1_000, 0.2),
    # Security operations
    link("link-core-socsw", "core-rtr-01", "soc-sw-01", L.ETHERNET, 1_000, 0.4),
    link("link-socsw-siem", "soc-sw-01", "soc-siem-01", L.ETHERNET, 1_000, 0.2),
    link("link-socsw-ids1", "soc-sw-01", "soc-ids-01", L.ETHERNET, 1_000, 0.2),
    link("link-socsw-ids2", "soc-sw-01", "soc-ids-02", L.ETHERNET, 1_000, 0.2),
    link("link-ids1-tap", "soc-ids-01", "edge-fw-01", L.ETHERNET, 1_000, 0.2, permitted=False, note=TAP_NOTE),
    link("link-ids2-tap", "soc-ids-02", "grid-fw-01", L.ETHERNET, 1_000, 0.2, permitted=False, note=TAP_NOTE),
    # Grid OT
    link("link-core-gridfw", "core-rtr-01", "grid-fw-01", L.ETHERNET, 1_000, 1.2),
    link("link-gridfw-hmi", "grid-fw-01", "grid-hmi-01", L.ETHERNET, 100, 0.8),
    link("link-gridfw-plc1", "grid-fw-01", "grid-plc-01", L.ETHERNET, 100, 1.5),
    link("link-gridfw-plc2", "grid-fw-01", "grid-plc-02", L.ETHERNET, 100, 3.0, permitted=False,
         note="Administratively disabled pending controller replacement."),
)
