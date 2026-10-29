import type { StylesheetJson } from "cytoscape";

import { DEVICE_STYLES, MAP_COLORS as C, ZONE_COLORS } from "./palette";

export const networkStylesheet: StylesheetJson = [
  // ---- Zones (compound parents) ------------------------------------------
  {
    selector: "node.zone",
    style: {
      label: "data(label)",
      "text-valign": "top",
      "text-halign": "center",
      "text-margin-y": -6,
      color: C.zoneText,
      "font-size": 13,
      "font-weight": 600,
      "font-family": "Inter, system-ui, sans-serif",
      "text-transform": "uppercase",
      shape: "round-rectangle",
      "background-opacity": 0.05,
      "border-width": 1.5,
      "border-style": "dashed",
      "border-opacity": 0.7,
      padding: "14px",
    },
  },
  ...Object.entries(ZONE_COLORS).map(([kind, color]) => ({
    selector: `node.zone[kind = "${kind}"]`,
    style: { "border-color": color, "background-color": color },
  })),

  // ---- Devices -------------------------------------------------------------
  {
    selector: "node.device",
    style: {
      label: "data(label)",
      color: C.text,
      "font-size": 11.5,
      "font-family": "Inter, system-ui, sans-serif",
      "text-valign": "bottom",
      "text-margin-y": 4,
      "text-wrap": "wrap",
      "text-max-width": "112px",
      width: 26,
      height: 26,
      "border-width": 2,
      "border-color": C.border,
    },
  },
  ...Object.entries(DEVICE_STYLES).map(([type, { color, shape }]) => ({
    selector: `node.device[deviceType = "${type}"]`,
    style: { "background-color": color, shape: shape as never },
  })),
  { selector: 'node.device[criticality = "critical"]', style: { width: 31, height: 31 } },

  // Visual states: operational (default), degraded, isolated, unavailable.
  { selector: "node.state-degraded", style: { "border-color": C.degraded, "border-width": 3 } },
  {
    selector: "node.state-isolated",
    style: { "border-color": C.isolated, "border-width": 3, "border-style": "dashed" },
  },
  {
    selector: "node.state-unavailable",
    style: {
      "background-color": C.offline,
      "border-style": "dotted",
      "border-color": "#7d889b",
      opacity: 0.55,
      color: "#6b778c",
    },
  },

  // ---- Links ---------------------------------------------------------------
  {
    selector: "edge",
    style: {
      width: "mapData(capacity, 2, 4, 1.5, 4)",
      "line-color": C.edge,
      "curve-style": "straight",
      "font-size": 9,
      color: C.text,
      "text-background-color": "#0d1424",
      "text-background-opacity": 0.85,
      "text-background-padding": "2px",
    },
  },
  {
    selector: "edge.arced",
    style: {
      "curve-style": "unbundled-bezier",
      "control-point-distances": "data(bend)",
      "control-point-weights": 0.5,
    },
  },
  { selector: "edge.encrypted", style: { "line-color": C.encrypted } },
  {
    selector: 'edge[linkType = "vpn"], edge[linkType = "wireless"]',
    style: { "line-style": "dashed" },
  },
  {
    selector: "edge.blocked",
    style: { "line-color": C.blocked, "line-style": "dotted", opacity: 0.7 },
  },

  // ---- Selection and highlighting ------------------------------------------
  {
    selector: "node.device:selected",
    style: {
      "border-color": C.highlight,
      "border-width": 4,
      "overlay-color": C.highlight,
      "overlay-opacity": 0.14,
      "overlay-padding": 7,
    },
  },
  {
    selector: "edge:selected",
    style: { "line-color": C.highlight, width: 4, label: "data(label)" },
  },
  { selector: ".dimmed", style: { opacity: 0.18 } },
  { selector: "node.zone.dimmed", style: { opacity: 0.5 } },
  {
    selector: "node.device.highlighted",
    style: { "border-color": C.highlight, "border-width": 4, opacity: 1 },
  },
  {
    selector: "edge.highlighted",
    style: {
      "line-color": C.highlight,
      width: 4.5,
      opacity: 1,
      label: "data(label)",
      "z-index": 10,
    },
  },
];
