// TypeScript mirrors of the backend Pydantic models (backend/app/models).
// Keep these in sync by hand for now; a later phase could generate them
// from the FastAPI OpenAPI schema.

export type DeviceType =
  | "workstation"
  | "server"
  | "database"
  | "router"
  | "switch"
  | "firewall"
  | "iot_controller"
  | "cloud_gateway";

export type Criticality = "low" | "medium" | "high" | "critical";
export type LinkType = "ethernet" | "fiber" | "wireless" | "vpn";
export type Sector = "healthcare" | "finance" | "energy" | "government" | "business" | "cloud";
export type ServiceStatus = "operational" | "degraded" | "offline";
export type Difficulty = "training" | "standard" | "challenging";

export interface NetworkDevice {
  id: string;
  name: string;
  device_type: DeviceType;
  zone: string;
  criticality: Criticality;
  online: boolean;
  patch_age_days: number;
}

export interface NetworkConnection {
  id: string;
  source_id: string;
  target_id: string;
  link_type: LinkType;
  bandwidth_mbps: number;
  encrypted: boolean;
}

export interface NetworkSnapshot {
  devices: NetworkDevice[];
  connections: NetworkConnection[];
}

export interface CityService {
  id: string;
  name: string;
  sector: Sector;
  status: ServiceStatus;
  dependency_ids: string[];
}

export interface SimulationConfig {
  seed: number;
  city_name: string;
  difficulty: Difficulty;
  starting_budget: number;
  tick_minutes: number;
}

export interface SimulationSummary {
  config: SimulationConfig;
  tick: number;
  simulated_minutes: number;
  device_count: number;
  connection_count: number;
  services: CityService[];
}

export interface HealthResponse {
  status: string;
  version: string;
}

export interface ApiErrorDetail {
  location: (string | number)[];
  message: string;
  type: string;
}

export interface ApiErrorBody {
  error: {
    code: string;
    message: string;
    details: ApiErrorDetail[];
  };
}
