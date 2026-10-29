import type { ServiceOverview } from "../types/city";
import type { DeviceDetail, NetworkConnection, NetworkDevice, Topology, ValidationReport } from "../types/network";
import type { SimulationSummary } from "../types/simulation";

const base = {
  status: "online" as const,
  criticality: "medium" as const,
  configured_services: [],
  patch: { level: "current" as const, days_since_patch: 4 },
  vulnerabilities: [],
};

export const devices: NetworkDevice[] = [
  { ...base, id: "rtr-01", name: "Edge Router", zone_id: "dmz", device_type: "router", internet_edge: true, criticality: "critical" },
  {
    ...base, id: "web-01", name: "Public Portal", zone_id: "dmz", device_type: "application_server",
    application: "Portal", configured_services: [{ protocol: "https", port: 443 }],
  },
  { ...base, id: "sw-01", name: "Core Switch", zone_id: "lan", device_type: "switch", port_count: 48, status: "degraded" },
  {
    ...base, id: "db-01", name: "Records Database", zone_id: "data", device_type: "database_server",
    data_classification: "regulated", criticality: "critical",
    configured_services: [{ protocol: "sql", port: 5432 }],
    patch: { level: "behind", days_since_patch: 47 },
    vulnerabilities: [
      { id: "ccv-2026-0001", title: "Fictional weak config", severity: "high", affected_protocol: "sql", remediated: false },
      { id: "ccv-2026-0002", title: "Fictional old issue", severity: "low", affected_protocol: null, remediated: true },
    ],
  },
  { ...base, id: "ws-01", name: "Clerk PC", zone_id: "lan", device_type: "workstation", user_role: "Clerk", status: "offline" },
  { ...base, id: "ids-01", name: "IDS Sensor", zone_id: "lan", device_type: "security_sensor", monitored_zone_ids: ["dmz", "lan"] },
];

const link = (id: string, a: string, b: string, extra: Partial<NetworkConnection> = {}): NetworkConnection => ({
  id, source_id: a, target_id: b, link_type: "ethernet", bandwidth_mbps: 1000, latency_ms: 0.5,
  encrypted: false, traffic_permitted: true, description: "", ...extra,
});

export const topologyFixture: Topology = {
  zones: [
    { id: "dmz", name: "Public DMZ", kind: "public", description: "" },
    { id: "lan", name: "Internal LAN", kind: "internal", description: "" },
    { id: "data", name: "Data Zone", kind: "restricted", description: "" },
  ],
  devices,
  connections: [
    link("link-rtr-web", "rtr-01", "web-01"),
    link("link-rtr-sw", "rtr-01", "sw-01", { link_type: "fiber", bandwidth_mbps: 10000, encrypted: true }),
    link("link-sw-db", "sw-01", "db-01"),
    link("link-sw-ws", "sw-01", "ws-01"),
    link("link-sw-ids", "sw-01", "ids-01", { traffic_permitted: false, description: "Passive tap." }),
  ],
  segments: [["db-01", "rtr-01", "sw-01", "web-01"], ["ids-01"]],
  isolated_device_ids: ["ids-01"],
};

export const deviceDetailFixture: DeviceDetail = {
  device: devices[3]!,
  zone: topologyFixture.zones[2]!,
  links: [{ connection: topologyFixture.connections[2]!, neighbor_id: "sw-01" }],
  reachable_device_ids: ["rtr-01", "sw-01", "web-01"],
  isolated: false,
  dependent_service_ids: ["svc-portal"],
};

export const servicesFixture: ServiceOverview[] = [
  {
    service: {
      id: "svc-portal", name: "Citizen Portal", organization_id: "org-city", criticality: "high",
      entry_point_id: "web-01", description: "",
      dependencies: [{ device_id: "db-01", protocol: "sql", role: "records database", required: true, client_id: null }],
    },
    organization: { id: "org-city", name: "City Hall", sector: "government", description: "" },
    health: {
      service_id: "svc-portal", status: "down", entry_point_status: "online",
      summary: "Required records database ('db-01', sql) is unavailable.",
      dependencies: [{
        device_id: "db-01", client_id: "web-01", protocol: "sql", role: "records database", required: true,
        device_status: "online", ok: false, reason: "Not permitted: Denied by default: no rule matches dmz → data over sql.",
      }],
    },
  },
];

export const validationFixture: ValidationReport = {
  valid: true,
  error_count: 0,
  warning_count: 1,
  issues: [{ severity: "warning", code: "isolated_device", message: "'ids-01' is operational but cut off.", subject_ids: ["ids-01"] }],
};

export const summaryFixture: SimulationSummary = {
  config: { seed: 1337, city_name: "CyberCity", difficulty: "standard", starting_budget: 250000, tick_minutes: 15 },
  tick: 0,
  simulated_minutes: 0,
  zone_count: 3,
  device_count: devices.length,
  connection_count: 5,
  organization_count: 1,
  service_count: 1,
};
