// TypeScript mirrors of backend/app/models/{network,devices,policy,analysis}.py.
// Kept in sync by hand. The backend API tests parse every response with the
// Pydantic models, so schema drift on that side is caught there.

export type Protocol =
  | "http" | "https" | "ssh" | "rdp" | "sql" | "ldap" | "dns" | "smtp"
  | "smb" | "syslog" | "dicom" | "modbus" | "dnp3";

export const PROTOCOLS: Protocol[] = [
  "http", "https", "ssh", "rdp", "sql", "ldap", "dns", "smtp", "smb", "syslog", "dicom", "modbus", "dnp3",
];

export type ZoneKind =
  | "public" | "internal" | "restricted" | "monitoring" | "critical_infrastructure" | "cloud";

export interface NetworkZone {
  id: string;
  name: string;
  kind: ZoneKind;
  description: string;
}

export type LinkType = "ethernet" | "fiber" | "wireless" | "vpn";

export interface NetworkConnection {
  id: string;
  source_id: string;
  target_id: string;
  link_type: LinkType;
  bandwidth_mbps: number;
  latency_ms: number;
  encrypted: boolean;
  traffic_permitted: boolean;
  description: string;
}

export type DeviceType =
  | "router" | "firewall" | "switch" | "workstation" | "application_server" | "database_server"
  | "cloud_service" | "security_sensor" | "hospital_system" | "power_controller" | "banking_system";

export type OperationalStatus = "online" | "degraded" | "offline";
export type Criticality = "low" | "medium" | "high" | "critical";
export type PatchLevel = "current" | "behind" | "unsupported";
export type Severity = "info" | "low" | "medium" | "high" | "critical";
export type DataClassification = "public" | "internal" | "confidential" | "regulated";

export interface ConfiguredService {
  protocol: Protocol;
  port: number;
}

export interface Vulnerability {
  id: string;
  title: string;
  severity: Severity;
  affected_protocol: Protocol | null;
  remediated: boolean;
}

interface DeviceBase {
  id: string;
  name: string;
  zone_id: string;
  status: OperationalStatus;
  criticality: Criticality;
  configured_services: ConfiguredService[];
  patch: { level: PatchLevel; days_since_patch: number };
  vulnerabilities: Vulnerability[];
}

/** Discriminated union on device_type, mirroring the backend's per-category models. */
export type NetworkDevice = DeviceBase &
  (
    | { device_type: "router"; internet_edge: boolean }
    | { device_type: "firewall"; protected_zone_ids: string[] }
    | { device_type: "switch"; port_count: number }
    | { device_type: "workstation"; user_role: string }
    | { device_type: "application_server"; application: string }
    | { device_type: "database_server"; data_classification: DataClassification }
    | { device_type: "cloud_service"; provider: string }
    | { device_type: "security_sensor"; monitored_zone_ids: string[] }
    | { device_type: "hospital_system"; clinical_function: string; life_safety: boolean }
    | { device_type: "power_controller"; substation: string; control_protocol: "modbus" | "dnp3" }
    | { device_type: "banking_system"; transaction_role: string; data_classification: DataClassification }
  );

export interface Topology {
  zones: NetworkZone[];
  devices: NetworkDevice[];
  connections: NetworkConnection[];
  segments: string[][];
  isolated_device_ids: string[];
}

export interface ZoneSummary {
  zone: NetworkZone;
  device_ids: string[];
  operational_device_count: number;
}

export interface DeviceDetail {
  device: NetworkDevice;
  zone: NetworkZone;
  links: { connection: NetworkConnection; neighbor_id: string }[];
  reachable_device_ids: string[];
  isolated: boolean;
  dependent_service_ids: string[];
}

export type PathMetric = "hops" | "latency";

export interface NetworkPath {
  device_ids: string[];
  connection_ids: string[];
  hop_count: number;
  total_latency_ms: number;
  bottleneck_bandwidth_mbps: number | null;
}

export interface PathResult {
  source_id: string;
  target_id: string;
  metric: PathMetric;
  found: boolean;
  path: NetworkPath | null;
  reason: string;
}

export interface PolicyRule {
  id: string;
  priority: number;
  action: "allow" | "deny";
  source_zone_id: string | null;
  destination_zone_id: string | null;
  protocols: Protocol[];
  description: string;
}

export interface PolicyDecision {
  allowed: boolean;
  source_zone_id: string;
  destination_zone_id: string;
  protocol: Protocol;
  matched_rule_id: string | null;
  default_applied: boolean;
  reason: string;
}

export type CheckName =
  | "source_operational" | "destination_operational" | "destination_service" | "policy" | "network_path";

export interface ConnectionCheck {
  source_id: string;
  destination_id: string;
  protocol: Protocol;
  permitted: boolean;
  steps: { check: CheckName; passed: boolean; detail: string }[];
  policy: PolicyDecision;
  path: NetworkPath | null;
  summary: string;
}

export interface ValidationIssue {
  severity: "error" | "warning" | "info";
  code: string;
  message: string;
  subject_ids: string[];
}

export interface ValidationReport {
  valid: boolean;
  error_count: number;
  warning_count: number;
  issues: ValidationIssue[];
}
