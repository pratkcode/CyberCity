import type { DeviceType, ZoneKind } from "../../types/network";

// Cytoscape draws on a canvas and cannot read CSS variables, so the map
// palette lives here. The legend reads the same values.

export type ShapeName =
  | "diamond" | "hexagon" | "rhomboid" | "ellipse" | "round-rectangle" | "barrel"
  | "round-tag" | "triangle" | "pentagon" | "octagon" | "concave-hexagon";

export const DEVICE_STYLES: Record<DeviceType, { color: string; shape: ShapeName; label: string }> = {
  router: { color: "#5b8cff", shape: "diamond", label: "Router" },
  firewall: { color: "#ff8a4c", shape: "hexagon", label: "Firewall" },
  switch: { color: "#8494c0", shape: "rhomboid", label: "Switch" },
  workstation: { color: "#a9bbcf", shape: "ellipse", label: "Workstation" },
  application_server: { color: "#4cc3ff", shape: "round-rectangle", label: "Application server" },
  database_server: { color: "#b98cff", shape: "barrel", label: "Database server" },
  cloud_service: { color: "#38d9c0", shape: "round-tag", label: "Cloud service" },
  security_sensor: { color: "#3ccf7e", shape: "triangle", label: "Security sensor" },
  hospital_system: { color: "#ff6fa0", shape: "pentagon", label: "Hospital system" },
  power_controller: { color: "#f2c94c", shape: "octagon", label: "Power controller" },
  banking_system: { color: "#d9b27c", shape: "concave-hexagon", label: "Banking system" },
};

export const ZONE_COLORS: Record<ZoneKind, string> = {
  public: "#5b8cff",
  cloud: "#38d9c0",
  internal: "#8494c0",
  restricted: "#b98cff",
  monitoring: "#3ccf7e",
  critical_infrastructure: "#f2c94c",
};

export const MAP_COLORS = {
  text: "#c9d4e5",
  zoneText: "#8fa0bb",
  edge: "#3a4a66",
  encrypted: "#2f9e8f",
  blocked: "#ff6b6b",
  degraded: "#f2a03c",
  isolated: "#ff6b6b",
  offline: "#4b5566",
  highlight: "#38d9c0",
  border: "#0b1220",
};
