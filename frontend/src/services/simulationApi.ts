import type {
  CityService,
  HealthResponse,
  NetworkDevice,
  NetworkSnapshot,
  SimulationConfig,
  SimulationSummary,
} from "../types/simulation";
import { requestJson } from "./apiClient";

export const simulationApi = {
  getHealth: () => requestJson<HealthResponse>("/health"),

  getSimulation: () => requestJson<SimulationSummary>("/simulation"),

  createSimulation: (config: Partial<SimulationConfig>) =>
    requestJson<SimulationSummary>("/simulation", {
      method: "POST",
      body: JSON.stringify(config),
    }),

  getNetwork: () => requestJson<NetworkSnapshot>("/network"),

  getDevice: (deviceId: string) =>
    requestJson<NetworkDevice>(`/network/devices/${encodeURIComponent(deviceId)}`),

  getServices: () => requestJson<CityService[]>("/services"),
};
