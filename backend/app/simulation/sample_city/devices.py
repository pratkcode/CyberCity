"""Devices in the fictional sample city (36 devices across 7 zones).

Names, organizations and vulnerability IDs are invented. There are no IP
addresses or hostnames, because the simulator never resolves anything.
Patch ages are filled in at initialization from the simulation seed.
"""

from app.models import (
    ApplicationServerDevice as App,
    BankingSystemDevice as Bank,
    CloudServiceDevice as Cloud,
    ConfiguredService,
    Criticality as C,
    DatabaseServerDevice as Db,
    DataClassification as Data,
    FirewallDevice as Firewall,
    HospitalSystemDevice as Hospital,
    OperationalStatus,
    PatchLevel,
    PatchStatus,
    PowerControllerDevice as PowerController,
    Protocol as P,
    RouterDevice as Router,
    SecuritySensorDevice as Sensor,
    Severity,
    SwitchDevice as Switch,
    Vulnerability,
    WorkstationDevice as Workstation,
)

DEFAULT_PORTS: dict[P, int] = {
    P.HTTPS: 443, P.HTTP: 80, P.SSH: 22, P.RDP: 3389, P.SQL: 5432, P.LDAP: 389,
    P.SMTP: 587, P.SYSLOG: 514, P.DICOM: 104, P.MODBUS: 502, P.DNP3: 20000,
}


def offers(*protocols: P) -> tuple[ConfiguredService, ...]:
    return tuple(ConfiguredService(protocol=p, port=DEFAULT_PORTS[p]) for p in protocols)


def vuln(id: str, title: str, severity: Severity, protocol: P | None = None, remediated: bool = False) -> Vulnerability:
    return Vulnerability(id=id, title=title, severity=severity, affected_protocol=protocol, remediated=remediated)


UNSUPPORTED = PatchStatus(level=PatchLevel.UNSUPPORTED)

PUBLIC = "public-dmz"
CORP = "corp-internal"
CLINICAL = "clinical-net"
DATA = "restricted-data"
SOC = "security-ops"
GRID = "grid-ot"
CLOUD = "cloud-hosted"

