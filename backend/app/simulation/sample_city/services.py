"""Organizations and critical services in the sample city."""

from app.models import (
    CityService,
    Criticality as C,
    Organization,
    Protocol as P,
    Sector,
    ServiceDependency as Dep,
)

SAMPLE_ORGANIZATIONS = (
    Organization(id="org-st-aurelia", name="St. Aurelia General Hospital", sector=Sector.HEALTHCARE),
    Organization(id="org-harbor-trust", name="Harbor Trust Bank", sector=Sector.FINANCE),
    Organization(id="org-eastside-power", name="Eastside Power Cooperative", sector=Sector.ENERGY),
    Organization(id="org-city-hall", name="City of CyberCity", sector=Sector.GOVERNMENT),
    Organization(id="org-northgate", name="Northgate University", sector=Sector.EDUCATION),
    Organization(id="org-market-street", name="Market Street Merchants", sector=Sector.BUSINESS),
)

SAMPLE_SERVICES = (
    CityService(
        id="svc-ehr", name="Electronic Health Records", organization_id="org-st-aurelia",
        criticality=C.CRITICAL, entry_point_id="hosp-ehr-app-01",
        description="Clinicians view and update patient charts.",
        dependencies=(
            Dep(device_id="hosp-ehr-db-01", protocol=P.SQL, role="patient database"),
            Dep(device_id="idp-01", protocol=P.LDAP, role="identity service"),
            Dep(device_id="soc-siem-01", protocol=P.SYSLOG, role="audit logging", required=False),
        ),
    ),
    CityService(
        id="svc-imaging", name="Radiology Imaging", organization_id="org-st-aurelia",
        criticality=C.HIGH, entry_point_id="hosp-pacs-01",
        dependencies=(
            Dep(device_id="hosp-ehr-db-01", protocol=P.SQL, role="patient lookup"),
            Dep(device_id="idp-01", protocol=P.LDAP, role="identity service"),
            Dep(device_id="cloud-backup-01", protocol=P.HTTPS, role="offsite image backup", required=False),
        ),
    ),
    CityService(
        id="svc-online-banking", name="Online Banking", organization_id="org-harbor-trust",
        criticality=C.CRITICAL, entry_point_id="bank-web-01",
        dependencies=(
            Dep(device_id="bank-core-01", protocol=P.HTTPS, role="core banking API"),
            Dep(device_id="bank-ledger-db-01", protocol=P.SQL, role="ledger database", client_id="bank-core-01"),
            Dep(device_id="idp-01", protocol=P.LDAP, role="staff identity", client_id="bank-core-01"),
        ),
    ),
    CityService(
        id="svc-grid-control", name="Feeder Control", organization_id="org-eastside-power",
        criticality=C.CRITICAL, entry_point_id="grid-hmi-01",
        description="Operators supervise distribution feeders.",
        dependencies=(
            Dep(device_id="grid-plc-01", protocol=P.MODBUS, role="Substation 4 feeder"),
            Dep(device_id="grid-plc-02", protocol=P.DNP3, role="Substation 7 feeder (redundant)", required=False),
            Dep(device_id="soc-siem-01", protocol=P.SYSLOG, role="OT event logging", required=False),
        ),
    ),
    CityService(
        id="svc-permits", name="Online Permits & Licensing", organization_id="org-city-hall",
        criticality=C.HIGH, entry_point_id="web-portal-01",
        dependencies=(
            Dep(device_id="gov-app-01", protocol=P.HTTPS, role="permits application"),
            Dep(device_id="gov-db-01", protocol=P.SQL, role="records database", client_id="gov-app-01"),
            Dep(device_id="idp-01", protocol=P.LDAP, role="staff identity", client_id="gov-app-01"),
        ),
    ),
    CityService(
        id="svc-student-portal", name="Student Portal", organization_id="org-northgate",
        criticality=C.MEDIUM, entry_point_id="univ-app-01",
        dependencies=(
            Dep(device_id="univ-db-01", protocol=P.SQL, role="student records"),
            Dep(device_id="idp-01", protocol=P.LDAP, role="identity service"),
            Dep(device_id="cloud-mail-01", protocol=P.SMTP, role="notification email", required=False),
        ),
    ),
    CityService(
        id="svc-retail-payments", name="Retail Card Payments", organization_id="org-market-street",
        criticality=C.MEDIUM, entry_point_id="biz-pos-01",
        dependencies=(
            Dep(device_id="biz-app-01", protocol=P.HTTPS, role="inventory service"),
            Dep(device_id="bank-web-01", protocol=P.HTTPS, role="card payment gateway"),
        ),
    ),
)
