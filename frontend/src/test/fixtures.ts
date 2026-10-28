import type { NetworkSnapshot, SimulationSummary } from "../types/simulation";

export const networkFixture: NetworkSnapshot = {
  devices: [
    {
      id: "edge-router-01",
      name: "City Edge Router",
      device_type: "router",
      zone: "internet-edge",
      criticality: "critical",
      online: true,
      patch_age_days: 12,
    },
    {
      id: "hosp-ehr-db-01",
      name: "St. Aurelia Patient Records DB",
      device_type: "database",
      zone: "hospital-lan",
      criticality: "critical",
      online: true,
      patch_age_days: 47,
    },
    {
      id: "biz-pos-01",
      name: "Market Street Retail Terminal",
      device_type: "workstation",
      zone: "business-lan",
      criticality: "low",
      online: false,
      patch_age_days: 3,
    },
  ],
  connections: [
    {
      id: "link-edge-hosp",
      source_id: "edge-router-01",
      target_id: "hosp-ehr-db-01",
      link_type: "fiber",
      bandwidth_mbps: 10000,
      encrypted: true,
    },
    {
      id: "link-edge-biz",
      source_id: "biz-pos-01",
      target_id: "edge-router-01",
      link_type: "wireless",
      bandwidth_mbps: 300,
      encrypted: false,
    },
  ],
};

export const summaryFixture: SimulationSummary = {
  config: {
    seed: 1337,
    city_name: "CyberCity",
    difficulty: "standard",
    starting_budget: 250000,
    tick_minutes: 15,
  },
  tick: 0,
  simulated_minutes: 0,
  device_count: 3,
  connection_count: 2,
  services: [
    {
      id: "svc-hospital-records",
      name: "Hospital Patient Records",
      sector: "healthcare",
      status: "operational",
      dependency_ids: ["hosp-ehr-db-01"],
    },
  ],
};
