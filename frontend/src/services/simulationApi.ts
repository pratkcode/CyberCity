import type { Organization, ServiceOverview } from "../types/city";
import type {
  ConnectionCheck,
  DeviceDetail,
  PathMetric,
  PathResult,
  PolicyRule,
  Protocol,
  Topology,
  ValidationReport,
  ZoneSummary,
} from "../types/network";
import type { HealthResponse, SimulationConfig, SimulationSummary } from "../types/simulation";
import { requestJson } from "./apiClient";

const query = (params: Record<string, string>) => new URLSearchParams(params).toString();

export const simulationApi = {
  getHealth: () => requestJson<HealthResponse>("/health"),

  getSimulation: () => requestJson<SimulationSummary>("/simulation"),

  createSimulation: (config: Partial<SimulationConfig>) =>
    requestJson<SimulationSummary>("/simulation", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  // Network
  getTopology: () => requestJson<Topology>("/network"),

  getZones: () => requestJson<ZoneSummary[]>("/network/zones"),

  getDeviceDetail: (deviceId: string) =>
    requestJson<DeviceDetail>(`/network/devices/${encodeURIComponent(deviceId)}`),

  findPath: (source: string, target: string, metric: PathMetric = "hops") =>
    requestJson<PathResult>(`/network/path?${query({ source, target, metric })}`),

  getValidation: () => requestJson<ValidationReport>("/network/validation"),

  // Policy
  getPolicyRules: () => requestJson<{ rules: PolicyRule[] }>("/policy/rules"),

  checkAccess: (source: string, target: string, protocol: Protocol) =>
    requestJson<ConnectionCheck>(`/policy/check?${query({ source, target, protocol })}`),

  // City
  getOrganizations: () => requestJson<Organization[]>("/city/organizations"),

  getServices: () => requestJson<ServiceOverview[]>("/city/services"),
};
