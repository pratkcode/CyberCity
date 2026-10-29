// Mirrors backend/app/models/city.py.
import type { Criticality, OperationalStatus, Protocol } from "./network";

export type Sector = "healthcare" | "finance" | "energy" | "government" | "education" | "business";
export type ServiceHealthStatus = "operational" | "degraded" | "down";

export interface Organization {
  id: string;
  name: string;
  sector: Sector;
  description: string;
}

export interface ServiceDependency {
  device_id: string;
  protocol: Protocol;
  role: string;
  required: boolean;
  client_id: string | null;
}

export interface CityService {
  id: string;
  name: string;
  organization_id: string;
  criticality: Criticality;
  entry_point_id: string;
  dependencies: ServiceDependency[];
  description: string;
}

export interface DependencyHealth {
  device_id: string;
  client_id: string;
  protocol: Protocol;
  role: string;
  required: boolean;
  device_status: OperationalStatus;
  ok: boolean;
  reason: string;
}

export interface ServiceHealth {
  service_id: string;
  status: ServiceHealthStatus;
  entry_point_status: OperationalStatus;
  dependencies: DependencyHealth[];
  summary: string;
}

export interface ServiceOverview {
  service: CityService;
  organization: Organization;
  health: ServiceHealth;
}

/** Every device a service touches: entry point, dependencies, and their clients. */
export function serviceDeviceIds(service: CityService): string[] {
  const ids = new Set([service.entry_point_id]);
  for (const dep of service.dependencies) {
    ids.add(dep.device_id);
    ids.add(dep.client_id ?? service.entry_point_id);
  }
  return [...ids].sort();
}
