import type { ServiceOverview } from "../../types/city";
import type { Topology } from "../../types/network";

/** Resolve ids to display names, falling back to the id itself. */
export interface NameLookup {
  device: (id: string) => string;
  zone: (id: string) => string;
  service: (id: string) => string;
}

export function buildNameLookup(topology: Topology, services: ServiceOverview[]): NameLookup {
  const devices = new Map(topology.devices.map((d) => [d.id, d.name]));
  const zones = new Map(topology.zones.map((z) => [z.id, z.name]));
  const serviceNames = new Map(services.map((s) => [s.service.id, s.service.name]));
  return {
    device: (id) => devices.get(id) ?? id,
    zone: (id) => zones.get(id) ?? id,
    service: (id) => serviceNames.get(id) ?? id,
  };
}
