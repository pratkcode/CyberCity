import type { StylesheetJson } from "cytoscape";

import type { DeviceType } from "../../types/simulation";

// Cytoscape draws on a canvas and cannot read CSS variables, so the map
// palette lives here. Values match the tokens in styles/theme.css.
const COLORS = {
  text: "#c9d4e5",
  edge: "#34445e",
  edgeEncrypted: "#2f9e8f",
  accent: "#38d9c0",
  offline: "#5c6779",
};

export const DEVICE_STYLES: Record<DeviceType, { color: string; shape: string }> = {
  router: { color: "#5b8cff", shape: "diamond" },
  switch: { color: "#7a8bb8", shape: "round-rectangle" },
  firewall: { color: "#ff8a4c", shape: "hexagon" },
  server: { color: "#4cc3ff", shape: "round-rectangle" },
  database: { color: "#b98cff", shape: "barrel" },
  workstation: { color: "#9fb3c8", shape: "ellipse" },
  iot_controller: { color: "#f2c94c", shape: "octagon" },
  cloud_gateway: { color: "#38d9c0", shape: "round-tag" },
};

export const networkStylesheet: StylesheetJson = [
  {
    selector: "node",
    style: {
      label: "data(label)",
      color: COLORS.text,
      "font-size": 10,
      "font-family": "Inter, system-ui, sans-serif",
      "text-valign": "bottom",
      "text-margin-y": 6,
      "text-wrap": "wrap",
      "text-max-width": "84px",
      width: 30,
      height: 30,
      "border-width": 2,
      "border-color": "#0b1220",
      "background-color": "#7a8bb8",
    },
  },
  ...Object.entries(DEVICE_STYLES).map(([type, { color, shape }]) => ({
    selector: `node[deviceType = "${type}"]`,
    style: { "background-color": color, shape: shape as never },
  })),
  {
    selector: 'node[criticality = "critical"]',
    style: { width: 38, height: 38 },
  },
  {
    selector: "node.offline",
    style: { "background-color": COLORS.offline, opacity: 0.6 },
  },
  {
    selector: "node:selected",
    style: {
      "border-color": COLORS.accent,
      "border-width": 4,
      "overlay-color": COLORS.accent,
      "overlay-opacity": 0.12,
      "overlay-padding": 8,
    },
  },
  {
    selector: "edge",
    style: {
      width: 2,
      "line-color": COLORS.edge,
      "curve-style": "bezier",
    },
  },
  {
    selector: "edge.encrypted",
    style: { "line-color": COLORS.edgeEncrypted },
  },
  {
    selector: 'edge[linkType = "vpn"], edge[linkType = "wireless"]',
    style: { "line-style": "dashed" },
  },
];