SAMPLE_DEVICES = (
    # --- Public DMZ ---------------------------------------------------------
    Router(id="edge-rtr-01", name="City Internet Edge Router", zone_id=PUBLIC, criticality=C.CRITICAL,
           internet_edge=True, configured_services=offers(P.SSH)),
    Firewall(id="edge-fw-01", name="Perimeter Firewall", zone_id=PUBLIC, criticality=C.CRITICAL,
             protected_zone_ids=(PUBLIC, CORP), configured_services=offers(P.SSH)),
    App(id="web-portal-01", name="Citizen Services Portal", zone_id=PUBLIC, criticality=C.HIGH,
        application="Public permits web front end", configured_services=offers(P.HTTPS),
        vulnerabilities=(vuln("ccv-2026-0101", "Outdated web framework component", Severity.MEDIUM, P.HTTPS),)),
    Bank(id="bank-web-01", name="Harbor Trust Online Banking", zone_id=PUBLIC, criticality=C.CRITICAL,
         transaction_role="Customer web banking", configured_services=offers(P.HTTPS),
         vulnerabilities=(vuln("ccv-2026-0119", "Weak TLS cipher configuration", Severity.LOW, P.HTTPS, remediated=True),)),
    # --- Corporate & civic LAN ---------------------------------------------
    Router(id="core-rtr-01", name="Municipal Core Router", zone_id=CORP, criticality=C.CRITICAL,
           configured_services=offers(P.SSH)),
    Switch(id="core-sw-01", name="Core Distribution Switch", zone_id=CORP, criticality=C.HIGH, port_count=48),
    App(id="idp-01", name="Citywide Identity Directory", zone_id=CORP, criticality=C.CRITICAL,
        application="Identity and single sign-on", configured_services=offers(P.LDAP, P.HTTPS)),
    App(id="gov-app-01", name="Permits & Licensing App", zone_id=CORP, criticality=C.HIGH,
        application="Permit case management", configured_services=offers(P.HTTPS)),
    Workstation(id="gov-ws-01", name="City Hall Clerk Workstation", zone_id=CORP, criticality=C.LOW,
                user_role="Permits clerk", status=OperationalStatus.DEGRADED, configured_services=offers(P.RDP),
                vulnerabilities=(vuln("ccv-2026-0412", "Remote desktop without network-level auth", Severity.MEDIUM, P.RDP),)),
    App(id="univ-app-01", name="Northgate Student Portal", zone_id=CORP, criticality=C.MEDIUM,
        application="Course registration", configured_services=offers(P.HTTPS)),
    Workstation(id="univ-ws-01", name="Northgate Research Lab PC", zone_id=CORP, criticality=C.LOW,
                user_role="Graduate researcher", status=OperationalStatus.OFFLINE, configured_services=offers(P.SSH)),
    App(id="biz-app-01", name="Market Street Inventory Server", zone_id=CORP, criticality=C.MEDIUM,
        application="Shared retail inventory", configured_services=offers(P.HTTPS)),
    Workstation(id="biz-pos-01", name="Market Street POS Terminal", zone_id=CORP, criticality=C.MEDIUM,
                user_role="Retail cashier"),
    Bank(id="bank-core-01", name="Harbor Trust Core Banking", zone_id=CORP, criticality=C.CRITICAL,
         transaction_role="Account and payment processing", configured_services=offers(P.HTTPS)),
    Workstation(id="bank-ws-01", name="Harbor Trust Teller Station", zone_id=CORP, criticality=C.MEDIUM,
                user_role="Bank teller"),
    # --- Clinical network ---------------------------------------------------
    Firewall(id="hosp-fw-01", name="St. Aurelia Clinical Firewall", zone_id=CLINICAL, criticality=C.HIGH,
             protected_zone_ids=(CLINICAL,), configured_services=offers(P.SSH)),
    Switch(id="hosp-sw-01", name="Clinical Floor Switch", zone_id=CLINICAL, criticality=C.MEDIUM),
    Hospital(id="hosp-ehr-app-01", name="EHR Application Server", zone_id=CLINICAL, criticality=C.CRITICAL,
             clinical_function="Electronic health records", configured_services=offers(P.HTTPS)),
    Hospital(id="hosp-pacs-01", name="Radiology PACS", zone_id=CLINICAL, criticality=C.HIGH,
             clinical_function="Medical imaging archive", configured_services=offers(P.DICOM, P.HTTPS)),
    Hospital(id="hosp-infusion-01", name="Infusion Pump Gateway", zone_id=CLINICAL, criticality=C.CRITICAL,
             clinical_function="Infusion pump management", life_safety=True, patch=UNSUPPORTED,
             configured_services=offers(P.HTTPS),
             vulnerabilities=(vuln("ccv-2026-0214", "Default maintenance credentials", Severity.HIGH, P.HTTPS),)),
    Workstation(id="hosp-ws-01", name="Ward 3 Nurse Station", zone_id=CLINICAL, criticality=C.MEDIUM,
                user_role="Nurse"),
    # --- Restricted data zone -----------------------------------------------
    Firewall(id="data-fw-01", name="Data Zone Firewall", zone_id=DATA, criticality=C.CRITICAL,
             protected_zone_ids=(DATA,), configured_services=offers(P.SSH)),
    Db(id="hosp-ehr-db-01", name="Patient Records Database", zone_id=DATA, criticality=C.CRITICAL,
       data_classification=Data.REGULATED, configured_services=offers(P.SQL)),
    Db(id="bank-ledger-db-01", name="Harbor Trust Ledger Database", zone_id=DATA, criticality=C.CRITICAL,
       data_classification=Data.REGULATED, configured_services=offers(P.SQL)),
    Db(id="gov-db-01", name="Municipal Records Database", zone_id=DATA, criticality=C.HIGH,
       data_classification=Data.CONFIDENTIAL, configured_services=offers(P.SQL)),
    Db(id="univ-db-01", name="Student Records Database", zone_id=DATA, criticality=C.HIGH,
       data_classification=Data.CONFIDENTIAL, configured_services=offers(P.SQL)),
    # --- Security operations ------------------------------------------------
    Switch(id="soc-sw-01", name="SOC Switch", zone_id=SOC, criticality=C.MEDIUM, port_count=16),
    App(id="soc-siem-01", name="SOC Log Analytics Server", zone_id=SOC, criticality=C.HIGH,
        application="Log collection and search", configured_services=offers(P.SYSLOG, P.HTTPS)),
    Sensor(id="soc-ids-01", name="Perimeter IDS Sensor", zone_id=SOC, criticality=C.HIGH,
           monitored_zone_ids=(PUBLIC, CORP)),
    Sensor(id="soc-ids-02", name="Clinical & OT IDS Sensor", zone_id=SOC, criticality=C.HIGH,
           monitored_zone_ids=(CLINICAL, GRID)),
    # --- Grid operations (OT) -----------------------------------------------
    Firewall(id="grid-fw-01", name="Grid OT Firewall", zone_id=GRID, criticality=C.CRITICAL,
             protected_zone_ids=(GRID,), configured_services=offers(P.SSH)),
    Workstation(id="grid-hmi-01", name="Grid Operator Console", zone_id=GRID, criticality=C.HIGH,
                user_role="Grid operator"),
    PowerController(id="grid-plc-01", name="Substation 4 Feeder Controller", zone_id=GRID, criticality=C.CRITICAL,
                    substation="Substation 4", control_protocol=P.MODBUS, configured_services=offers(P.MODBUS)),
    PowerController(id="grid-plc-02", name="Substation 7 Feeder Controller", zone_id=GRID, criticality=C.HIGH,
                    substation="Substation 7", control_protocol=P.DNP3, configured_services=offers(P.DNP3),
                    patch=UNSUPPORTED,
                    vulnerabilities=(vuln("ccv-2026-0307", "Control commands accepted without authentication", Severity.CRITICAL, P.DNP3),)),
    # --- Hosted cloud services ----------------------------------------------
    Cloud(id="cloud-backup-01", name="Offsite Backup Vault", zone_id=CLOUD, criticality=C.HIGH,
          provider="Nimbus Metro Cloud", configured_services=offers(P.HTTPS)),
    Cloud(id="cloud-mail-01", name="City Email Service", zone_id=CLOUD, criticality=C.MEDIUM,
          provider="Nimbus Metro Cloud", configured_services=offers(P.SMTP, P.HTTPS)),
)
